from PIL import Image
import numpy as np

def global_hist_eq(img):
    view = np.ravel(img)
    count = np.bincount(view, minlength=255)
    c = np.cumsum(count) / view.size * 255
    out = c[img].astype(np.uint8)
    return out

def local_hist_eq(img, neighbor_size=3, k0=0.4, k1=0.02, k2=0.4, e=4.0):
    # brute forceee
    h, w = img.shape
    pad_width = (neighbor_size - 1) // 2

    out = np.empty(img.shape, dtype=np.float32)
    normalized = img / 255
    padded = np.pad(normalized, pad_width=pad_width, mode='edge') # repeat

    mean = np.mean(normalized)
    sd = np.std(normalized)
    count = 0

    for y in range(h):
        for x in range(w):
            # image coord to padded coord
            px = x + pad_width
            py = y + pad_width
            # actual pos
            neighbor = padded[py-pad_width:py+pad_width+1, px-pad_width:px+pad_width+1]        
            local_mean = np.mean(neighbor)
            local_sd = np.std(neighbor)

            if local_mean <= k0 * mean and k1 * sd <= local_sd <= k2 * sd:
                count += 1
                out[y, x] = e * padded[py, px]
            else:
                out[y, x] = padded[py, px]
    print(count)
    return np.clip(out * 255, 0, 255).astype(np.uint8)

def global_gamma_correction(img, gamma=0.7):
    return (((img / 255) ** gamma) * 255).astype(np.uint8)

gamma_2x2 = [2, 2, 2, 0.5]
gamma_3x3 = [2, 2, 2, 2, 2, 0.5, 2, 0.5, 0.5]
def tiled_gamma_correction(img, gamma=gamma_3x3):
    normalized = img / 255.0
    tile_count = int(len(gamma) ** 0.5)
    i = 0
    for row_or_col_idk in np.array_split(normalized, tile_count, axis=1):
        for tile in np.array_split(row_or_col_idk, tile_count, axis=0):
            # inplace
            np.pow(tile, gamma[i], out=tile)
            i += 1

    return (normalized * 255).astype(np.uint8)


if __name__ == "__main__":
    image_path = "../static/filament.jpg"
    # output_path = "./out/filament_local_hist_eq_3x3.jpg"
    output_path = "./out/filament_global_gamma_correction_2.jpg"
    # output_path = "./out/filament_2x2_gamma_correction.jpg"
    # output_path = "./out/filament_3x3_gamma_correction.jpg"
    image = Image.open(image_path)
    image = image.convert('L')
    data = np.array(image)

    # out = global_hist_eq(data)
    # out = local_hist_eq(data)
    out = global_gamma_correction(data, 2)
    # out = tiled_gamma_correction(data)

    out = Image.fromarray(out)
    out.save(output_path)
