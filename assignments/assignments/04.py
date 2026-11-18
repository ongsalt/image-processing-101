from PIL import Image
import numpy as np

# axes=(0, 1) -> only transform over height/width, so rgb (h, w, 3) is done per channel

def fft_image(img):
    F = np.fft.fft2(img.astype(np.float32), axes=(0, 1))
    return np.fft.fftshift(F, axes=(0, 1))

def ifft_image(F, offset=0):
    out = np.real(np.fft.ifft2(np.fft.ifftshift(F, axes=(0, 1)), axes=(0, 1)))
    return np.clip(np.round(out + offset), 0, 255).astype(np.uint8)

def magnitude_spectrum(F):
    mag = np.log1p(np.abs(F))
    mag = mag / mag.max() * 255
    return mag.astype(np.uint8)

def phase_spectrum(F):
    phase = (np.angle(F) + np.pi) / (2 * np.pi) * 255
    return phase.astype(np.uint8)

def save_spectrum(F, path, phase_path=None):
    # F: spectrum from fft_image (or after filtering), saved as is, no re-fft
    # rgb: average the channels, fft is linear so this = spectrum of the gray-ish image
    if F.ndim == 3:
        F = F.mean(axis=2)
    Image.fromarray(magnitude_spectrum(F)).save(path)
    if phase_path:
        Image.fromarray(phase_spectrum(F)).save(phase_path)

def distance_from_center(shape):
    h, w = shape[:2]
    y = np.arange(h) - h // 2
    x = np.arange(w) - w // 2
    return np.sqrt(y[:, None] ** 2 + x[None, :] ** 2)

def lowpass_mask(shape, cutoff, kind="gaussian"):
    D = distance_from_center(shape)
    if kind == "ideal":
        # hard cut
        return (D <= cutoff).astype(np.float32)
    if kind == "gaussian":
        return np.exp(-(D ** 2) / (2 * cutoff ** 2))
    raise ValueError(kind)

def highpass_mask(shape, cutoff, kind="gaussian"):
    return 1 - lowpass_mask(shape, cutoff, kind)

def fill_rect(H, y0, y1, x0, x1, value):
    # coords relative to the spectrum center, end exclusive, either order works
    y0, y1 = sorted((y0, y1))
    x0, x1 = sorted((x0, x1))
    h, w = H.shape[:2]
    cy, cx = h // 2, w // 2
    H[max(cy + y0, 0):max(cy + y1, 0), max(cx + x0, 0):max(cx + x1, 0)] = value
    return H

def strip_reject_mask(shape, half_width=1, start=40, axis="vertical", floor=0.0):
    h, w = shape[:2]
    H = np.ones((h, w), dtype=np.float32)
    if axis == "horizontal":
        H = H.T

    n = H.shape[0]
    x0, x1 = -half_width, half_width + 1
    fill_rect(H, -n, -start + 1, x0, x1, floor)  # top
    fill_rect(H, start, n, x0, x1, floor)        # bottom

    return H.T if axis == "horizontal" else H

def strip_filter(F, half_width=1, start=40, axis="vertical", floor=0.0):
    # spectrum in, spectrum out. fft_image before, ifft_image after
    return apply_mask(F, strip_reject_mask(F.shape, half_width, start, axis, floor))

def apply_mask(F, H):
    # rgb: (h, w) mask -> (h, w, 1) so it broadcasts over the 3 channels
    if F.ndim == 3:
        H = H[..., None]
    return F * H

def lowpass_filter(img, cutoff, kind="gaussian"):
    F = fft_image(img)
    return ifft_image(apply_mask(F, lowpass_mask(F.shape, cutoff, kind)))

def highpass_filter(img, cutoff, kind="gaussian"):
    # dc is removed so the result sits around 0, shift by 128 to see negatives
    F = fft_image(img)
    return ifft_image(apply_mask(F, highpass_mask(F.shape, cutoff, kind)), offset=128)

if __name__ == "__main__":
    image_path = "../static/diag_noisy_animals.jpg"
    input_image = Image.open(image_path)
    output_path = "./out/a4/animal/1.jpg" 
    input_data = np.array(input_image)

    F = fft_image(input_data)
    G = strip_filter(F, half_width=4, start=20, axis="horizontal", floor=0)
    G = strip_filter(G, half_width=4, start=20, axis="vertical", floor=0)

    for y_sign in (-1, 1):
        for x_sign in (-1, 1):
            fill_rect(G, y_sign * 34, y_sign * 42, x_sign * 23, x_sign * 257 , 0)
            fill_rect(G, y_sign * 34, y_sign * 156, x_sign * 25, x_sign * 32, 0)
    # fill_rect(G, 30, -30, 60, 120, 0)

    out = ifft_image(G)
    Image.fromarray(out).save(output_path)

    save_spectrum(F, "./out/a4/animal/1_spectrum_before.png")
    save_spectrum(G, "./out/a4/animal/1_spectrum_after.png")


# 2
# F = fft_image(input_data)
# G = strip_filter(F, half_width=6, start=20, axis="horizontal", floor=0)

# fill_rect(G, 30, -30, -60, -120, 0)
# fill_rect(G, 30, -30, 60, 120, 0)



# for r in [10, 50, 100]:
#     out = lowpass_filter(input_data, r)
#     out = Image.fromarray(out)
#     out.save(output_path + f"lowpass_gaussian{r}.jpg")

#     out = highpass_filter(input_data, r)
#     out = Image.fromarray(out)
#     out.save(output_path + f"highpass_gaussian{r}.jpg")

#     out = lowpass_filter(input_data, r, kind="ideal")
#     out = Image.fromarray(out)
#     out.save(output_path + f"lowpass_ideal{r}.jpg")

#     out = highpass_filter(input_data, r, kind="ideal")
#     out = Image.fromarray(out)
#     out.save(output_path + f"highpass_ideal{r}.jpg")



