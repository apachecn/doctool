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
import tempfile
import time
import argparse
import shutil
import fitz
import img2pdf
from imgyaso import adathres
import subprocess as subp
import platform
import uuid

def dump_pdf(fname, dir):

    RE_XOBJ = r"/Type\s*/XObject" 
    RE_IMG  = r"/Subtype\s*/Image"

    doc = fitz.open(fname)
    
    img_idcs = []
    for i in range(1, doc.xref_length()):
        xref = doc.xref_object(i)
        
        is_xobj = re.search(RE_XOBJ, xref)
        is_img = re.search(RE_IMG, xref)
        if is_xobj and is_img: img_idcs.append(i)
        
    l = len(str(len(img_idcs) - 1))
    
    for i, j in enumerate(img_idcs):
        print(f'no: {i}, xref: {j}')
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

def process_img(img, size=1900, deskew=True):
    # firstly deskew
    if deskew:
        img = magick_deskew(img)
    
    img = np.frombuffer(img, np.uint8)
    img = cv2.imdecode(img, cv2.IMREAD_GRAYSCALE)
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
    img = adathres(img, 9)
    
    img = cv2.imencode('.png', img, [
        cv2.IMWRITE_PNG_BILEVEL, 1,
    ])[1]
    return bytes(img)
    
is_pic = lambda s: s.endswith('.jpg') or \
                   s.endswith('.png') or \
                   s.endswith('.gif')
    
def process_dir(args):
    
    dir = args.fname
    if dir.endswith('\\') or dir.endswith('/'): dir = dir[:-1]
    p = path.join(path.dirname(dir), path.basename(dir) + '.pdf')
    if path.exists(p):
        print('文件已存在')
        return
        
    files = filter(is_pic, os.listdir(dir))
    
    for f in files:
        print(f)
        f = path.join(dir, f)
        img = open(f, 'rb').read()
        img = process_img(img, size=args.size, deskew=args.deskew)
        open(f, 'wb').write(img)

    gen_pdf(p, dir)
    
def magick_deskew(img):
    fname = path.join(tempfile.gettempdir(), uuid.uuid4().hex + '.png')
    open(fname, 'wb').write(img)
    cmd = f'convert "{fname}" -deskew 40% "{fname}"'
    if platform.system().lower() == 'windows':
        cmd = 'magick ' + cmd
    subp.Popen(cmd, shell=True).communicate()
    return open(fname, 'rb').read()
    
def process_pdf(args):
    
    dir = path.join(tempfile.gettempdir(), str(time.time()))
    os.mkdir(dir)
    fname = args.fname
    print(f'{fname} 导出中...')
    dump_pdf(fname, dir)
    print(f'{fname} 导出完毕')
    
    args.fname = dir
    process_dir(args)
    shutil.rmtree(dir)
    os.rename(fname, fname + '.bak')
    shutil.move(dir + '.pdf', fname)
    
def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("fname", help="pdf or dir name")
    parser.add_argument("-s", "--size", type=int, default=1900, help="width of pics")
    parser.add_argument("-d", "--deskew", action='store_true', help="deskew or not")
    args = parser.parse_args()
    
    if path.isdir(args.fname):
        process_dir(args)
    elif args.fname.endswith('.pdf'):
        process_pdf(args)
    else:
        print('请提供目录或 PDF')
        
        
if __name__ == '__main__': main()
