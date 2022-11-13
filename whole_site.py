import sys
from collections import deque
from urllib.parse import urljoin
import requests
from pyquery import PyQuery as pq

site = sys.argv[1]
q = deque([site])
vis = set([site])
f = open('out.txt', 'a')

while q:
    url = q.popleft()
    print(url)
    f.write(url + '\n')
    html = requests.get(url).text
    rt = pq(html)
    el_links = rt('a')
    links = [
        urljoin(site, el_links.eq(i).attr('href')) 
        for i in range(len(el_links))
    ]
    links = [
        l for l in links 
        if l.startswith(site) and l not in vis
    ]
    for l in links:
        q.append(l)
        vis.add(l)
    
f.close()
