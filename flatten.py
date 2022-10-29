form os import path
import sys
import os

def main():
    dir = sys.argv[1]
    if not path.isdir(dir):
        print('请提供目录！')
        return
        
    for rt, _, fnames in os.walk(dir):
        rel_rt = rt[len(dir)+1:]
        for fnames in fnames:
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