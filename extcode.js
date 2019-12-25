var fs = require('fs')
var path = require('path')

var isFile = f => fs.statSync(f).isFile()

function recoverFile(fname) {
    if(!fname.endsWith('.md'))
        return
    if(!fs.existsSync(fname + '.json')) {
        console.log(fname + ' 未提取')
        return
    }
    
    console.log(fname)
    var pres = JSON.parse(fs.readFileSync(fname + '.json', 'utf-8'))
    var co = fs.readFileSync(fname, 'utf-8')
    
    for(var [i, p] of pres.entries())
        co = co.replace(`[PRE${i}]`, p)
    
    fs.writeFileSync(fname, co)
    fs.unlinkSync(fname + '.json')
}

function extractFile(fname) {
    
    if(!fname.endsWith('.md'))
        return
    if(fs.existsSync(fname + '.json')) {
        console.log(fname + ' 已提取')
        return
    }
    
    console.log(fname)
    var co = fs.readFileSync(fname, 'utf-8')
    
    var pres = []
    co = co.replace(/```\w*$[\s\S]+?^```/mg, s => {
        pres.push(s)
        var idx = pres.length - 1
        return `[PRE${idx}]`
    })
    
    fs.writeFileSync(fname + '.json', JSON.stringify(pres))
    fs.writeFileSync(fname, co)
}

function processDir(dir, op) {
    var files = fs.readdirSync(dir)
    for(var f of files) op(path.join(dir, f))
}

var recoverDir = dir => processDir(dir, recoverFile)
var extractDir = dir => processDir(dir, extractFile)

function extract(fname) {
    
    if(isFile(fname))
        extractFile(fname)
    else
        extractDir(fname)
}

function recover(fname) {
    
    if(isFile(fname))
        recoverFile(fname)
    else
        recoverDir(fname)
}

function main() {
    
    var op = process.argv[2]
    var fname = process.argv[3]
    if(['e', 'extract'].includes(op))
        extract(fname)
    else if(['r', 'recover'].includes(op))
        recover(fname)
}

if(require.main === module) main()
