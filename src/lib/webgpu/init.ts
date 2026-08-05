import { onMount } from "svelte";

export async function initWebGPU(context: GPUCanvasContext) {
    const adapter = (await navigator.gpu.requestAdapter({}))!

    let device = await adapter.requestDevice({})

    context.configure({
        device,
        format: navigator.gpu.getPreferredCanvasFormat(),
        alphaMode: "premultiplied",
        colorSpace: "display-p3",
    })

    return {
        adapter,
        device
    }
}

// function useWebGPU(canvas: () => HTMLCanvasElement) {
//     onMount(() => {
//         const c = canvas();
//         if (!c) {
//             return;
//         }

//         let context = c.getContext("webgpu")!;
//         const stuff = initWebGPU(context)
//     });

// }