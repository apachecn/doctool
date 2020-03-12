var fs = require('fs')
var crypto = require('crypto')
var request = require('sync-request')
var path = require('path')

function processTex(html, isMD=false) {
    
    var rm;
    while(rm = /\\\((.+?)\\\)|\\\[([\s\S]+?)\\\]|\$\$?([\s\S]+?)\$\$?/g.exec(html)){
        var tex = rm[1] || rm[2] || rm[3]
        var encoTex = encodeURIComponent(tex)
            .replace(/\(/g, '%28')
            .replace(/\)/g, '%29')
        
        var url = 'https://www.zhihu.com/equation?tex=' + encoTex
        
        // replace_all
        if(isMD)
            html = html.split(rm[0]).join(`![${encoTex}](${url})`)
        else
            html = html.split(rm[0]).join(`<img alt='${encoTex}' src='${url}' />`)

    }
    
    return html
    
}

function processFile(fname) {
    
    if(!fname.endsWith('.html') && !fname.endsWith('.md'))
        return
    console.log(fname)
    var co = fs.readFileSync(fname, 'utf-8')
    co = processTex(co, fname.endsWith('.md'))
    fs.writeFileSync(fname, co)
}

function processDir(docDir) {
    var flist = fs.readdirSync(docDir)
        .filter(s => s.endsWith('.html') || s.endsWith('.md'))

    for(var fname of flist) {
        fname = path.join(docDir, fname)
        processFile(fname)
    }

}

function main() {

    var fname = process.argv[2]
    
    if(fs.statSync(fname).isDirectory())
        processDir(fname)
    else
        processFile(fname)
    console.log('done')

}

main()
