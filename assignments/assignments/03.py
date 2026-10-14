from PIL import Image
import numpy as np

def global_hist_eq(img):
    view = np.ravel(img)
    count = np.bincount(view, minlength=255)
    c = np.cumsum(count) / view.size * 255
    out = c[img].astype(np.uint8)
    return out

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

def impulse_median_filter(img, neighbor_size=3):
    # only touch pixels that are exactly salt (255) or pepper (0)
    h, w = img.shape
    pad_width = (neighbor_size - 1) // 2

    out = img.copy()
    padded = np.pad(img, pad_width=pad_width, mode='edge') # repeat

    for y in range(h):
        for x in range(w):
            center = img[y, x]
            if center != 0 and center != 255:
                continue

            # image coord to padded coord
            px = x + pad_width
            py = y + pad_width
            # actual pos
            neighbor = padded[py-pad_width:py+pad_width+1, px-pad_width:px+pad_width+1]
            out[y, x] = np.median(neighbor)

    return out

def wiener_filter(img, neighbor_size=3, noise_var=None):
    # adaptive local wiener: out = mean + (var - noise_var) / var * (x - mean)
    pad_width = (neighbor_size - 1) // 2
    normalized = img / 255
    padded = np.pad(normalized, pad_width=pad_width, mode='edge') # repeat

    # every neighborhood at once, shape (h, w, n, n)
    neighbors = np.lib.stride_tricks.sliding_window_view(padded, (neighbor_size, neighbor_size))
    local_mean = np.mean(neighbors, axis=(2, 3))
    local_var = np.var(neighbors, axis=(2, 3))

    # dont know the noise -> guess it from average local variance
    if noise_var is None:
        noise_var = np.mean(local_var)

    # flat area (var ~ noise) -> use mean, edge (var >> noise) -> keep pixel
    gain = np.maximum(local_var - noise_var, 0) / np.maximum(local_var, noise_var)
    out = local_mean + gain * (normalized - local_mean)

    return np.clip(out * 255, 0, 255).astype(np.uint8)

if __name__ == "__main__":
    image_path = "../static/cabin1.jpg"
    # output_path = "./out/cabin1_median.jpg"
    output_path = "./out/cabin1_adaptive_median_top.jpg"
    output_path = "./out/cabin1_impulse_median.jpg"
    # image_path = "../static/cabin2.jpg"
    # output_path = "./out/cabin2_wiener.jpg"
    image = Image.open(image_path)
    image = image.convert('L')
    data = np.array(image)

    # out = median_filter(data, 3)
    out = median_filter(data, 5, adaptive=True, max_size=7)
    out = median_filter(out, 3, adaptive=True, max_size=3)
    # out = wiener_filter(data, 3)

    out = Image.fromarray(out)
    out.save(output_path)
