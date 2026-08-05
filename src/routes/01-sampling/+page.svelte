<script lang="ts">
  import { DisposeBag } from "$lib/utils";
  import GPUCanvas, { type SetupFn } from "$lib/webgpu/GPUCanvas.svelte";
  import { loadTextureFromURL } from "$lib/webgpu/image-loading";
  import shaderCode from "./01.wgsl?raw";

  let settings = $state({
    sampling: "nearest",
    scale: 1.0,
    x: 300,
    y: 300,
  });

  const disposeBag = new DisposeBag();

  const setup: SetupFn = async ({
    device,
    context,
    presentationFormat,
    canvas,
  }) => {
    const origin = new URL(window.location.href).origin;
    const imagePromise = loadTextureFromURL(
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

      // device.queue.writeBuffer()

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

        const f32 = new Float32Array(immediateBuffer); // is a view
        const u32 = new Uint32Array(immediateBuffer);
        u32[0] = 0; // sampling mode
        f32.set(
          [
            // sourceSize
            image.width,
            image.height,
            // scale
            settings.scale,
            settings.scale,
            // offset
            settings.x,
            settings.y,
          ],
          2,
        );

        pass.setImmediates(0, immediateBuffer);
        pass.draw(6);
        pass.end();
      }

      device.queue.submit([encoder.finish()]);
    }

    const stop = $effect.root(() => {
      $effect(() => {
        $state.snapshot(settings);
        requestAnimationFrame(() => {
          render();
        });
      });
    });

    disposeBag.add(stop);

    return render;
  };
</script>

<GPUCanvas {setup} />
<div class="control">
  <div>
    <label>
      Sampling
      <select bind:value={settings.sampling}>
        <option value="bilinear">bilinear</option>
        <option value="nearest">nearest</option>
        <!-- <option value="bicubic">bicubic</option> -->
      </select>
    </label>
  </div>
  <div>
    <label>
      Scale
      <input type="range" min="0.1" max="10" bind:value={settings.scale} step="0.001" />
    </label>
  </div>

  <div>
    <label>
      x
      <input type="range" min="0" max="1000" bind:value={settings.x} step="0.01" />
    </label>
  </div>

  <div>
    <label>
      y
      <input type="range" min="0" max="1000" bind:value={settings.y} step="0.01" />
    </label>
  </div>
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
</style>
