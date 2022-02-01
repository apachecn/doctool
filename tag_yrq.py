import requests
import sys
import re
from pyquery import PyQuery as pq
from datetime import datetime

config = {
    'dateElem': 'time',
    'format': '%Y-%m-%d',
}

def get_yrq(dt_str):
    dt = datetime.strptime(dt_str, config['format'])
    yr = dt.year
    q = (dt.month - 1) // 3 + 1
    return f'{yr}Q{q}'

def main():
    fname = sys.argv[1]
    urls = open(fname, encoding='utf-8').read().split('\n')
    urls = filter(None, map(lambda x: x.strip(), urls))
    
    ofname = re.sub(r'\.\w+$', '', fname) + '.out.txt'
    ofile = open(ofname, 'a', encoding='utf=8')
    last_yrq = None
    
    for url in urls:
        html = requests.get(url).text
        dt_str = pq(html) \
            .find(config['dateElem']) \
            .eq(0).text().strip()
        yrq = get_yrq(dt_str)
        if yrq != last_yrq:
            print(yrq)
            ofile.write(yrq + '\n')
            last_yrq = yrq
        ofile.write(url + '\n')
        print(url)
        
    ofile.close()
        
if __name__ == '__main__': main()