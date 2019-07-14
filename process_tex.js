var fs = require('fs')
var crypto = require('crypto')
var request = require('sync-request')
var path = require('path')

var imgRelDir = 'img'

function processTex(html, imgDir, isMD=false) {
    
    var rm;
    while(rm = /\\\((.+?)\\\)|\\\[([\s\S]+?)\\\]/g.exec(html)){
        var tex = rm[1] || rm[2]

        var url = 'http://latex.codecogs.com/gif.latex?'
            + encodeURIComponent(tex)
        var tex_md5 = crypto.createHash("md5").update(tex).digest('hex')
        var img = request('get', url).getBody()
        
        // replace_all
        if(isMD)
            html = html.split(rm[0]).join(`![${tex}](${imgRelDir}/tex-${tex_md5}.gif)`)
        else
            html = html.split(rm[0]).join(`<img src='${imgRelDir}/tex-${tex_md5}.gif' />`)
        fs.writeFileSync(`${imgDir}/tex-${tex_md5}.gif`, img)
        
        console.log(tex_md5)
    }
    
    return html
    
}

function processFile(fname, imgDir) {
    
    if(!fname.endsWith('.html') && !fname.endsWith('.md'))
        return
    console.log(fname)
    var co = fs.readFileSync(fname, 'utf-8')
    co = processTex(co, imgDir, fname.endsWith('.md'))
    fs.writeFileSync(fname, co)
}

function processDir(docDir, imgDir) {
    var flist = fs.readdirSync(docDir)
        .filter(s => s.endsWith('.html') || s.endsWith('.md'))

    for(var fname of flist) {
        fname = path.join(docDir, fname)
        processFile(fname, imgDir)
    }

}

function main() {

    var docDir = process.argv[2]
    var imgDir = path.join(docDir, imgRelDir)

    try { fs.mkdirSync(imgDir) }
    catch(e) {}
    processDir(docDir, imgDir)

    console.log('done')

}

main()
