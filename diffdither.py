# coding: utf-8

import sys
import cv2
import numpy as np
import re

# 四阶灰度扩散仿色
# python diffdither.py <file>

def build_pattern(shape, a0, a1, a2, a3):
    arr = np.zeros(shape)
    arr[::2, ::2] = a0
    arr[::2, 1::2] = a1
    arr[1::2, ::2] = a2
    arr[1::2, 1::2] = a3
    return arr

# 0 85 170 255
def process_img(img):
    assert img.ndim == 2
    
    h, w = img.shape
    if w > 1000:
        rate = 1000 / w
        nh = round(h * rate)
        img = cv2.resize(img, (1000, nh), interpolation=cv2.INTER_CUBIC)
    
    b, l11, l12, g1, l21, l22, g2, l31, l32, w = np.linspace(0, 255, 10).astype(int)

    pt11 = build_pattern(img.shape, b, b, b, g1)
    pt12 = build_pattern(img.shape, b, g1, g1, b)
    pt13 = build_pattern(img.shape, b, g1, g1, g1)
    pt21 = build_pattern(img.shape, g1, g1, g1, g2)
    pt22 = build_pattern(img.shape, g1, g2, g2, g1)
    pt23 = build_pattern(img.shape, g1, g2, g2, g2)
    pt31 = build_pattern(img.shape, g2, g2, g2, w)
    pt32 = build_pattern(img.shape, g2, w, w, g2)
    pt33 = build_pattern(img.shape, g2, w, w, w)
                       
    cond11 = lambda x: (x > b) & (x < l11)
    cond12 = lambda x: (x >= l11) & (x < l12)
    cond13 = lambda x: (x >= l12) & (x < g1)
    cond21 = lambda x: (x > g1) & (x < l21)
    cond22 = lambda x: (x >= l21) & (x < l22)
    cond23 = lambda x: (x >= l22) & (x < g2)
    cond31 = lambda x: (x > g2) & (x < l31)
    cond32 = lambda x: (x >= l31) & (x < l32)
    cond33 = lambda x: (x >= l32) & (x < w)
    pts = {
        cond11: pt11,
        cond12: pt12,
        cond13: pt13,
        cond21: pt21,
        cond22: pt22,
        cond23: pt23,
        cond31: pt31,
        cond32: pt32,
        cond33: pt33,
    }
    
    for cond, pt in pts.items():
        idx = cond(img).astype(int)
        img = img * (1 - idx) + pt * idx
    
    return img

def main():
    fname = sys.argv[1]
    print(fname)
    img = cv2.imread(fname, cv2.IMREAD_GRAYSCALE)
    img = process_img(img)
    fname = re.sub(r'\.\w+$', '', fname) + '.png'
    cv2.imwrite(fname, img, [cv2.IMWRITE_PNG_COMPRESSION, 9])
    
if __name__ == '__main__': main()
