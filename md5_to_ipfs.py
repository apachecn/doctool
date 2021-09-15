import hashlib
import re
import requests
from os import path
import os
import sys
from concurrent.futures import ThreadPoolExecutor

def process_file(fname):
    if not path.isfile(fname): return
    bts = open(fname, 'rb').read()
    md5 = hashlib.md5(bts).hexdigest().upper()
    r = requests.get(f'http://library.lol/main/{md5}')
    print(r.status_code)
    if r.status_code == 404:
        print(f'{path.basename(fname)}：未上传')
        return
    tk = re.findall('(?<=/ipfs/)\w+', r.text)[0]
    print(f'{path.basename(fname)}：f{tk}')
    
def tr_process_file_safe(fname):
    try:
        process_file(fname)
    except Exception as ex: 
        print(ex)
    
def process_dir(dir):
    fnames = os.listdir(dir)
    pool = ThreadPoolExecutor(1)
    hdls = []
    for f in fnames:
        f = path.join(dir, f)
        hdl = pool.submit(tr_process_file_safe, f)
        hdls.append(hdl)
    for h in hdls: h.result()
        
def main():
    fname = sys.argv[1]
    
    if path.isdir(fname):
        process_dir(fname)
    else:
        process_file(fname)

if __name__ == '__main__': main()
        