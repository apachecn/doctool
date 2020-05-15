// my conventors for https://github.com/domchristie/to-markdown

'use strict';

function cell(content, node) {
  var index = Array.prototype.indexOf.call(node.parentNode.childNodes, node);
  var prefix = ' ';
  if (index === 0) { prefix = '| '; }
  return prefix + content + ' |';
}

module.exports = [

  //<p> in <td>
  {
    filter: function(n) {
        return n.nodeName == 'P' &&
            n.parentNode.nodeName === 'TD'
    },
    replacement: function(c){return c}
  },

  //<dl> (to <p>)
  {
    filter: ['dd', 'dt'],
    replacement: function (c) {
      return '\n\n' + c + '\n\n';
    }
  },
  
  {
      filter: 'dl',
      replacement: function(c){return c}
  },
  
  // <em> & <i>
  
  {
      filter: ['em', 'i'],
      replacement: function(c){return '*' + c + '*'}
  },
  
  //<span> & <div>
  
  {
    filter: ['span', 'div'],
    replacement: function(c){return c}
  },
  
  //sth to clean
  {
    filter: ['style', 'base', 'meta', 'script'],
    replacement: function(){return ''}
  },
  
  // <code>
  {
    filter: ['code', 'tt', 'var', 'kbd'],
    replacement: function(c, n) {
      if(n.parentNode.nodeName !== 'PRE')
        return '`' + c + '`';
      else
        return c;
    }
  },
  
  //non-link <a>
  {
    filter: function (n) {
      return n.nodeName === 'A' && !n.getAttribute('href');
    },
    replacement: function(){return ''}
  },
  
  // <pre>
  {
    filter: 'pre',
    replacement: function(c) {
        return '\n\n```\n' + c + '\n```\n\n';
    }
  },
  
  // tags in <pre>
  {
    filter: function(n) {
        return n.parentNode.nodeName === 'PRE' &&
            n.nodeName != 'BR'
    },
    replacement: function(c){return c}
  },
  
  //<th> & <td>
  {
    filter: ['th', 'td'],
    replacement: function (c, n) {
      return cell(c.replace(/\|/g, '&#124;'), n);
    }
  },
];
