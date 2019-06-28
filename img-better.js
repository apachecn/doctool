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
    var fname = new Date().getTime().toString() + '.jpg'
    fname = path.join(tmpDir, fname)
    fs.writeFileSync(fname, img)
    fnamePng = fname.slice(0, -4) + '-conv.png'
    fnameFs8 = fnamePng.slice(0, -4) + '-comp.png'
    chp.spawnSync('magick', ['convert', fname, fnamePng])
    chp.spawnSync('pngquant', ['8', fnamePng, '-o', fnameFs8])
    if(fs.existsSync(fnameFs8)) {
        img = fs.readFileSync(fnameFs8)
        safeUnlink(fnameFs8)
    }
    safeUnlink(fnamePng)
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
             x.endsWith('.gif')
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
