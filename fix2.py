with open("project/index.html", "r") as f:
    html = f.read()

letter_content = """Gửi người con gái anh yêu,

Nhân ngày Quốc tế Phụ nữ 8/3, anh muốn gửi đến em những lời chúc ngọt ngào nhất. Chúc em luôn xinh đẹp, rạng rỡ như những đóa hoa và luôn tràn ngập hạnh phúc bên anh.

Cảm ơn em đã luôn đồng hành và mang lại hơi ấm cho trái tim anh. Anh yêu em rất nhiều!

Chúc em một ngày 8/3 thật ý nghĩa và tràn đầy niềm vui. Mong rằng mỗi ngày trôi qua, nụ cười luôn nở trên môi em.

Mãi yêu em ❤️"""

import re

# Thay thế loadLetter()
html = re.sub(
    r'async function loadLetter\(\) \{[\s\S]*?\}',
    f'''async function loadLetter() {{
  const letterBody = document.getElementById("letter-body");
  const text = `{letter_content}`;
  letterBody.innerHTML = "";
  let i = 0;
  function typeWriter() {{
    if (i < text.length) {{
      if (text.charAt(i) === "\\n") {{
        letterBody.innerHTML += "<br>";
      }} else {{
        letterBody.innerHTML += text.charAt(i);
      }}
      i++;
      setTimeout(typeWriter, 50);
    }}
  }}
  typeWriter();
}}''',
    html
)

# Thay thế loadMessages()
html = re.sub(
    r'async function loadMessages\(\) \{[\s\S]*?\}',
    f'''async function loadMessages() {{
  window.messages = ["Mãi yêu em ❤️", "Chúc em 8/3 vui vẻ!", "Luôn xinh đẹp nhé!"];
}}''',
    html
)

with open("project/index.html", "w") as f:
    f.write(html)
