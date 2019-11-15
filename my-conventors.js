// my conventors for https://github.com/domchristie/to-markdown

'use strict';

function esc(s)
{
    return s.replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
}

function escForTable(s)
{
    return s.replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/\|/g, '&#124;');
}

function cell(content, node) {
  var index = Array.prototype.indexOf.call(node.parentNode.childNodes, node);
  var prefix = ' ';
  if (index === 0) { prefix = '| '; }
  return prefix + content + ' |';
}

var highlightRegEx = /highlight highlight-(\S+)/;

module.exports = [

  //paragraph
  {
    filter: 'p',
    replacement: function (content, node) {
      if(node.parentNode.nodeName === 'TD')
          return esc(content);
      else
        return '\n\n' + esc(content) + '\n\n';
    }
  },

  //dl (to paragraph)
  {
    filter: ['dd', 'dt'],
    replacement: function (content) {
      return '\n\n' + esc(content) + '\n\n';
    }
  },
  
  {
      filter: 'dl',
      replacement: function(c){return c;}
  },
  
  //span & div
  
  {
    filter: ['span', 'div'],
    replacement: function(c){return c;}
  },
  
  //sth to clean
  {
    filter: ['style', 'base', 'meta', 'script'],
    replacement: function(c){return '';}
  },

  //title
  {
    filter: ['h1', 'h2', 'h3', 'h4','h5', 'h6'],
    replacement: function(content, node) {
      var hLevel = node.nodeName.charAt(1);
      var hPrefix = '';
      for(var i = 0; i < hLevel; i++) {
        hPrefix += '#';
      }
      return '\n\n' + hPrefix + ' ' + esc(content) + '\n\n';
    }
  },

  //quote
  {
    filter: 'blockquote',
    replacement: function (content) {
      content = esc(content).trim();
      content = content.replace(/\n{3,}/g, '\n\n');
      content = content.replace(/^/gm, '> ');
      return '\n\n' + content + '\n\n';
    }
  },

  //list
  {
    filter: 'li',
    replacement: function (content, node) {
      content = content.replace(/^\s+/, '').replace(/\n/gm, '\n    ');
      var prefix = '*   ';
      var parent = node.parentNode;
      var index = Array.prototype.indexOf.call(parent.children, node) + 1;

      prefix = /ol/i.test(parent.nodeName) ? index + '.  ' : '*   ';
      return prefix + esc(content);
    }
  },
  
  // Inline code
  {
    filter: function (node) {
      return ['CODE', 'TT', 'VAR'].indexOf(node.nodeName) != -1;
    },
    replacement: function(content, node) {
      if(node.parentNode.nodeName !== 'PRE')
        return '`' + content + '`';
      else
        return content;
    }
  },
  
  //non-link anchor
  {
    filter: function (node) {
      return node.nodeName === 'A' && !node.getAttribute('href');
    },
    replacement: function(content) { return content; }
  },
  
  // Fenced code blocks
  {
    filter: 'pre',
    replacement: function(c, n) {
        var lang = '';
        if(n.parentNode.nodeName === 'DIV' &&
           highlightRegEx.test(n.parentNode.className))
           lang = n.parentNode.className.match(highlightRegEx)[1];
        
        return '\n\n```' + lang + '\n' + c + '\n```\n\n';
    }
  },
  
  {
    filter: function(n) {
        return n.parentNode.nodeName === 'PRE';
    },
    replacement: function(c){return c;}
  },
  
  //table 
  {
    filter: ['th', 'td'],
    replacement: function (content, node) {
      return cell(escForTable(content), node);
    }
  },
  
  {
    filter: 'tr',
    replacement: function (content, node) {
      var borderCells = '';
      var alignMap = { left: ':--', right: '--:', center: ':-:' };

      if (node.childNodes[0].nodeName === 'TH') {
        for (var i = 0; i < node.childNodes.length; i++) {
          var align = node.childNodes[i].attributes.align;
          var border = '---';

          if (align) { border = alignMap[align.value] || border; }

          borderCells += cell(border, node.childNodes[i]);
        }
      }
      return '\n' + content + (borderCells ? '\n' + borderCells : '');
    }
  }
];
