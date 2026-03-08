const fs = require('fs');
const https = require('https');

const download = (url, dest) => {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(dest);
    https.get(url, (response) => {
      response.pipe(file);
      file.on('finish', () => {
        file.close(resolve);
      });
    }).on('error', (err) => {
      fs.unlink(dest, () => {});
      reject(err);
    });
  });
};

const run = async () => {
  try {
    await download('https://dr-gifter.onrender.com/assets/index-CB81GR8f.js', 'dr-gifter/index.js');
    await download('https://dr-gifter.onrender.com/assets/index-6K-OT-IY.css', 'dr-gifter/index.css');
    console.log('Downloaded assets');
  } catch (err) {
    console.error('Failed to download assets', err);
  }
};

run();
