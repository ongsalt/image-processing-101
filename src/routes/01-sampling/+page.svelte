<script lang="ts">
  import { DisposeBag } from "$lib/utils";
  import GPUCanvas, { type SetupFn } from "$lib/webgpu/GPUCanvas.svelte";
  import shaderCode from "./01.wgsl?raw";

  let sampling = $state("nearest");
  let scale = $state(1);
  const disposeBag = new DisposeBag();

  const setup: SetupFn = ({ device, context, presentationFormat }) => {
    const configBuffer = device.createBuffer({
      size: 128,
      usage: GPUBufferUsage.UNIFORM | GPUBufferUsage.COPY_DST,
    });
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
    });

    const shaderModule = device.createShaderModule({
      code: shaderCode,
    });

    const pipeline = device.createRenderPipeline({
      layout: pipelineLayout,
      vertex: {
        module: shaderModule,
      },
      fragment: {
        module: shaderModule,
        targets: [
          {
            format: presentationFormat,
          },
        ],
      },
    });

    function render() {
      const currentTexture = context.getCurrentTexture();
      const view = currentTexture.createView();
      const encoder = device.createCommandEncoder();

      // device.queue.writeBuffer()

      {
        const pass = encoder.beginComputePass();
        pass.setImmediates;
      }

      device.queue.submit([encoder.finish()]);
    }

    const clear = $effect.root(() => {
      $effect(() => {
        console.log({ sampling, scale });
        render();
      });
    });

    disposeBag.add(clear);
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
