<script lang="ts">
  import GPUCanvas, { type SetupFn } from "$lib/webgpu/GPUCanvas.svelte";
  import shaderCode from "./shader.wgsl?raw";

  const IMMEDIATE_SIZE = 32; // padded
  const immediateBuffer = new ArrayBuffer(IMMEDIATE_SIZE);
  const immediateBufferf32 = new Float32Array(immediateBuffer); // is a view

  const setup: SetupFn = ({ device, context, presentationFormat, canvas }) => {
    const bindGroupLayout = device.createBindGroupLayout({
      entries: [
        {
          binding: 0,
          visibility: GPUShaderStage.FRAGMENT,
          sampler: {
            type: "filtering",
          },
        },
        {
          binding: 1,
          visibility: GPUShaderStage.FRAGMENT,
          texture: {},
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

    return function render() {
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

        pass.setPipeline(pipeline);
        pass.draw(6);
        pass.end();
      }

      device.queue.submit([encoder.finish()]);
    };
  };
</script>

<GPUCanvas {setup} />
