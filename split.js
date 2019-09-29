var fs = require('fs');
var process = require('process');

try {fs.mkdirSync('out');}
catch(ex){}

var co = fs.readFileSync(process.argv[2], 'utf-8');

var files = co.split(/<!\-\-split\-\->/g);

for(var i = 0; i < files.length; i++)
{
	fs.writeFileSync('out/' + i + '.html', files[i], {encoding: 'utf-8'});
}
