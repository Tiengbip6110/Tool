import re

def process_css():
    with open('project/style1.css', 'r') as f:
        css1 = f.read()

    with open('project/style2.css', 'r') as f:
        css2 = f.read()

    # Dọn dẹp css2: Xóa định dạng chung body/html có thể làm hỏng giao diện
    css2 = re.sub(r'html,\s*body\s*\{[^}]+\}', '', css2)
    css2 = re.sub(r'\*\s*\{[^}]+\}', '', css2)
    # Tinh chỉnh lại CSS cho container phần hoa để nó không chiếm toàn màn hình trang chính
    css2 = css2.replace('.night {', '.gift-main-content .night {')
    css2 = css2.replace('.flowers {', '.gift-main-content .flowers {')

    # Chúng ta sẽ cần wrap style của gift lại, nhưng chỉ các rule chính
    # Vì quá dài nên tôi sẽ ghi ra gộp cả 2.

    merged = f"/* --- MAIN CSS --- */\n{css1}\n\n/* --- GIFT CSS --- */\n{css2}\n"

    # Custom CSS cho việc tích hợp
    custom_css = """
/* --- INTEGRATION CSS --- */
.gift-integrated-container {
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
  border-radius: inherit;
}
.gift-main-content {
  width: 100%;
  height: 100%;
  position: absolute;
  top: 0;
  left: 0;
  overflow: hidden;
  background-color: #000;
}
.gift-main-content.hidden {
  display: none;
}
.intro-overlay {
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  background: #000;
  display: flex; justify-content: center; align-items: center;
  z-index: 100;
  transition: opacity 1s ease;
}
.intro-overlay.fade-out {
  opacity: 0;
  pointer-events: none;
}
.floating-gift {
  width: 250px;
  animation: floatGift 3s ease-in-out infinite;
  cursor: pointer;
}
.open-text {
  color: white; margin-top: 20px; text-align: center;
  font-size: 24px; font-family: 'Segoe UI', sans-serif;
  animation: pulseText 1.5s infinite;
}
@keyframes floatGift {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-30px); }
}
@keyframes pulseText {
  0%, 100% { opacity: 0.8; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.1); }
}
.gift-main-content .night {
  position: absolute; top: 0; left: 0; width: 100%; height: 100%;
}
"""

    with open('project/all_style.css', 'w') as f:
        f.write(merged + custom_css)

process_css()
