import re
with open("project/index.html", "r") as f:
    html = f.read()

# Replace the mangled section completely
start = html.find('async function loadLetter()')
end = html.find('async function loadMessages()')

if start != -1 and end != -1:
    before = html[:start]
    after = html[end:]
    middle = """async function loadLetter() {
  const letterBody = document.getElementById("letter-body");
  const text = `Gửi người con gái anh yêu,\\n\\nNhân ngày Quốc tế Phụ nữ 8/3, anh muốn gửi đến em những lời chúc ngọt ngào nhất. Chúc em luôn xinh đẹp, rạng rỡ như những đóa hoa và luôn tràn ngập hạnh phúc bên anh.\\n\\nCảm ơn em đã luôn đồng hành và mang lại hơi ấm cho trái tim anh. Anh yêu em rất nhiều!\\n\\nChúc em một ngày 8/3 thật ý nghĩa và tràn đầy niềm vui. Mong rằng mỗi ngày trôi qua, nụ cười luôn nở trên môi em.\\n\\nMãi yêu em ❤️`;
  letterBody.innerHTML = "";
  let i = 0;
  function typeWriter() {
    if (i < text.length) {
      if (text.charAt(i) === "\\n") {
        letterBody.innerHTML += "<br>";
      } else {
        letterBody.innerHTML += text.charAt(i);
      }
      i++;
      setTimeout(typeWriter, 50);
    }
  }
  typeWriter();
}

"""
    html = before + middle + after

with open("project/index.html", "w") as f:
    f.write(html)
