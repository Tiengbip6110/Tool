import re

def process_js():
    with open('project/script1.js', 'r') as f:
        js1 = f.read()

    with open('project/script2.js', 'r') as f:
        js2 = f.read()

    # JS1: Sửa mã PIN thành 3310
    js1 = js1.replace('const correctPin = "0803";', 'const correctPin = "3310";')

    # JS1: Thay đổi ảnh tạm cho songs và thư viện
    js1 = js1.replace('"style/sound/Anh (1).jpg"', '"https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=100"')
    js1 = js1.replace('"style/sound/Anh (2).jpg"', '"https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=100"')
    js1 = js1.replace('"style/sound/Anh (3).jpg"', '"https://images.unsplash.com/photo-1493225457124-a1a2a4f0a4f4?w=100"')
    js1 = js1.replace('"style/sound/Anh (4).jpg"', '"https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=100"')
    js1 = js1.replace('"style/sound/Anh (5).jpg"', '"https://images.unsplash.com/photo-1459749411175-04bf5292ceea?w=100"')
    js1 = js1.replace('"style/sound/Anh (6).jpg"', '"https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=100"')

    # URL nhạc (lấy từ bản gốc)
    js1 = js1.replace('"style/sound/In Love x Có Đôi Điều.mp3"', '"https://gift-surprise-v2.vercel.app/style/sound/In%20Love%20x%20C%C3%B3%20%C4%90%C3%B4i%20%C4%90i%E1%BB%81u.mp3"')
    js1 = js1.replace('"style/sound/Ai Ngoài Anh.mp3"', '"https://gift-surprise-v2.vercel.app/style/sound/Ai%20Ngo%C3%A0i%20Anh.mp3"')
    js1 = js1.replace('"style/sound/Track 06 x Nơi Này Có Anh.mp3"', '"https://gift-surprise-v2.vercel.app/style/sound/Track%2006%20x%20N%C6%A1i%20N%C3%A0y%20C%C3%B3%20Anh.mp3"')
    js1 = js1.replace('"style/sound/Lỡ Say Bye Là Bye.mp3"', '"https://gift-surprise-v2.vercel.app/style/sound/L%E1%BB%A1%20Say%20Bye%20L%C3%A0%20Bye.mp3"')
    js1 = js1.replace('"style/sound/MISSING YOU.mp3"', '"https://gift-surprise-v2.vercel.app/style/sound/MISSING%20YOU.mp3"')
    js1 = js1.replace('"style/sound/Anh là ai.mp3"', '"https://gift-surprise-v2.vercel.app/style/sound/Anh%20l%C3%A0%20ai.mp3"')

    # js1: Sửa logic mở gift
    js1 = re.sub(
        r'btnGift\.addEventListener\("click", \(\) => \{\n  if \(giftIframe\).*?\n  \}\n  giftOverlay\.classList\.add\("active"\);\n\}\);',
        'btnGift.addEventListener("click", () => {\n  giftOverlay.classList.add("active");\n});',
        js1, flags=re.DOTALL
    )

    # js1: Thư viện ảnh (imageFiles)
    js1 = re.sub(
        r'const imageFiles = \[.*?\];',
        'const imageFiles = [' + ','.join(['"https://images.unsplash.com/photo-1682687220742-aba13b6e50ba?w=300"'] * 18) + '];',
        js1, flags=re.DOTALL
    )

    # js2: Logic mở hộp quà (intro => main)
    js2_integration = """
// --- GIFT INTEGRATION LOGIC ---
const introOverlay = document.getElementById("introOverlay");
const giftMainContent = document.getElementById("giftMainContent");

introOverlay.addEventListener("click", () => {
    introOverlay.classList.add("fade-out");
    setTimeout(() => {
        giftMainContent.classList.remove("hidden");
        // Gọi hàm của gift.js để render falling images (nếu cần, nhưng script2 tự render)
        if(typeof startFallingAnimations === "function") startFallingAnimations();
    }, 1000); // Đợi animation mờ dần kết thúc
});
"""

    # Cắt gọn script2 để không tự động chạy event load (vì popup không phải page load)
    js2 = re.sub(r'onload = \(\) => \{\n  const c = setTimeout\(\(\) => \{\n    document\.body\.classList\.remove\("not-loaded"\);\n    clearTimeout\(c\);\n  \}, 1000\);\n\};', '', js2)
    # Loại bỏ code menu trong js2 (do ta đã ở trong modal)
    js2 = re.sub(r'const menuTrigger = document.getElementById\("menuTrigger"\);.*?if\(!menuContainer.contains\(e.target\)\).*?\}', '', js2, flags=re.DOTALL)

    with open('project/all_script.js', 'w') as f:
        f.write(js1 + "\n\n" + js2_integration + "\n\n" + js2)

process_js()
