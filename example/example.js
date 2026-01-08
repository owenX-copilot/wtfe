// CommonJS style
const fs = require('fs');

function helper(name) {
  return `Hello, ${name}`;
}

if (typeof module !== 'undefined') {
  module.exports = { helper };
}
