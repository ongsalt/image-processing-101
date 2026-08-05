import { initWebGPU } from "./init";

export class GPUState {
    ready = $state(false)
    canvas = $state<HTMLCanvasElement>()!;
    context: GPUCanvasContext = undefined!;
    device: GPUDevice = undefined!;
    adapter: GPUAdapter = undefined!;
    presentationFormat: GPUTextureFormat = undefined!;

    constructor() { }

    async configure(canvas: HTMLCanvasElement) {
        this.canvas = canvas;
        this.context = canvas.getContext("webgpu")!;
        const a = await initWebGPU(this.context);
        this.adapter = a.adapter;
        this.device = a.device;
        this.ready = true
        this.presentationFormat = navigator.gpu.getPreferredCanvasFormat()
    }

    destroy() {

    }
}