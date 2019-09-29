var fs = require('fs');
var path = require('path');
var process = require('process');

function safeMkdir(p) {
    try {fs.mkdirSync(p);}
    catch(ex){}
}

function getWidth(i) {
    return i == 0? 1: Math.trunc(Math.log10(i)) + 1
}

var fname = process.argv[2]
var dir = path.dirname(fname)
safeMkdir(path.join(dir, 'out'))
var co = fs.readFileSync(fname, 'utf-8');
var cos = co.split(/<!\-\-split\-\->/g);
var maxWid = getWidth(cos.length - 1)

for(var [i, co] of cos.entries())
{
    var fname = i.toString().padStart(maxWid, '0') + '.html'
    fs.writeFileSync(path.join(dir, 'out', fname), cos[i]);
}
