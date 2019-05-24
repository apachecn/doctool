var fs = require('fs')
var path = require('path')

function fmtZh(text) {
    return text.replace(/([\u4e00-\u9fff])(\w)/g, '$1 $2')
               .replace(/(\w)([\u4e00-\u9fff])/g, '$1 $2')
}

function processFile(fname) {
    console.log(`file: ${fname}`)
    var co = fs.readFileSync(fname, 'utf-8')
    co = fmtZh(co)
    fs.writeFileSync(fname, co)
}

function processDir(dir) {
    var files = fs.readdirSync(dir)
    
    for (var fname of files) {
        fname = path.join(dir, fname)
        if(!fs.statSync(fname).isFile())
            continue
        processFile(fname)
    }
}

function main() {
    
    var fname = process.argv[2]
    if(!fname) {
        console.log('请提供文件或目录。')
        process.exit()
    }
    
    if(fs.statSync(fname).isDirectory())
        processDir(fname)
    else
        processFile(fname)
}

if(module == require.main) main()