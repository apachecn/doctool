var toMD = require('to-markdown');
var fs = require('fs');
var myConventors = require('./my-conventors');
var path = require('path')

var isDir = s => fs.statSync(s).isDirectory()

function main() {
    
    var fname = process.argv[2]
    if(!fname) {
        console.log('请指定文件或目录。')
        process.exit();
    }
    
    if(isDir(fname))
        processDir(fname)
    else
        processFile(fname)
}

function processDir(dir) {
    var files = fs.readdirSync(dir)
    for(var fname of files) {
        fname = path.join(dir, fname)
        processFile(fname)
    }
}

function processFile(fname) {
    if(!fname.endsWith('.html')) 
        return;
    console.log(`file: ${fname}`)
    var co = fs.readFileSync(fname, 'utf-8');
    var mdName = fname.replace(/\.html/g, '.md')
    var md = toMD(co, {
        gfm: true,
        converters: myConventors,
    });
    fs.writeFileSync(mdName, md);
}

if(module == require.main) main()