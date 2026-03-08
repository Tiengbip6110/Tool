const fs = require('fs');

const css = fs.readFileSync('dr-gifter/index.css', 'utf8');
const js = fs.readFileSync('dr-gifter/index.js', 'utf8');

let html = `<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <link rel="icon" type="image/svg+xml" href="https://dr-gifter.onrender.com/assets/favicon-BFQtF5JZ.ico" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css" />
  <title>Dr.Gifter</title>
  <!-- Social Media Meta Tags -->
  <meta property="og:title" content="Dr.Gifter" />
  <meta property="og:description" content="Khám phá ngay thế giới quà tặng tại Dr.Gifter!" />
  <meta property="og:image" content="https://i.postimg.cc/15Lq1J1d/drgifter.png" />
  <meta property="og:url" content="https://dr-gifter.onrender.com/" />
  <meta property="og:type" content="website" />

  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="Dr.Gifter" />
  <meta name="twitter:description" content="Khám phá ngay thế giới quà tặng tại Dr.Gifter!" />
  <meta name="twitter:image" content="https://i.postimg.cc/15Lq1J1d/drgifter.png" />
  <script>
    (function () {
      const theme = localStorage.getItem('theme') || 'light';
      document.documentElement.setAttribute('data-theme', theme);

      // Fix for React Router SPA when loading from local file or unexpected path
      if (window.location.pathname !== '/code' && window.location.pathname !== '/') {
        window.history.replaceState(null, '', '/code');
      }
    })();
  </script>
  <style>
${css}
  </style>
</head>
<body>
  <div id="root"></div>
  <script type="module">
${js}
  </script>
</body>
</html>`;

fs.writeFileSync('crack1.html', html);
console.log('Combined into crack1.html');
const stats = fs.statSync('crack1.html');
console.log(`File size: ${stats.size} bytes`);
