var fs = require('fs');

var fname = process.argv[2] || 'out.html'
if(!fname.endsWith('.html')) {
    console.log('请提供 HTML')
    process.exit()
}
var dir = fname.replace(/\.html$/, '')

try {fs.mkdirSync(dir);}
catch(ex){}

var co = fs.readFileSync(fname, 'utf-8');

var files = co.split(/<!\-\-split\-\->/g);

for(var i = 0; i < files.length; i++)
{
	fs.writeFileSync(`${dir}/${i}.html`, files[i], {encoding: 'utf-8'});
}