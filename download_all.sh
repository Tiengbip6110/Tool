mkdir -p project
cd project

curl -s https://gift-surprise-v2.vercel.app/ -o index.html
curl -s https://gift-surprise-v2.vercel.app/style/style.css -o style.css
curl -s https://gift-surprise-v2.vercel.app/style/script.js -o script.js
curl -s https://gift-surprise-v2.vercel.app/style/gift/gift.html -o gift.html
curl -s https://gift-surprise-v2.vercel.app/style/gift/style/style.css -o gift_style.css
curl -s https://gift-surprise-v2.vercel.app/style/gift/style/script.js -o gift_script.js
curl -s https://gift-surprise-v2.vercel.app/style/letter.txt -o letter.txt
