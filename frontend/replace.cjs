const fs = require('fs');
const path = require('path');

function walk(dir) {
  let results = [];
  const list = fs.readdirSync(dir);
  list.forEach(file => {
    file = path.join(dir, file);
    const stat = fs.statSync(file);
    if (stat && stat.isDirectory()) {
      results = results.concat(walk(file));
    } else {
      if (file.endsWith('.vue') || file.endsWith('.scss')) {
        results.push(file);
      }
    }
  });
  return results;
}

const files = walk('src');
files.forEach(f => {
  let content = fs.readFileSync(f, 'utf8');
  let newContent = content
    .replace(/rgba\(\s*220\s*,\s*38\s*,\s*38/g, 'rgba(37, 99, 235')
    .replace(/rgba\(\s*216\s*,\s*74\s*,\s*74/g, 'rgba(37, 99, 235')
    .replace(/rgba\(\s*242\s*,\s*109\s*,\s*109/g, 'rgba(96, 165, 250')
    .replace(/rgba\(\s*185\s*,\s*46\s*,\s*53/g, 'rgba(96, 165, 250')
    .replace(/rgba\(\s*143\s*,\s*29\s*,\s*34/g, 'rgba(30, 64, 175');
  if (content !== newContent) {
    fs.writeFileSync(f, newContent);
    console.log('Updated ' + f);
  }
});
