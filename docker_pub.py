from os import path
import os
import sys
import subprocess as subp
import requests
from datetime import datetime

DOCKERFILE = '''
FROM httpd:2.4
COPY ./ /usr/local/apache2/htdocs/
'''

def get_latest_fix_ver(name, cur):
    now = datetime.now()
    cur = cur or \
        f'{now.year}.{now.month}.{now.day}.'
    url = f'https://registry.hub.docker.com/v2/repositories/{name}/tags/?page_size=100&page=1&name={cur}&ordering=last_updated'
    j = requests.get(url).json()
    fix_vers = [
        int(r['name'].split('.')[-1])
        for r in j['results']
    ]
    if len(fix_vers) == 0:
        return 0
    else:
        return max(fix_vers) + 1

def main():
    dir = sys.argv[1]
    if dir.endswith('/') or \
       dir.endswith('\\'):
        dir = dir[:-1]
    if not path.exists(dir):
        print('目录不存在')
        return
    
    fnames = os.listdir(dir)
    if 'README.md' not in fnames or \
       'index.html' not in fnames:
        print('请提供文档目录')
        return
        
    if 'Dockerfile' not in fnames:
        open(path.join(dir, 'Dockerfile'), 'w').write(DOCKERFILE)
        
    name = path.basename(dir).lower()
    now = datetime.now()
    ver = f'{now.year}.{now.month}.{now.day}.'
    fix_ver = get_latest_fix_ver(
        'apachecn0/' + name, ver)
    ver += str(fix_ver)
    print(f'name: {name}, ver: {ver}')
    
    cmds = [
        f'docker build -t apachecn0/{name}:{ver} {dir}',
        f'docker push apachecn0/{name}:{ver}',
        f'docker tag apachecn0/{name}:{ver} apachecn0/{name}:latest',
        f'docker push apachecn0/{name}:latest',
    ]
    for cmd in cmds:
        subp.Popen(cmd, shell=True).communicate()
    
    
if __name__ == '__main__': main()