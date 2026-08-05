export async function fetchImage(url: URL) {
    const res = await fetch(url)
    const blob = await res.blob();
    const bitmap = await createImageBitmap(blob, { colorSpaceConversion: "none" });

    return bitmap
}

export async function loadTexture(device: GPUDevice, bitmap: ImageBitmap) {
    const texture = device.createTexture({
        size: [bitmap.width, bitmap.height],
        format: "rgba8unorm",
        usage: GPUTextureUsage.STORAGE_BINDING
            | GPUTextureUsage.TEXTURE_BINDING
            | GPUTextureUsage.COPY_DST
            | GPUTextureUsage.RENDER_ATTACHMENT,
    });

    device.queue.copyExternalImageToTexture(
        { source: bitmap, flipY: false },
        { texture, premultipliedAlpha: false },
        [bitmap.width, bitmap.height],
    );

    return texture
}

export async function loadTextureFromURL(url: URL, device: GPUDevice) {
    const bitmap = await fetchImage(url)
    const texture = await loadTexture(device, bitmap)
    bitmap.close()
    return texture
}
