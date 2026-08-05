<script module>
  export interface GPUState {
    canvas: HTMLCanvasElement;
    context: GPUCanvasContext;
    device: GPUDevice;
    adapter: GPUAdapter;
    presentationFormat: GPUTextureFormat;
  }
  export type SetupFn = (state: GPUState) => void;
</script>

<script lang="ts">
  import { onDestroy, onMount, type Snippet } from "svelte";

  interface Props {
    setup?: SetupFn;
  }
  let { setup }: Props = $props();

  let canvas = $state<HTMLCanvasElement>();
  let device: GPUDevice | undefined;

  onMount(async () => {
    if (!canvas) {
      return;
    }

    const context = canvas.getContext("webgpu")!;
    const format = navigator.gpu.getPreferredCanvasFormat();
    const adapter = (await navigator.gpu.requestAdapter({}))!;
    device = await adapter.requestDevice({});

    context.configure({
      device,
      format: navigator.gpu.getPreferredCanvasFormat(),
      alphaMode: "premultiplied",
      colorSpace: "display-p3",
    });

    setup?.({
      device,
      adapter,
      canvas,
      context,
      presentationFormat: format,
    });
  });

  onDestroy(() => {
    device?.destroy();
  });

  //   TODO: resize observer
</script>

<canvas bind:this={canvas} width="1024" height="768"> </canvas>

<style>
  canvas {
    border: 1px solid color(sRGB 0.8 0.8 0.8);
  }
</style>
