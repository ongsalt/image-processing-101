from PIL import Image
import numpy as np
import bm3d

def median_filter(img, neighbor_size=3, adaptive=False, max_size=7):
    h, w = img.shape
    if not adaptive:
        max_size = neighbor_size
    max_pad = (max_size - 1) // 2

    out = np.empty(img.shape, dtype=np.float32)
    padded = np.pad(img, pad_width=max_pad, mode='edge') # repeat

    for y in range(h):
        for x in range(w):
            # image coord to padded coord
            px = x + max_pad
            py = y + max_pad
            center = padded[py, px]

            size = neighbor_size
            while True:
                pad_width = (size - 1) // 2
                # actual pos
                neighbor = padded[py-pad_width:py+pad_width+1, px-pad_width:px+pad_width+1]

                min = np.min(neighbor)
                max = np.max(neighbor)
                median = np.median(neighbor)

                if not adaptive:
                    out[y, x] = median
                    break

                # stage A: is the median itself an impulse?
                if min < median < max:
                    # stage B: is the center an impulse?
                    if min < center < max:
                        out[y, x] = center
                    else:
                        out[y, x] = median
                    break

                # median is an impulse -> grow window
                size += 2
                if size > max_size:
                    out[y, x] = median
                    break

    return out.astype(np.uint8)

def impulse_median_filter(img, neighbor_size=3, tolerance=0):
    # only touch pixels that are salt (255) or pepper (0)
    # tolerance: jpeg smears impulses (255 -> 242), so also treat <= tolerance and >= 255 - tolerance as impulse
    h, w = img.shape
    pad_width = (neighbor_size - 1) // 2

    out = img.copy()
    padded = np.pad(img, pad_width=pad_width, mode='edge') # repeat

    for y in range(h):
        for x in range(w):
            center = img[y, x]
            if tolerance < center < 255 - tolerance:
                continue

            # image coord to padded coord
            px = x + pad_width
            py = y + pad_width
            # actual pos
            neighbor = padded[py-pad_width:py+pad_width+1, px-pad_width:px+pad_width+1]
            out[y, x] = np.median(neighbor)

    return out

def wiener_filter(img, neighbor_size=3, noise_var=0.0):
    # adaptive local wiener: out = mean + (var - noise_var) / var * (x - mean)
    pad_width = (neighbor_size - 1) // 2
    normalized = img / 255
    padded = np.pad(normalized, pad_width=pad_width, mode='edge') # repeat

    # every neighborhood at once, shape (h, w, n, n)
    neighbors = np.lib.stride_tricks.sliding_window_view(padded, (neighbor_size, neighbor_size))
    local_mean = np.mean(neighbors, axis=(2, 3))
    local_var = np.var(neighbors, axis=(2, 3))

    # dont know the noise -> guess it from average local variance

    # flat area (var ~ noise) -> use mean, edge (var >> noise) -> keep pixel
    gain = np.maximum(local_var - noise_var, 0) / np.maximum(local_var, noise_var)
    out = local_mean + gain * (normalized - local_mean)

    return np.clip(out * 255, 0, 255).astype(np.uint8)

def gaussian_blur(img, neighbor_size=3, sigma=None):
    # weighted mean, closer neighbors count more: weight = exp(-(x^2 + y^2) / (2 sigma^2))
    # default sigma: window covers +-3 sigma
    if sigma is None:
        sigma = neighbor_size / 6
    pad_width = (neighbor_size - 1) // 2
    padded = np.pad(img.astype(np.float64), pad_width=pad_width, mode='edge') # repeat

    d = np.arange(neighbor_size) - pad_width # -2, -1, 0, 1, 2
    kernel = np.exp(-d ** 2 / (2 * sigma ** 2))
    kernel /= np.sum(kernel) # weights sum to 1 so brightness stays the same

    # gaussian is separable
    # -> blur rows with 1d kernel, then blur columns. n + n work per pixel instead of n * n
    # (neighbors * kernel on a (h, w, n, n) view would allocate h * w * n * n floats)
    h, w = img.shape
    rows = np.zeros((h + 2 * pad_width, w))
    for i, k in enumerate(kernel):
        rows += k * padded[:, i:i+w]
    out = np.zeros((h, w))
    for i, k in enumerate(kernel):
        out += k * rows[i:i+h, :]

    return np.clip(out, 0, 255).astype(np.uint8)

def geometric_mean_filter(img, neighbor_size=3):
    # (product of neighbors) ^ (1 / n)  ==  exp(mean(log(neighbors)))
    pad_width = (neighbor_size - 1) // 2
    # +1 so log(0) doesnt explode, a single 0 would make the whole product 0
    padded = np.pad(img.astype(np.float64) + 1, pad_width=pad_width, mode='edge') # repeat

    # every neighborhood at once, shape (h, w, n, n)
    neighbors = np.lib.stride_tricks.sliding_window_view(padded, (neighbor_size, neighbor_size))
    out = np.exp(np.mean(np.log(neighbors), axis=(2, 3))) - 1

    return np.clip(out, 0, 255).astype(np.uint8)

