var fs = require('fs');
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';
var request = require('sync-request');
var crypto = require('crypto');
var cheerio = require('cheerio');
var path = require('path')
var betterImg = require('./img-better.js')

var config = JSON.parse(fs.readFileSync('config.json', 'utf-8'))

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
    if(!fname.endsWith('.html'))
        return;
    console.log('file: ' + fname);
    var content = fs.readFileSync(fname, 'utf-8');
    var imgs = new Map()
    content = processImg(content, imgs);
    fs.writeFileSync(fname, content);
    var dir = path.dirname(fname)
    for(var [fname, img] of imgs.entries()) {
        fs.writeFileSync(path.join(dir, 'img', fname), img)
    }
}

function httpGetRetry(url, n=config.n_retry) {

    for(var i = 0; i < n; i++) {
        try {
            return request('GET', url, {headers: config.hdrs})
        } catch(ex) {
            if(i == n - 1) throw ex;
        }
    }
}

function processImg(html, imgs, options={}) {
    
    options.imgPrefix = options.imgPrefix || 'img/'
    
    var $ = cheerio.load(html);
    
    var $imgs = $('img');

    for(var i = 0; i < $imgs.length; i++) {
        
        try {
            var $img = $imgs.eq(i);
            var url = $img.attr('src');
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
                var data = httpGetRetry(url).getBody();
                data = betterImg(data)
                imgs.set(picname, data);
            }
            
            $img.attr('src', options.imgPrefix + picname);
        } catch(ex) {console.log(ex.toString())}
    }
    
    return $.html();

}

module.exports = processImg

if(module == require.main) main();
