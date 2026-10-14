from PIL import Image
import argparse
from pathlib import Path
import numpy as np

def zoom(pixels, size: tuple[int, int]):
    h, w = size
    out = np.zeros((h*4, w*4), dtype=np.uint8)
    for y in range(0, h*4):
        for x in range(0, w*4):
            out[y, x] = pixels[y//4, x//4]

    return out


def shrink(pixels, size: tuple[int, int]):
    h, w = size
    out = np.zeros((h//4, w//4), dtype=np.uint8)
    for y in range(0, h//4):
        for x in range(0, w//4):
            out[y, x] = pixels[y * 4, x * 4]
    return out


def requantize(image: Image.Image, bits: int):
    p = np.array(image, dtype=np.uint32)
    # truncate
    p = p >> (8 - bits)
    # rescale for displaying
    p = (p * 255) // (2**bits - 1)
    return p.astype(np.uint8)


def parse_args():
    p = argparse.ArgumentParser()

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("images", nargs="+")
    common.add_argument("-o", "--out", default="out")

    subparsers = p.add_subparsers(dest="mode", required=True)
    subparsers.add_parser("zoom", parents=[common])
    subparsers.add_parser("shrink", parents=[common])

    requantize = subparsers.add_parser("requantize", parents=[common])
    requantize.add_argument("-b", "--bits", type=int, default=1)

    return p.parse_args()


if __name__ == "__main__":
    print(np.show_runtime())
    args = parse_args()
    for image_path in args.images:
        image = Image.open(image_path)
        greyscale_image = image.convert('L')
        size = greyscale_image.size

        if args.mode == "zoom":
            out = zoom(greyscale_image.load(), size)
        elif args.mode == "shrink":
            out = shrink(greyscale_image.load(), size)
        else:
            out = requantize(greyscale_image, args.bits)
            
        out = Image.fromarray(out)
        out.save(Path(args.out) / Path(image_path).name)
