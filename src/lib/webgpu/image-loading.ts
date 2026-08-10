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

/** Keyed by url, dedupes in-flight loads. */
abstract class UrlCache<T> {
  #cache = new Map<string, T>();
  #pending = new Map<string, Promise<T>>();

  protected abstract load(url: URL): Promise<T>;

  preload(url: URL) {
    const url_ = url.toString();
    const existing = this.#cache.get(url_) ?? this.#pending.get(url_);
    if (existing) {
      return Promise.resolve(existing);
    }

    const pending = (async () => {
      const value = await this.load(url);
      this.#cache.set(url_, value);
      this.#pending.delete(url_);

      return value;
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

  protected get cached() {
    return this.#cache.values();
  }

  protected clear() {
    this.#cache.clear();
    this.#pending.clear();
  }
}

/** Decoded `ImageBitmap`s. Nothing here touches the GPU. */
export class ImageCache extends UrlCache<ImageBitmap> {
  protected load(url: URL) {
    return fetchImage(url);
  }

  dispose() {
    for (const bitmap of this.cached) {
      bitmap.close();
    }
    this.clear();
  }
}

/**
 * `GPUTexture`s uploaded from an {@link ImageCache}. Bitmaps stay owned by the
 * image cache, so they are not closed here.
 */
export class GPUTextureCache extends UrlCache<GPUTexture> {
  #device: GPUDevice;
  #images: ImageCache;

  constructor(device: GPUDevice, images: ImageCache = new ImageCache()) {
    super();
    this.#device = device;
    this.#images = images;
  }

  get images() {
    return this.#images;
  }

  protected async load(url: URL) {
    const bitmap = await this.#images.getAsync(url);
    return loadTexture(this.#device, bitmap);
  }

  dispose() {
    for (const texture of this.cached) {
      texture.destroy();
    }
    this.clear();
  }
}
