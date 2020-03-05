# coding: utf-8

# PDF 高清锐化
# 或者图片锐化打包 PDF
# python packpdf.py <pdf|dir> [-s <size>]

import numpy as np
import cv2
import sys
import os
from os import path
import re
from adathres import adaptive_thres
import tempfile
import time
import argparse
import shutil
import fitz
import img2pdf

def dump_pdf(fname, dir):

    RE_XOBJ = r"/Type\s*/XObject" 
    RE_IMG  = r"/Subtype\s*/Image"

    doc = fitz.open(fname)
    
    img_idcs = []
    for i in range(1, doc._getXrefLength()):
        xref = doc._getXrefString(i)
        
        is_xobj = re.search(RE_XOBJ, xref)
        is_img = re.search(RE_IMG, xref)
        if is_xobj and is_img: img_idcs.append(i)
        
    l = len(str(len(img_idcs) - 1))
    
    for i, j in enumerate(img_idcs):
        img = fitz.Pixmap(doc, j)
        if img.n >= 5:
            pix = fitz.Pixmap(fitz.csRGB, pix)
        imgname = path.join(dir, f'{i:0{l}d}.png')
        img.writePNG(imgname)
        
    doc.close()

    '''
    imgs = convert_from_path(fname)
    l = len(str(len(imgs) - 1))
    for i, img in enumerate(imgs):
        picname = path.join(dir, f'{i:0{l}d}.png')
        img.save(picname, 'png')
    '''

def gen_pdf(fname, dir):
    files = filter(is_pic, os.listdir(dir))
    files = list(map(lambda s: path.join(dir, s), files))
    pdf = img2pdf.convert(files)
    with open(fname, 'wb') as f:
        f.write(pdf)

def process_img(img, size=1440):
    # check grayscale
    assert img.ndim == 2
    
    # resize
    if size:
        nw = size
        h, w = img.shape
        rate = nw / w
        nh = round(h * rate)
        img = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_CUBIC)
    
    # bw
    img = adaptive_thres(img, 9)
    
    return img
    
is_pic = lambda s: s.endswith('.jpg') or \
                   s.endswith('.png') or \
                   s.endswith('.gif')
    
def process_dir(dir, **kwargs):
    
    if dir.endswith('\\') or dir.endswith('/'): dir = dir[:-1]
    p = path.join(path.dirname(dir), path.basename(dir) + '.pdf')
    if path.exists(p):
        print('文件已存在')
        return
        
    files = filter(is_pic, os.listdir(dir))
    
    for f in files:
        print(f)
        f = path.join(dir, f)
        img = cv2.imdecode(np.fromfile(f, np.uint8), cv2.IMREAD_GRAYSCALE)
        img = process_img(img, size=kwargs['size'])
        os.unlink(f)
        nf = re.sub(r'\.\w+$', '', f) + '.png'
        cv2.imwrite(nf, img, [
            # cv2.IMWRITE_PNG_COMPRESSION, 9,
            cv2.IMWRITE_PNG_BILEVEL, 1,
        ])

    gen_pdf(p, dir)
    
def process_pdf(fname, **kwargs):
    
    dir = path.join(tempfile.gettempdir(), str(time.time()))
    os.mkdir(dir)
    print(f'{fname} 导出中...')
    dump_pdf(fname, dir)
    print(f'{fname} 导出完毕')
    
    process_dir(dir, **kwargs)
    shutil.rmtree(dir)
    os.rename(fname, fname + '.bak')
    os.rename(dir + '.pdf', fname)
    
def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("fname", help="pdf or dir name")
    parser.add_argument("-s", "--size", type=int, default=1440, help="width of pics")
    args = parser.parse_args()
    
    if path.isdir(args.fname):
        process_dir(args.fname, size=args.size)
    elif args.fname.endswith('.pdf'):
        process_pdf(args.fname, size=args.size)
    else:
        print('请提供目录或 PDF')
        
        
if __name__ == '__main__': main()