def non_local_means_filter(img, noise_sd, patch_size=5, search_size=11, h=None):
    # average pixels whose *patch around them* looks similar, not just pixels that are nearby
    # -> repeated stuff (siding, roof) gets averaged with itself, edges dont get mixed with background
    if h is None:
        h = 0.6 * noise_sd
    x = img.astype(np.float64)
    hh, ww = x.shape
    r = search_size // 2
    padded = np.pad(x, pad_width=r, mode='edge') # repeat

    total = np.zeros_like(x)
    weight_sum = np.zeros_like(x)
    # loop over offsets instead of pixels, every pixel at once per offset
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            shifted = padded[r+dy:r+dy+hh, r+dx:r+dx+ww]

            # mean squared diff between patch at p and patch at p + offset
            diff = np.pad((x - shifted) ** 2, pad_width=patch_size // 2, mode='edge')
            dist = np.mean(np.lib.stride_tricks.sliding_window_view(diff, (patch_size, patch_size)), axis=(2, 3))

            # two noisy copies of the same patch already differ by 2 * noise_sd^2, dont punish that
            weight = np.exp(-np.maximum(dist - 2 * noise_sd ** 2, 0) / h ** 2)
            total += weight * shifted
            weight_sum += weight

    return np.clip(total / weight_sum, 0, 255).astype(np.uint8)

def bm3d_filter(img, noise_sd=23):
    # block matching + 3d filtering (bm3d package)
    # find similar patches like nlm, stack them into 3d, transform, drop small coefficients (noise)
    # noise_sd in 0..255 units, lower keeps more texture
    out = bm3d.bm3d(img / 255, sigma_psd=noise_sd / 255)
    return np.clip(out * 255, 0, 255).astype(np.uint8)

def gaussian_psf(shape, sigma):
    # blur kernel as big as the image, peak at (0, 0) so fft doesnt shift the result
    h, w = shape
    y = np.fft.fftfreq(h) * h # 0, 1, 2, ..., -2, -1
    x = np.fft.fftfreq(w) * w
    psf = np.exp(-(y[:, None] ** 2 + x[None, :] ** 2) / (2 * sigma ** 2))
    return psf / np.sum(psf)

def inverse_deconvolution(img, sigma=2.0, cutoff=0.001):
    # plain inverse filter: F = G / H
    # H ~ 0 at high freq -> noise / 0 = boom, so only invert below cutoff (cycles/pixel, max 0.5)
    if img.ndim == 3:
        # rgb
        return np.stack([inverse_deconvolution(img[..., c], sigma, cutoff) for c in range(img.shape[2])], axis=2)

    pad_width = int(3 * sigma) + 1
    padded = np.pad(img / 255, pad_width=pad_width, mode='edge') # repeat

    H = np.fft.fft2(gaussian_psf(padded.shape, sigma))
    G = np.fft.fft2(padded)
    F = G / H

    out = np.real(np.fft.ifft2(F))

    out = out[pad_width:-pad_width, pad_width:-pad_width]
    return np.clip(out * 255, 0, 255).astype(np.uint8)

def wiener_deconvolution(img, sigma=2.0, k=0.01):
    # blurry = sharp * psf  ->  G = F H  ->  F = conj(H) / (|H|^2 + k) * G
    # k ~ noise / signal power, 0 = plain inverse filter (blows up noise)
    if img.ndim == 3:
        # rgb
        return np.stack([wiener_deconvolution(img[..., c], sigma, k) for c in range(img.shape[2])], axis=2)

    # fft assumes the image wraps around, pad so left edge doesnt ring with right edge
    pad_width = int(3 * sigma) + 1
    padded = np.pad(img / 255, pad_width=pad_width, mode='edge') # repeat

    H = np.fft.fft2(gaussian_psf(padded.shape, sigma))
    G = np.fft.fft2(padded)
    F = np.conj(H) / (np.abs(H) ** 2 + k) * G
    out = np.real(np.fft.ifft2(F))

    out = out[pad_width:-pad_width, pad_width:-pad_width]
    return np.clip(out * 255, 0, 255).astype(np.uint8)

def tv_deconvolution(img, sigma=2.0, lam=0.002, rho=None, iterations=100):
    # find f that minimizes  0.5 * ||blur(f) - g||^2 + lam * sum |grad f|
    #   data term: re-blurring f should give back the photo
    #   tv term: L1 on gradient -> one sharp jump is as cheap as a ramp, wiggles (ringing, noise) are expensive
    # solved with ADMM (split bregman): introduce d = grad f, then alternate
    #   1. f step: quadratic -> exact solve with one fft division (like wiener)
    #   2. d step: shrink grad f toward 0 (small gradients = noise -> 0, big = edges -> keep)
    #   3. b step: accumulate how far d and grad f disagree
    if img.ndim == 3:
        # rgb
        return np.stack([tv_deconvolution(img[..., c], sigma, lam, rho, iterations) for c in range(img.shape[2])], axis=2)

    if rho is None:
        rho = 10 * lam

    # fft assumes the image wraps around, pad so left edge doesnt ring with right edge
    pad_width = int(3 * sigma) + 1
    g = np.pad(img / 255, pad_width=pad_width, mode='edge') # repeat
    h, w = g.shape

    H = np.fft.fft2(gaussian_psf(g.shape, sigma))
    # forward difference f[x + 1] - f[x] in frequency domain
    Dx = np.exp(2j * np.pi * np.fft.fftfreq(w))[None, :] - 1
    Dy = np.exp(2j * np.pi * np.fft.fftfreq(h))[:, None] - 1

    HtG = np.conj(H) * np.fft.fft2(g)
    denominator = np.abs(H) ** 2 + rho * (np.abs(Dx) ** 2 + np.abs(Dy) ** 2)

    f = g.copy()
    dx = np.zeros_like(g); dy = np.zeros_like(g)
    bx = np.zeros_like(g); by = np.zeros_like(g)
    for _ in range(iterations):
        # 1. f step
        numerator = HtG + rho * (np.conj(Dx) * np.fft.fft2(dx - bx) + np.conj(Dy) * np.fft.fft2(dy - by))
        f = np.real(np.fft.ifft2(numerator / denominator))

        # 2. d step: isotropic shrink of (grad f + b) by lam / rho
        gx = np.roll(f, -1, axis=1) - f
        gy = np.roll(f, -1, axis=0) - f
        vx = gx + bx; vy = gy + by
        magnitude = np.sqrt(vx ** 2 + vy ** 2)
        shrink = np.maximum(magnitude - lam / rho, 0) / np.maximum(magnitude, 1e-12)
        dx = shrink * vx; dy = shrink * vy

        # 3. b step
        bx += gx - dx
        by += gy - dy

    out = f[pad_width:-pad_width, pad_width:-pad_width]
    return np.clip(out * 255, 0, 255).astype(np.uint8)

def disk_psf(shape, radius):
    # out of focus lens spreads a point into a flat circle, peak at (0, 0) like gaussian_psf
    h, w = shape
    y = np.fft.fftfreq(h) * h # 0, 1, 2, ..., -2, -1
    x = np.fft.fftfreq(w) * w
    psf = (y[:, None] ** 2 + x[None, :] ** 2 <= radius ** 2).astype(np.float64)
    return psf / np.sum(psf)

def defocus_deconvolution(img, radius=5, k=0.01):
    # wiener deconvolution with disk psf: F = conj(H) / (|H|^2 + k) * G
    # k ~ noise / signal power, 0 = plain inverse filter
    if img.ndim == 3:
        # rgb
        return np.stack([defocus_deconvolution(img[..., c], radius, k) for c in range(img.shape[2])], axis=2)

    # fft assumes the image wraps around, pad so left edge doesnt ring with right edge
    pad_width = int(radius) + 1
    padded = np.pad(img / 255, pad_width=pad_width, mode='edge') # repeat

    H = np.fft.fft2(disk_psf(padded.shape, radius))
    G = np.fft.fft2(padded)
    F = np.conj(H) / (np.abs(H) ** 2 + k) * G
    out = np.real(np.fft.ifft2(F))

    out = out[pad_width:-pad_width, pad_width:-pad_width]
    return np.clip(out * 255, 0, 255).astype(np.uint8)

def unsharp_mask(img, neighbor_size=9, amount=1.5):
    # img - blur = edges only, add them back on top: out = img + amount * (img - blur)
    if img.ndim == 3:
        # rgb
        return np.stack([unsharp_mask(img[..., c], neighbor_size, amount) for c in range(img.shape[2])], axis=2)

    blurred = gaussian_blur(img, neighbor_size)
    out = img + amount * (img.astype(np.float64) - blurred)

    return np.clip(out, 0, 255).astype(np.uint8)

if __name__ == "__main__":
    # image_path = "../static/cabin1.jpg"
    # output_path = "./out/cabin1_adaptive_median_top.jpg"
    # output_path = "./out/cabin1_impulse_median.jpg"

    # image_path = "../static/stop_sign.jpg"
    # output_path = "./out/stop_sign_wiener.jpg"

    # image_path = "../static/cabin2.jpg"
    # output_path = "./out/cabin2.jpg"

    image_path = "../static/moon.jpeg"
    output_path = "./out/moon_unsharp.jpg"

    image = Image.open(image_path)
    # image = image.convert('L')
    data = np.array(image)

    # out = median_filter(data, 3)
    out = median_filter(data, 5, adaptive=True, max_size=7)
    out = median_filter(out, 3, adaptive=True, max_size=3)
    # out = wiener_filter(data, 7, 0.1)
    # out = inverse_deconvolution(data, 4, 0.01)
    # out = non_local_means_filter(data, 28.5, 3, 11)
    # out = gaussian_blur(data, 5)
    out = unsharp_mask(data, 21, 3)

    out = Image.fromarray(out)
    out.save(output_path)
