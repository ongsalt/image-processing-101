export async function fetchImage(url: URL) {
  const res = await fetch(url);
  const blob = await res.blob();
  const bitmap = await createImageBitmap(blob, {
    colorSpaceConversion: "default",
  });

  return bitmap;
}

export async function loadTexture(device: GPUDevice, bitmap: ImageBitmap) {
  // gamma encoded
  const texture = device.createTexture({
    size: [bitmap.width, bitmap.height],
    format: "rgba8unorm",
    usage:
      GPUTextureUsage.STORAGE_BINDING |
      GPUTextureUsage.TEXTURE_BINDING |
      GPUTextureUsage.COPY_DST |
      GPUTextureUsage.RENDER_ATTACHMENT,
  });

  device.queue.copyExternalImageToTexture(
    { source: bitmap },
    { texture },
    [bitmap.width, bitmap.height],
  );

  return texture;
}

export async function loadTextureFromURL(url: URL, device: GPUDevice) {
  const bitmap = await fetchImage(url);
  const texture = await loadTexture(device, bitmap);
  bitmap.close();
  return texture;
}

export class ImageCache {
  #cache = new Map<string, GPUTexture>();
  #pending = new Map<string, Promise<GPUTexture>>();
  #device: GPUDevice;

  constructor(device: GPUDevice) {
    this.#device = device;
  }

  async preload(url: URL) {
    const url_ = url.toString();
    let existing = this.#cache.get(url_) ?? this.#pending.get(url_);
    if (existing) {
      return existing;
    }

    const pending = (async () => {
      const bitmap = await fetchImage(url);
      const texture = await loadTexture(this.#device, bitmap);
      this.#cache.set(url_, texture);
      this.#pending.delete(url_);

      bitmap.close();
      return texture;
    })();

    this.#pending.set(url_, pending);

    return pending;
  }

  async waitAll() {
    await Promise.all(this.#pending.values());
  }

  get(url: URL) {
    return this.#cache.get(url.toString());
  }

  getAsync(url: URL) {
    return this.preload(url);
  }
}
