const path = require('path')
const fs = require('fs')
const request = require('sync-request')

const RE = /\/\/unpkg\.com(?:\/[\w\-\.]+)+/g

function main() {
    
    var dir = process.argv[2]
    var hpg = path.join(dir, 'index.html')
    if(!fs.existsSync(hpg)) {
        console.log('no homepage')
        return
    }
    
    var co = fs.readFileSync(hpg, 'utf-8')
    
    var assetDir = path.join(dir, 'asset')
    try { fs.mkdirSync(assetDir)} catch {}
    
    var co = processHtml(co, assetDir, 'asset/')
    fs.writeFileSync(hpg, co)
    console.log('done')
}

function processHtml(html, assetDir, prefix) {
    var res = html
    var rm
    while(rm = RE.exec(html)) {
        var url = 'https:' + rm[0]
        console.log(url)
        var co = request('GET', url).body.toString()
        var fname = url.split('/').slice(-1)[0]
        fs.writeFileSync(path.join(assetDir, fname), co)
        res = res.split(rm[0]).join(prefix + fname)
    }
    return res
}

if(require.main === module) main()
