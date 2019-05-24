var fs = require('fs')
var path = require('path')

var dir = process.argv[2]
var files = fs.readdirSync(dir).filter(x => x.endsWith('.md'))

var res = []
for(var f of files) {
    full_f = path.join(dir, f)
    console.log(full_f)
    var co = fs.readFileSync(full_f, 'utf-8')
    var re = /^#+ (.+?)$/m
    var rm = re.exec(co)
    if(!rm) continue;
    var title = rm[1];
    res.push(`+   [${title}](${f})`)
}

var summary = res.join('\n')
fs.writeFileSync(path.join(dir, 'SUMMARY.md'), summary)
