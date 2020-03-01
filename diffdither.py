# coding: utf-8

# 四阶灰度扩散仿色
# python diffdither.py <file>

import sys
import cv2
import numpy as np
import re

def make_strip(size, fc=0, bc=255, k=2):
    img = np.zeros(size) + bc
    for i in range(k):
        img[i::k, i::k] = fc
    return img


def process_img(img):
    assert img.ndim == 2
    
    h, w = img.shape
    if w > 1000:
        rate = 1000 / w
        nh = round(h * rate)
        img = cv2.resize(img, (1000, nh), interpolation=cv2.INTER_CUBIC)
    
    # b=0, c11, c12, c13, 
    # c1=85, c21, c22, c23,
    # c2=170, c31, c32, c33, w=255
    clrs = np.linspace(0, 255, 13).astype(int)

    settings = [
        {'fc': 0, 'bc': 0, 'k': 0}, # b
        {'fc': 85, 'bc': 0, 'k': 4}, # c11
        {'fc': 0, 'bc': 85, 'k': 2}, # c12
        {'fc': 0, 'bc': 85, 'k': 4}, # c13
        {'fc': 0, 'bc': 85, 'k': 0}, # c1
        {'fc': 170, 'bc': 85, 'k': 4}, # c21
        {'fc': 85, 'bc': 170, 'k': 2}, # c22
        {'fc': 85, 'bc': 170, 'k': 4}, # c23
        {'fc': 0, 'bc': 170, 'k': 0}, # c2
        {'fc': 170, 'bc': 255, 'k': 4}, # c31
        {'fc': 170, 'bc': 255, 'k': 2}, # c32
        {'fc': 255, 'bc': 170, 'k': 4}, # c33
        {'fc': 0, 'bc': 255, 'k': 0}, # w
    ]
    
    delims = (clrs[1:] + clrs[:-1]) // 2
    delims = np.asarray([0, *delims, 255])
                       
    idcs = [((img >= st) & (img < ed)) for st, ed in zip(delims[:-1], delims[1:])]
    
    for idx, kwargs in zip(idcs, settings):
        pt = make_strip(img.shape, **kwargs)
        img = img * (1 - idx) + pt * idx
    
    return img

def main():
    fname = sys.argv[1]
    print(fname)
    img = cv2.imdecode(np.fromfile(fname, np.uint8), cv2.IMREAD_GRAYSCALE)
    img = process_img(img)
    fname = re.sub(r'\.\w+$', '', fname) + '.png'
    cv2.imwrite(fname, img, [cv2.IMWRITE_PNG_COMPRESSION, 9])
    
if __name__ == '__main__': main()
