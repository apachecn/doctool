from io import BytesIO
import zipfile
from os import path
from imgyaso import pngquant_bts
import sys
from EpubCrawler.util import is_pic, safe_mkdir, safe_rmdir
import subprocess as subp
import re

def convert_to_epub(fname):
    nfname = re.sub(r'\.\w+$', '', fname) + '.epub'
    print(f'{fname} => {nfname}')
    subp.Popen(f'ebook-convert "{fname}" "{nfname}"', 
        shell=True, stdin=subp.PIPE, stdout=subp.PIPE).communicate()
    if not path.exists(nfname):
        raise FileNotFoundError(f'{nfname} not found')
    return nfname

def main():
    fname = sys.argv[1]
    if fname.endswith('.mobi') or \
        fname.endswith('.azw3'):
            fname = convert_to_epub(fname)
    elif not fname.endswith('.epub'):
        print('请提供EPUB')
        return
        
    bio = BytesIO(open(fname, 'rb').read())
    zip = zipfile.ZipFile(bio, 'r', zipfile.ZIP_DEFLATED)
    new_bio = BytesIO()
    new_zip = zipfile.ZipFile(new_bio, 'w', zipfile.ZIP_DEFLATED)
    
    for n in zip.namelist():
        print(n)
        data = zip.read(n)
        if is_pic(n):
            data = pngquant_bts(data)
        new_zip.writestr(n, data)
        
    zip.close()
    new_zip.close()
    open(fname, 'wb').write(new_bio.getvalue())
    print('done...')
        
        
if __name__ == '__main__': main()
