/*
npm install sync-request
npm install cheerio
npm install gen-epub@git+https://github.com/258ch/gen-epub
npm install iconv-lite
npm install sleep
apt install imagemagick
apt install pngquant
*/

var cheerio = require('cheerio');
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';
var {requestRetry} = require('./util.js');
var fs = require('fs');
var {URL} = require('url')
var genEpub = require('gen-epub')
var crypto = require('crypto');
var processImg = require('./img.js')
var iconv = require('iconv-lite')
var sleep = require('sleep')

var config = JSON.parse(fs.readFileSync('config.json', 'utf-8'))

function main() {
    
    var toc = getTocFromCfg()
    
    var articles = []
    var imgs = new Map()
    
    if(config.name) {
        articles.push({
            title: config.name, 
            content: `<p>来源：<a href='${config.url}'>${config.url}</a></p>`
        })
    }

    for(var i = 0; i< toc.length; i++) {
        try {
            var url = toc[i];
            console.log('page: ' + url);
            
            if(url.startsWith('http')) {
                
                var html = requestRetry('GET', url, {
                    headers: config.hdrs,
                    retry: config.n_retry,
                }).body
                html = iconv.decode(html, config.encoding)
                var res = getArticle(html, url)
                res.content = processImg(res.content, imgs, {
                    pageUrl: url, 
                    imgPrefix: '../Images/'
                })
                articles.push(res)
            }
            else 
                articles.push({title: url, content: ''})
            
            sleep.sleep(config.wait)
        } catch(ex) {
            console.log(ex);
            i--;
        }
    }
    
    genEpub(articles, imgs)
    console.log('Done..');
}

function getTocFromCfg() {
    
    if(config.list && config.list.length > 0)
        return config.list;
    
    if (!config.url) {
        console.log('请指定 URL')
        process.exit()
    }
    
    var html = requestRetry('GET', config.url, {
        retry: config.n_retry,
        headers: config.hdrs,
    }).body
    html = iconv.decode(html, config.encoding)
    var toc = getToc(html);
    return toc;
    
}

function getToc(html)  {
        
    var $ = cheerio.load(html);
    
    if(config.remove)
        $(config.remove).remove()
    
    var $list = $(config.link);
    var vis = new Set()

    var res = [];
    for(var i = 0; i < $list.length; i++)
    {
        var $link = $list.eq(i)
        var url = $link.attr('href');
        if(!url) {
            var text = $link.text()
            res.push(text)
            continue
        }
        
        url = url.replace(/#.*$/, '')
        if(config.base)
            url = new URL(url, config.base).toString()
        if(vis.has(url)) continue
        vis.add(url)
        res.push(url)
    }
    return res;
}

function getArticle(html, url) {
    if(config.processMath)
        html = processMath(html)
    if(config.processDecl)
        html = processDecl(html)
    
    var $ = cheerio.load(html);
    
    if(config.remove)
        $(config.remove).remove()
    
    // 只取一个元素
    var $title = $(config.title).eq(0)
    var title = $title.text().trim()
    $title.remove()
    
    // 解决 Cheerio 的 .html 多播问题
    var $co = $(config.content)
    var co = []
    for(var i = 0; i < $co.length; i++)
        co.push($co.eq(i).html())
    co = co.join('\r\n')

    if(config.credit) {
        var credit = `<blockquote>原文：<a href='${url}'>${url}</a></blockquote>`
        co = credit + co
    }
    
    return {title: title, content: co}
}

////////////////////////////////////////////////////

// for sphinx docs
function processDecl(html) {
    
    var $ = cheerio.load(html)
    $('colgroup').remove()
    
    var $dts = $('dt')
    
    for(var i = 0; i < $dts.length; i++) {
        var $dt = $dts.eq(i)
        $dt.find('a.reference').remove()
        var t = $dt.text()
        var $pre = $('<pre></pre>')
        $pre.text(t)
        $dt.replaceWith($pre)
    }
    
    return $.html()
}

function processMath(html){
    
    var $ = cheerio.load(html)
    
    var $maths = $('span.math, div.math');
    for(var i = 0; i < $maths.length; i++) {
        var $m = $maths.eq(i)
        var tex = $m.text().replace(/\\\[|\\\]|\\\(|\\\)/g, '')
        var url = 'http://latex.codecogs.com/gif.latex?' + encodeURIComponent(tex)
        var $img = $('<img />')
        $img.attr('src', url)
        if($m.is('div')) {
            var $p = $('<p></p>')
            $p.append($img)
            $img = $p
        }
        $m.replaceWith($img)
    }
    
    return $.html()
}

if(module == require.main) main()
