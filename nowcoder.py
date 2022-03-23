import os
from os import path
import sys
import re
from datetime import datetime
from pyquery import PyQuery as pq
from EpubCrawler.util import request_retry
from EpubCrawler.img import process_img

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    'accept-language': 'zh-CN,zh;q=0.9',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36',
    'Cache-Control': 'no-cache', 
    'Pragma': 'no-cache', 
    'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="99", "Google Chrome";v="99"', 
    'sec-ch-ua-mobile': '?0', 
    'sec-ch-ua-platform': '"Windows"', 
    'Sec-Fetch-Dest': 'document', 
    'Sec-Fetch-Mode': 'navigate', 
    'Sec-Fetch-Site': 'none', 
    'Sec-Fetch-User': '?1', 
    'Upgrade-Insecure-Requests': '1', 
    'Cookie': os.environ.get('NC_COOKIE', ''),
}

def get_info(html):
    RE_TID = r'tid: \'(\d+)\''
    RE_QID = r'qid: \'(\d+)\''
    RE_TOTAL = r'total: \'(\d+)\''
    RE_TITLE = r'paperName: \'(.+?)\''
    m = re.search(RE_TID, html)
    tid = m.group(1) if m else ''
    m = re.search(RE_QID, html)
    qid = m.group(1) if m else ''
    m = re.search(RE_TOTAL, html)
    total = m.group(1) if m else '0'
    m = re.search(RE_TITLE, html)
    title = m.group(1) if m else ''
    return {
        'tid': tid, 
        'qid': qid, 
        'total': int(total), 
        'title': title
    }
    
def get_content(html):
    html = re.sub(r'<(/?)h\d', r'<\1p', html)
    rt = pq(html)
    rt('.result-subject-answer .clearfix, .topic-quality, .contain-knowledge-box').remove()
    num = rt('.result-question-box .question-number').text()
    ques = rt('.result-question-box .question-main').html()
    ans = rt('.result-subject-answer').html()
    tag = rt('.knowledge-point').html()
    ans2 = rt('.result-subject-answer+result-subject-item').html()
    replies = ''
    el_replies = rt('.answer-content')
    for i in range(len(el_replies)):
        el = el_replies.eq(i)
        link = 'https://www.nowcoder.com' + \
            el.find('.answer-head').attr('href')
        name = el.find('.answer-name').text()
        cont = el.find('.answer-brief').html()
        tm = el.find('.answer-time').text()
        replies += f'''
            <p><a href='{link}'>{name}</a></p>
            {cont}
            <p>{tm}</p>
            <hr/>
        '''
    return f'''
        <h2>{num}</h2>
        {ques}
        {ans or ''}
        {ans2 or ''}
        {tag}
        {'<p>讨论</p>' + replies if replies else ''}
    '''
    
def get_title(html):
    return pq(html).find('.paper-title').text()
    
def get_qids(html):
    els = pq(html).find('.subject-num-list li a')
    return [
        els.eq(i).attr('data-qid')
        for i in range(len(els))
    ]

def download(pid):
    fname = f'out/{pid}.html'
    if path.isfile(fname):
        print(f'{pid} 已存在')
        return
    
    url = f'https://www.nowcoder.com/test/{pid}/begin'
    r = request_retry(
        'POST', url, headers=headers, allow_redirects=False)
    url = r.headers.get('Location')
    html = request_retry(
        'GET', url, headers=headers).text
    info = get_info(html)
    if not info['tid'] or not info['qid']:
        print(f'{pid} TID, QID 获取失败')
        return
    tid, qid, title = info['tid'], info['qid'], info['title']
    url = f'https://www.nowcoder.com/test/question/done?tid={tid}&qid={qid}'
    html = request_retry(
        'GET', url, headers=headers).text
    qids = get_qids(html)
    if len(qids) == 0:
        print(f'{pid} QIDS 获取失败')
        return
    print(pid, title, tid, qids)
    art_html = f'<h1>{title}</h1>'
    for i, qid in enumerate(qids):
        print(qid)
        url = f'https://www.nowcoder.com/test/question/done?tid={tid}&qid={qid}'
        html = request_retry('GET', url, headers=headers).text
        cont = get_content(html)
        art_html += cont
    
    imgs = {}
    art_html = process_img(
        art_html, imgs, page_url=url)
    for iname, img in list(imgs.items()):
        if img[:4] == b'<svg':
            iname2 = iname.replace('.png', '.svg')
            art_html = art_html.replace(iname, iname2)
            imgs[iname2] = img
            del imgs[iname]
    try: os.mkdir('out')
    except: pass
    open(f'out/{pid}.html', 'w', encoding='utf-8').write(art_html)
    try: os.mkdir('out/img')
    except: pass
    for iname, img in imgs.items():
        open(f'out/img/{iname}', 'wb').write(img)
    print('done')

def fetch(st=None, ed=None):
    url_tmpl = 'https://www.nowcoder.com/api/questiontraining/companyPaper/getCompanypaperList?orderByHotValue=3&jobId=0&pageSize=45&page={page}&filter=0&mutiTagIds='
    
    i = 1
    stop = False
    while not stop:
        url = url_tmpl.replace('{page}', str(i))
        print(url)
        hdrs = headers.copy()
        hdrs['Cookie'] = 'acw_sc__v2=623b401866fbc3f05bf6ecb156035d9ea88a80af'
        j = request_retry('GET', url, headers=hdrs).json()
        if j['code'] != 0: break
        for it in j['data']['paperVos']:
            dt = datetime.fromtimestamp(it['properties']['paper']['createTime'] / 1000)
            dt_str = f'{dt.year}{dt.month:02d}{dt.day:02d}'
            if ed and dt_str > ed: continue
            if st and dt_str < dt:
                stop = True
                break
            pid = it['properties']['contentItemClick']['contentID_var']
            download(str(pid))
        i += 1

def main():
    cmd = sys.argv[1]
    if cmd in ['download', 'dl']:
        download(sys.argv[2])
    elif cmd == 'fetch':
        fetch(
            sys.argv[2] if len(sys.argv) > 2 else None,
            sys.argv[3] if len(sys.argv) > 3 else None,
        )

if __name__ == '__main__': main()
