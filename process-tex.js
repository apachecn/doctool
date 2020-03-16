var fs = require('fs')
var crypto = require('crypto')
var request = require('sync-request')
var path = require('path')

function processTex(html, isMD=false) {
    
    var re = /\\\((.+?)\\\)|\\\[([\s\S]+?)\\\]|\$(.+?)\$|\$\$([\s\S]+?)\$\$/g
    var rm;
    while(rm = re.exec(html)){
        var tex = rm[1] || rm[2] || rm[3] || rm[4]
        tex = tex.replace(/&#x\d+;/g, s => {
            var code = s.slice(3, -1)
            return String.fromCharCode(Number.parseInt(code, 16))
        }).replace(/&lt;/g, '<')
          .replace(/&gt;/g, '>')
          .replace(/&quot;/g, '"')
          .replace(/&apos;/g, "'")
          .replace(/&amp;/g, '&')
          .replace(/&nbsp;/g, ' ')
          
        var encoTex = encodeURIComponent(tex)
            .replace(/\(/g, '%28')
            .replace(/\)/g, '%29')
            .replace(/"/g, '%22')
        
        var url = 'https://www.zhihu.com/equation?tex=' + encoTex
        
        // replace_all
        if(isMD)
            html = html.split(rm[0]).join(`![${encoTex}](${url})`)
        else
            html = html.split(rm[0]).join(`<img alt="${encoTex}" src="${url}" />`)

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
