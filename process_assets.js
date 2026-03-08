const fs = require('fs');

let css = fs.readFileSync('dr-gifter/index.css', 'utf8');
let js = fs.readFileSync('dr-gifter/index.js', 'utf8');

// Replace URLs in CSS
// For example: url(/assets/font.woff2) -> url(https://dr-gifter.onrender.com/assets/font.woff2)
css = css.replace(/url\(\s*['"]?(\/assets\/[^)'"]+)['"]?\s*\)/g, 'url(https://dr-gifter.onrender.com$1)');

// Replace imports or paths in JS
// Since it's a Vite build, it might have things like __vitePreload(()=>import("/assets/chunk.js"),true?__vite__mapDeps([]):void 0)
// We will replace "/assets/" with "https://dr-gifter.onrender.com/assets/" inside strings
// It's safer to just replace all occurrences of "/assets/" and similar paths where they are literal strings.
// But let's check first if there are any.
const matches = js.match(/(["'])\/assets\/[^"']+\1/g);
console.log('Matches in JS:', matches);

js = js.replace(/(["'])\/assets\/([^"']+)\1/g, '$1https://dr-gifter.onrender.com/assets/$2$1');

fs.writeFileSync('dr-gifter/index.css', css);
fs.writeFileSync('dr-gifter/index.js', js);
console.log('Processed assets');
