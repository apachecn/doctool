/*
apt install imagemagick
apt install pngquant
*/

var chp = require('child_process')
var fs = require('fs')
var path = require('path')
var os = require('os')

function betterImg(img, tmpDir) {
    
    tmpDir = tmpDir || os.tmpdir()
    var fname = new Date().getTime().toString() + '.png'
    fname = path.join(tmpDir, fname)
    fs.writeFileSync(fname, img)
    chp.spawnSync('convert', [fname, fname])
    chp.spawnSync('pngquant', ['4', fname, '-o', fname, '-f'])
    img = fs.readFileSync(fname)
    safeUnlink(fname)
    return img
}

module.exports = betterImg

function safeUnlink(f){
    
    try {fs.unlinkSync(f)}
    catch(ex) {}
}

function main() {

    var dir = process.argv[2]
    var qualify = process.argv[3] || '8'
    var pics = fs.readdirSync(dir).filter(
        x => x.endsWith('.jpg') || 
             x.endsWith('.png') || 
             x.endsWith('.gif') || 
             x.endsWith('.jpeg')
    )

    for(var f of pics){
        
        f = path.join(dir, f)
        console.log(f)
        var img = fs.readFileSync(f)
        img = betterImg(img)
        fs.writeFileSync(f, img)
    }

}

if(module == require.main) main()
