from pyquery import PyQuery as pq
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from EpubCrawler.util import opti_img
from EpubCrawler.config import config
from GenEpub import gen_epub
import sys
import json
import re
import hashlib
import base64
import time

RE_DATA_URL = r'^data:image/\w+;base64,'

JS_GET_IMG_B64 = '''
function getImageBase64(img_stor) {
    var img = document.querySelector(img_stor)
    if (!img) return ''
    var canvas = document.createElement("canvas");
    canvas.width = img.width;
    canvas.height = img.height;
    var ctx = canvas.getContext("2d");
    ctx.drawImage(img, 0, 0, img.width, img.height);
    var dataURL = canvas.toDataURL("image/png");
    return dataURL;
}
'''

def get_img_src(el_img):
    url = ''
    for prop in config['imgSrc']:
        url = el_img.attr(prop)
        if url: break
    return url
    
def process_img_data_url(url, el_img, imgs, **kw):
    if not re.search(RE_DATA_URL, url):
        return False
    picname = hashlib.md5(url.encode('utf-8')).hexdigest() + '.png'
    print(f'pic: {url} => {picname}')
    if picname not in imgs:
        enco_data = re.sub(RE_DATA_URL, '', url)
        data = base64.b64decode(enco_data.encode('utf-8'))
        data = opti_img(data, config['optiMode'], config['colors'])
        imgs[picname] = data
    el_img.attr('src', kw['img_prefix'] + picname)
    return True
    
def process_img(driver, html, imgs, **kw):
    kw.setdefault('img_prefix', 'img/')
    
    root = pq(html)
    el_imgs = root('img')
    
    for i in range(len(el_imgs)):
        el_img = el_imgs.eq(i)
        url = get_img_src(el_img)
        if not url: continue
        if process_img_data_url(url, el_img, imgs, **kw):
            continue
        if not url.startswith('http'):
            if kw.get('page_url'):
                url = urljoin(kw.get('page_url'), url)
            else: continue
        
        picname = hashlib.md5(url.encode('utf-8')).hexdigest() + '.png'
        print(f'pic: {url} => {picname}')
        if picname not in imgs:
            try:
                driver.get(url)
                b64 = driver.execute_script(
                    JS_GET_IMG_B64 + '\nreturn getImageBase64("body>img")')
                print(b64[:100])
                process_img_data_url(b64, el_img, imgs, **kw)
                time.sleep(config['wait'])
            except Exception as ex: print(ex)
        
    return root.html()

def main():
    
    config_fname = sys.argv[1] if len(sys.argv) > 1 else 'config.json'
    user_config = json.loads(open(config_fname, encoding='utf8').read())
    config.update(user_config)
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--log-level=3')
    driver = webdriver.Chrome(options=options)
    driver.get(config['url'])
    
    for kv in config.get('headers', {}).get('Cookie', '').split('; '):
        kv = kv.split('=')
        if len(kv) < 2: continue
        driver.add_cookie({'name': kv[0], 'value': kv[1]})
    driver.get(config['url'])
    
    
    articles = [{
        'title': config['name'],
        'content': f"<p>来源：<a href='" + config['url'] + "'>" + config['url'] + "</a></p>"
    }]
    imgs = {}
    
    for url in config['list']:
        try:
            print(url)
            if not re.search(r'https?://', url):
                articles.append({'title': url, 'content': ''})
                continue
            driver.get(url)
            html = driver.find_element_by_css_selector('body').get_attribute('outerHTML')
            root = pq(html)
            title = root(config['title']).eq(0).text().replace('\n', '')
            title = f'<h1>{title}</h1>'
            print(title)
            el_co = root(config['content'])
            co = '\n'.join([
                el_co.eq(i).html()
                for i in range(len(el_co))
            ])
            co = "<blockquote>来源：<a href='" + url + "'>" + url + "</a></blockquote>\n" + co
            co = process_img(driver, co, imgs, page_url=url, img_prefix='../Images/')
            articles.append({'title': title, 'content': co})
            time.sleep(config['wait'])
        except Exception as ex: print(ex)
    
    gen_epub(articles, imgs)
    driver.close()
    
if __name__ == '__main__': main()
