# coding: utf-8

# 四阶灰度扩散仿色
# python diffdither.py <file>

import sys
import cv2
import numpy as np
import re
from argparse import ArgumentParser

def make_noise(size, fc=0, bc=255, k=2):
    # P(fc) = 1/k, P(bc) = (k-1)/k
    if k == 0: return np.zeros(size) + bc
    idx = np.random.random(size) < 1/k
    img = np.where(idx, fc, bc)
    return img

def make_strip(size, fc=0, bc=255, k=2):
    img = np.zeros(size) + bc
    for i in range(k):
        img[i::k, i::k] = fc
    return img

def make_grid(size, fc=0, bc=255, k=2):
    if k == 0: return np.zeros(size) + bc
    if k == 1: return np.zeros(size) + fc
    img = np.zeros(size) + bc
    img[0::k, 1::k] = fc
    img[1::k, 0::k] = fc
    img[1::k, 2::k] = fc
    img[2::k, 1::k] = fc
    return img
    

modes = {
    'grid': make_grid,
    'noise': make_noise,
    'strip': make_strip,
}


def process_img(img, mode='grid'):
    assert img.ndim == 2
    
    '''
    h, w = img.shape
    if size and w > size:
        nw = size
        rate = nw / w
        nh = round(h * rate)
        img = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_CUBIC)
    '''
    
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
        {'fc': 255, 'bc': 170, 'k': 4}, # c31
        {'fc': 170, 'bc': 255, 'k': 2}, # c32
        {'fc': 170, 'bc': 255, 'k': 4}, # c33
        {'fc': 0, 'bc': 255, 'k': 0}, # w
    ]

    
    delims = (clrs[1:] + clrs[:-1]) // 2
    delims = np.asarray([0, *delims, 255])
                       
    idcs = [((img >= st) & (img < ed)) for st, ed in zip(delims[:-1], delims[1:])]
    
    for idx, kwargs in zip(idcs, settings):
        pt = modes[mode](img.shape, **kwargs)
        img = img * (1 - idx) + pt * idx
    
    return img

def main():
    parser = ArgumentParser()
    parser.add_argument('fname')
    parser.add_argument('--mode', '-m', default='grid', choices=modes.keys())
    args = parser.parse_args()

    fname = args.fname
    print(fname)
    img = cv2.imdecode(np.fromfile(fname, np.uint8), cv2.IMREAD_GRAYSCALE)
    img = process_img(img, args.mode)
    fname = re.sub(r'\.\w+$', '', fname) + '.png'
    cv2.imwrite(fname, img, [cv2.IMWRITE_PNG_COMPRESSION, 9])
    
if __name__ == '__main__': main()
