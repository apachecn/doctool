# coding: utf-8

# 自适应二值化（扫描全能王的增强锐化）
# python adathres.py <file|dir>

import numpy as np
from scipy import signal
import cv2
import re
import os
from os import path
import sys

def adaptive_thres(img, win=9, beta=0.9):
    if win % 2 == 0: win = win - 1
    # 边界的均值有点麻烦
    # 这里分别计算和和邻居数再相除
    kern = np.ones([win, win])
    sums = signal.correlate2d(img, kern, 'same')
    cnts = signal.correlate2d(np.ones_like(img), kern, 'same')
    means = sums // cnts
    # 如果直接采用均值作为阈值，背景会变花
    # 但是相邻背景颜色相差不大
    # 所以乘个系数把它们过滤掉
    img = np.where(img < means * beta, 0, 255)
    return img

def process_file(fname):
    if not fname.endswith('.png') and \
       not fname.endswith('.jpg') and \
       not fname.endswith('.gif'):
        return
        
    print(fname)
    img = cv2.imdecode(np.fromfile(fname, np.uint8), cv2.IMREAD_GRAYSCALE)
    img = adaptive_thres(img)
    os.unlink(fname)
    nfname = re.sub(r'\.\w+$', '', fname) + '.png'
    cv2.imwrite(nfname, img, [cv2.IMWRITE_PNG_BILEVEL, 1])
    
def procee_dir(dir):
    files = os.listdir(dir)
    for fname in files:
        fname = path.join(dir, fname)
        process_file(fname)
        
def main():
    fname = sys.argv[1]
    if path.isdir(fname):
        procee_dir(fname)
    else:
        process_file(fname)
        
if __name__ == '__main__': main()
