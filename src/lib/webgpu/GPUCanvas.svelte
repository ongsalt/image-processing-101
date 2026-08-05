<script module>
  export interface GPUState {
    canvas: HTMLCanvasElement;
    context: GPUCanvasContext;
    device: GPUDevice;
    adapter: GPUAdapter;
    presentationFormat: GPUTextureFormat;
  }

  export type MaybePromise<T> = T | Promise<T>;
  export type RenderFn = () => void;
  export type SetupFn = (state: GPUState) => MaybePromise<RenderFn>;
</script>

<script lang="ts">
  import { onDestroy, onMount } from "svelte";

  interface Props {
    setup?: SetupFn;
  }
  let { setup }: Props = $props();

  let canvas = $state<HTMLCanvasElement>();
  let device: GPUDevice | undefined;
  let observer: ResizeObserver | undefined;

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
    });

    const render = await setup!({
      device,
      adapter,
      canvas,
      context,
      presentationFormat: format,
    });

    render();

    observer = new ResizeObserver(([e]) => {
      const width =
        e.devicePixelContentBoxSize?.[0].inlineSize ||
        e.contentBoxSize[0].inlineSize * devicePixelRatio;
      const height =
        e.devicePixelContentBoxSize?.[0].blockSize ||
        e.contentBoxSize[0].blockSize * devicePixelRatio;
      const canvas = e.target as HTMLCanvasElement;
      canvas.width = Math.max(
        1,
        Math.min(width, device!.limits.maxTextureDimension2D),
      );
      canvas.height = Math.max(
        1,
        Math.min(height, device!.limits.maxTextureDimension2D),
      );

      // requestAnimationFrame(() => {
      render();
      // });
    });

    try {
      observer.observe(canvas, { box: "device-pixel-content-box" });
    } catch {
      observer.observe(canvas, { box: "content-box" });
    }
  });

  onDestroy(() => {
    device?.destroy();
    observer?.disconnect();
  });

  //   TODO: resize observer
</script>

<canvas bind:this={canvas}> </canvas>

<style>
  canvas {
    box-sizing: border-box;
    width: 100vw;
    height: 100vh;
    position: fixed;
    inset: 0;
    image-rendering: pixelated;
  }
</style>
