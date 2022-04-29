import re
import os
from os import path
import shutil
import sys
import subprocess as subp

README_TMP = '''
# {title}

## 下载

### Docker

```
docker pull apachecn0/{docker_hub_name}
docker run -tid -p <port>:80 apachecn0/{docker_hub_name}
# 访问 http://localhost:{port} 查看文档
```

### PYPI

```
pip install {pip_name}
{pip_name} <port>
# 访问 http://localhost:{port} 查看文档
```

### NPM

```
npm install -g {npm_name}
{npm_name} <port>
# 访问 http://localhost:{port} 查看文档
```
'''

INDEX_HTML = '''
<html>
<head></head>
<body style="margin: 0;">
    <iframe src='file.pdf' style='width: 100%; height: 100%; border: 0;'></iframe>
</body>
</html>
'''

numPinyinMap = {
    '0': 'ling',
    '1': 'yi',
    '2': 'er',
    '3': 'san',
    '4': 'si',
    '5': 'wu',
    '6': 'liu',
    '7': 'qi',
    '8': 'ba',
    '9': 'jiu',
}

def npm_filter_name(name):
    name = re.sub(r'[^\w\-]', '-', name)
    name = '-'.join(filter(None, name.split('-')))
    
    def rep_func(m):
        s = m.group()
        return ''.join(numPinyinMap.get(ch, '') for ch in s)
    
    name = re.sub(r'\d{2,}', rep_func, name)
    return name


def main():
    name = sys.argv[1]
    fname = sys.argv[2]
    dir = sys.argv[3] if len(sys.argv) > 3 else '.'
    
    if not fname.endswith('.pdf'):
        print('请提供 PDF')
        return 
    
    proj_dir = path.join(dir, name)
    os.mkdir(proj_dir)
    
    shutil.copy(fname, path.join(proj_dir, 'file.pdf'))
    open(path.join(proj_dir, 'index.html'), 'w', encoding='utf8').write(INDEX_HTML)
    title = fname.replace('.pdf', '')
    npm_name = npm_filter_name(name)
    README_MD = README_TMP \
        .replace('{title}', title) \
        .replace('{docker_hub_name}', name) \
        .replace('{pip_name}', name) \
        .replace('{npm_name}', npm_name)
    open(path.join(proj_dir, 'README.md'), 'w', encoding='utf8').write(README_MD)
    
    '''
    if site in ['all', 'npm']:
        subp.Popen(
            f'nbp publish "{proj_dir}"',
            shell=True,
        ).communicate()
        
    if site in ['all', 'pip']:
        subp.Popen(
            f'pybp publish "{proj_dir}"',
            shell=True,
        ).communicate()
    
    if site in ['all', 'docker']:
        subp.Popen(
            f'python docker_pub.py "{proj_dir}"',
            shell=True,
        ).communicate()
        
    os.rmdir(proj_dir)
    '''

if __name__ == '__main__': main()