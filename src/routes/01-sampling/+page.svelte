<script lang="ts">
  import { DisposeBag } from "$lib/utils";
  import GPUCanvas, { type SetupFn } from "$lib/webgpu/GPUCanvas.svelte";
  import shaderCode from "./01.wgsl?raw";

  let sampling = $state("nearest");
  let scale = $state(1);
  const disposeBag = new DisposeBag();

  const setup: SetupFn = async ({ device, context, presentationFormat }) => {
    const bindGroupLayout = device.createBindGroupLayout({
      entries: [
        {
          binding: 0,
          visibility: GPUShaderStage.COMPUTE,
        },
      ],
    });

    const pipelineLayout = device.createPipelineLayout({
      bindGroupLayouts: [bindGroupLayout],
      immediateSize: 40,
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
        pass.setImmediates(
          0,
          new Uint32Array([
            // sampling mode
            0,
            // sourceSize
            0, 0,
            // size
            1, 1,
            // offset
            0, 0,
          ]),
        );
      }

      device.queue.submit([encoder.finish()]);
    }

    const stop = $effect.root(() => {
      $effect(() => {
        console.log({ sampling, scale });
        requestAnimationFrame(() => {
          render();
        });
      });
    });

    disposeBag.add(stop);
  };
</script>

<GPUCanvas {setup} />
<div class="control">
  <div>
    <label>
      Sampling
      <select bind:value={sampling}>
        <option value="bilinear">bilinear</option>
        <option value="nearest">nearest</option>
        <!-- <option value="bicubic">bicubic</option> -->
      </select>
    </label>
  </div>
  <div>
    <label>
      Scale
      <input type="range" min="0.1" max="3" bind:value={scale} step="0.1" />
    </label>
  </div>
</div>

<style>
  .control {
    border: 1px solid grey;
    border-radius: 6px;
    padding: 6px;
    margin-top: 1rem;
  }
</style>
