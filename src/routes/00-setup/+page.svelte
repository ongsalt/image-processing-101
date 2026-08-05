<script lang="ts">
  import GPUCanvas, { type SetupFn } from "$lib/webgpu/GPUCanvas.svelte";
  import shaderCode from "./00.wgsl?raw";

  const setup: SetupFn = ({ device, context, presentationFormat }) => {
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
  };
</script>

<GPUCanvas {setup} />
