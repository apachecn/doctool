var fs = require('fs');
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';
var {requestRetry} = require('./util.js');
var crypto = require('crypto');
var cheerio = require('cheerio');
var path = require('path')
var betterImg = require('./img-better.js')

var isDir = s => fs.statSync(s).isDirectory()

function mkdirSyncSafe(dir) {
    try {fs.mkdirSync(dir)} catch(ex) {}
}

function main() {
    
    var fname = process.argv[2];
    if(!fname)
    {
        console.log('请指定文件或目录。');
        process.exit(0);
    }
    
    if(isDir(fname)) {
        mkdirSyncSafe(path.join(fname, 'img'))
        processDir(fname)
    } else {
        mkdirSyncSafe(path.join(path.dirname(fname), 'img'))
        processFile(fname)
    }
}

function processDir(dir) {
    var files = fs.readdirSync(dir);
    for(var fname of files) {
        fname = path.join(dir, fname)
        processFile(fname)
    }
}

function processFile(fname) {
    if(!fname.endsWith('.html') &&
       !fname.endsWith('.md'))
        return;
    console.log('file: ' + fname);
    var content = fs.readFileSync(fname, 'utf-8');
    var imgs = new Map()
    if(fname.endsWith('.html'))
        content = processImg(content, imgs);
    else
        content = processImgMd(content, imgs);
    fs.writeFileSync(fname, content);
    var dir = path.join(path.dirname(fname), 'img')
    for(var [fname, img] of imgs.entries()) {
        fs.writeFileSync(path.join(dir, fname), img)
    }
}

function processImgMd(md, imgs, options={}) {
    options.imgPrefix = options.imgPrefix || 'img/'
    
    var re = /!\[.*?\]\((.*?)\)/g
    var rm;
    while(rm = re.exec(md)) {
        try {
            var url = rm[1]
            if(!url) continue
            if(!url.startsWith('http')) {
                if(options.pageUrl)
                    url = new URL(url, options.pageUrl).toString()
                else
                    continue
            }
            
            var picname = crypto.createHash('md5').update(url).digest('hex') + ".jpg";
            console.log(`pic: ${url} => ${picname}`)
            
            if(!imgs.has(picname)) {
                var data = requestRetry('GET', url).getBody();
                data = betterImg(data)
                imgs.set(picname, data);
            }
            
            md = md.split(rm[1]).join(options.imgPrefix + picname)
        } catch(ex) {console.log(ex.toString())}
    }
    
    return md
}

function processImg(html, imgs, options={}) {
    
    options.imgPrefix = options.imgPrefix || 'img/'
    
    var $ = cheerio.load(html);
    
    var $imgs = $('img');

    for(var i = 0; i < $imgs.length; i++) {
        
        try {
            var $img = $imgs.eq(i);
            var url = $img.attr('src') || 
                      $img.data('src') ||
                      $img.data('original-src')
            if(!url) continue
            if(!url.startsWith('http')) {
                if(options.pageUrl)
                    url = new URL(url, options.pageUrl).toString()
                else
                    continue
            }
            
            var picname = crypto.createHash('md5').update(url).digest('hex') + ".jpg";
            console.log(`pic: ${url} => ${picname}`)
            
            if(!imgs.has(picname)) {
                var data = requestRetry('GET', url).getBody();
                data = betterImg(data)
                imgs.set(picname, data);
            }
            
            $img.attr('src', options.imgPrefix + picname);
        } catch(ex) {console.log(ex.toString())}
    }
    
    return $.html();

}

module.exports = processImg
module.exports.processImg = processImg
module.exports.processImgMd = processImgMd

if(module == require.main) main();
