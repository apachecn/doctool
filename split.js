var fs = require('fs');

try {fs.mkdirSync('out');}
catch(ex){}

var co = fs.readFileSync('out.html', 'utf-8');

var files = co.split(/<!\-\-split\-\->/g);

for(var i = 0; i < files.length; i++)
{
	fs.writeFileSync('out/' + i + '.html', files[i], {encoding: 'utf-8'});
}
