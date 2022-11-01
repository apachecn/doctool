from os import path
import sys
import os

def main():
    dir = sys.argv[1]
    if not path.isdir(dir):
        print('请提供目录！')
        return
    
    if not dir.endswith('/') and \
       not dir.endswith('\\'):
       dir += '/'
        
    for rt, _, fnames in os.walk(dir):
        rel_rt = rt[len(dir):]
        for fname in fnames:
            print(path.join(rel_rt, fname))
            nfname = (
                path.join(rel_rt, fname)
                    .replace('/', '：')
                    .replace('\\', '：')
            )
            os.rename(
                path.join(rt, fname),
                path.join(dir, nfname),
            )
            
    print('done...')
    
if __name__ == '__main__': main()