<script lang="ts">
  import { PanZoomState } from "$lib/pan.svelte";
  import { DisposeBag } from "$lib/utils";
  import GPUCanvas, { type SetupFn } from "$lib/webgpu/GPUCanvas.svelte";
  import { loadTextureFromURL } from "$lib/webgpu/image-loading";
  import shaderCode from "./01.wgsl?raw";

  const disposeBag = new DisposeBag();

  const panZoomState = new PanZoomState({ maxScale: 100 });
  panZoomState.set({ x: 300, y: 300, scale: 2 });

  type Sampling = "nearest" | "bilinear" | "bicubic";
  const settings = $state({
    sampling: "bilinear" satisfies Sampling,
  });

  const setup: SetupFn = async ({ device, context, presentationFormat }) => {
    // get the image
    const origin = new URL(window.location.href).origin;
    const imagePromise = loadTextureFromURL(
      // new URL("/miku.png", origin),
      new URL("/miku_small.png", origin),
      device,
    );

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

    const module = device.createShaderModule({
      code: shaderCode,
    });

    const pipeline = await device.createRenderPipelineAsync({
      layout: pipelineLayout,
      vertex: { module },
      fragment: { module, targets: [{ format: presentationFormat }] },
      primitive: { topology: "triangle-list" },
    });

    const image = await imagePromise;

    const bindGroup = device.createBindGroup({
      layout: bindGroupLayout,
      entries: [
        {
          binding: 0,
          resource: image,
        },
      ],
    });

    function render() {
      const currentTexture = context.getCurrentTexture();
      const view = currentTexture.createView();
      const encoder = device.createCommandEncoder();

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

        immediateBufferu32[0] =
          settings.sampling === "nearest"
            ? 0
            : settings.sampling === "bilinear"
              ? 1
              : 2;
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
      panZoomState.set({ x: 300, y: 300 });
    }}
  >
    reset pan
  </button>
</div>

<style>
  .overlay {
    position: fixed;
  }
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
