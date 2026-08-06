<script lang="ts">
  import { PanZoomState } from "$lib/pan.svelte";
  import { DisposeBag } from "$lib/utils";
  import GPUCanvas, { type SetupFn } from "$lib/webgpu/GPUCanvas.svelte";
  import { ImageCache } from "$lib/webgpu/image-loading";
  import colorCode from "$lib/webgpu/color.wgsl?raw";
  import shaderCode from "./01.wgsl?raw";

  const disposeBag = new DisposeBag();
  const panZoomState = new PanZoomState({ maxScale: 1000, minScale: 0.01 });
  panZoomState.set({ x: 100, y: 100, scale: 2 });

  type Sampling = keyof typeof samplings;
  const samplings = {
    nearest: 0,
    bilinear: 1,
    bicubic: 2,
    lanczos4: 3,
    lanczos6: 4,
  } as const;
  
  const settings = $state({
    sampling: "bilinear" as Sampling,
    image: "miku" as keyof typeof imageUrls,
  });

  const origin = new URL(window.location.href).origin;
  const imageUrls = {
    miku: new URL("/miku.png", origin),
    mikuSmall: new URL("/miku_small.png", origin),
  };

  const setup: SetupFn = async ({ device, context, presentationFormat }) => {
    const imageCache = new ImageCache(device);
    for (const url of Object.values(imageUrls)) {
      imageCache.preload(url);
    }

    const bindGroupLayout = device.createBindGroupLayout({
      entries: [
        {
          binding: 0,
          visibility: GPUShaderStage.FRAGMENT,
          storageTexture: {
            format: "rgba8unorm",
            access: "read-only",
          },
        },
      ],
    });

    const IMMEDIATE_SIZE = 32; // padded
    const immediateBuffer = new ArrayBuffer(IMMEDIATE_SIZE);
    const immediateBufferf32 = new Float32Array(immediateBuffer); // is a view
    const immediateBufferu32 = new Uint32Array(immediateBuffer);

    const pipelineLayout = device.createPipelineLayout({
      bindGroupLayouts: [bindGroupLayout],
      immediateSize: 32,
    });

    const module = device.createShaderModule({ code: colorCode + shaderCode });

    const srgbFormat = `${presentationFormat}-srgb` as any
    const pipeline = await device.createRenderPipelineAsync({
      layout: pipelineLayout,
      vertex: { module },
      fragment: { module, targets: [{ format: srgbFormat }] },
      primitive: { topology: "triangle-list" },
    });

    await imageCache.waitAll();

    async function render() {
      const currentTexture = context.getCurrentTexture();
      const view = currentTexture.createView({
         format: srgbFormat,
      });
      const encoder = device.createCommandEncoder();

      const image = await imageCache.getAsync(imageUrls[settings.image])!;
      const bindGroup = device.createBindGroup({
        layout: bindGroupLayout,
        entries: [
          {
            resource: image,
            binding: 0,
          },
        ],
      });

      {
        const pass = encoder.beginRenderPass({
          colorAttachments: [
            {
              loadOp: "clear",
              storeOp: "store",
              view,
            },
          ],
        });

        pass.setPipeline(pipeline);
        pass.setBindGroup(0, bindGroup);

        immediateBufferu32[0] = samplings[settings.sampling]
        immediateBufferf32.set(
          [
            // sourceSize
            image.width,
            image.height,
            // scale
            1 / panZoomState.scale,
            1 / panZoomState.scale,
            // offset
            panZoomState.x,
            panZoomState.y,
          ],
          2,
        );

        pass.setImmediates(0, immediateBuffer);
        pass.draw(6);
        pass.end();
      }

      device.queue.submit([encoder.finish()]);
    }

    let id: number = 0;
    const stop = $effect.root(() => {
      $effect(() => {
        settings.sampling;
        settings.image;
        panZoomState.x;
        panZoomState.y;
        panZoomState.scale;
        cancelAnimationFrame(id);
        id = requestAnimationFrame(() => render());
      });
    });

    disposeBag.add(stop);
    disposeBag.add(() => cancelAnimationFrame(id));

    return render;
  };
</script>

<GPUCanvas {setup} attach={panZoomState.attach} />
<div class="control">
  <div>
    <label>
      Sampling
      <select bind:value={settings.sampling}>
        <option value="nearest">nearest</option>
        <option value="bilinear">bilinear</option>
        <option value="bicubic">bicubic</option>
        <option value="lanczos4">lanczos4</option>
        <option value="lanczos6">lanczos6</option>
      </select>
    </label>
    <label>
      Image
      <select bind:value={settings.image}>
        <option value="miku">miku</option>
        <option value="mikuSmall">miku (small)</option>
      </select>
    </label>
  </div>

  <div>
    <label>
      Scale
      <input
        type="range"
        min="0.01"
        max="10"
        step="0.001"
        bind:value={panZoomState.scale}
      />
      <input type="number" bind:value={panZoomState.scale} />
    </label>
  </div>

  Mouse: drag to pan. ctrl + wheel for zoom.<br />
  Touchpad: work naturally. <br />
  touchpad pan speed: <input type="number" bind:value={panZoomState.panSpeed} />

  <br />
  <button
    onclick={() => {
      panZoomState.set({ x: 100, y: 100 });
    }}
  >
    reset pan
  </button>
</div>

<style>
  .control {
    border: 1px solid rgb(0 0 0 / 0.3);
    color: white;
    background-color: rgb(0 0 0 / 0.3);
    padding: 8px;
    position: relative;
    top: 0.6rem;
    left: 0.6rem;
    width: fit-content;
  }

  input[type="number"] {
    max-width: 50px;
  }
</style>
