<script lang="ts">
  import { onDestroy, onMount } from "svelte";
  import { GPUState } from "../../lib/webgpu/setup.svelte";
  import shaderCode from "./00.wgsl?raw";

  let canvas = $state<HTMLCanvasElement>();
  let gpu = new GPUState();

  onMount(() => {
    if (!canvas) {
      return;
    }
    gpu.configure(canvas).then(() => setup());
  });

  function setup() {
    const { device, context, presentationFormat } = gpu;
    const bindGroupLayout = device.createBindGroupLayout({
      entries: [],
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

    const currentTexture = context.getCurrentTexture();
    const view = currentTexture.createView();
    const encoder = device.createCommandEncoder();

    {
      const pass = encoder.beginRenderPass({
        colorAttachments: [
          {
            view: view,
            loadOp: "clear",
            storeOp: "store",
          },
        ],
      });

      pass.setPipeline(pipeline);
      pass.draw(3);
      pass.end();
    }

    device.queue.submit([encoder.finish()]);
  }

  onDestroy(() => {});
</script>

<canvas bind:this={canvas} width="1024" height="768"> </canvas>
<div class="control">hihi</div>

<style>
  canvas {
    border: 1px solid color(sRGB 0.8 0.8 0.8);
  }
  .control {
    border: 1px solid grey;
    border-radius: 6px;
    padding: 6px;
    margin-top: 1rem;
  }
</style>
