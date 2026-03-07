with open("project/index.html", "r") as f:
    html = f.read()

# Look for syntax errors. I used multiline string with template literal, maybe quotes broke it.
html = html.replace("const text = `Gửi người con gái anh yêu,", "const text = `Gửi người con gái anh yêu,\\n\\nNhân ngày Quốc tế Phụ nữ 8/3, anh muốn gửi đến em những lời chúc ngọt ngào nhất. Chúc em luôn xinh đẹp, rạng rỡ như những đóa hoa và luôn tràn ngập hạnh phúc bên anh.\\n\\nCảm ơn em đã luôn đồng hành và mang lại hơi ấm cho trái tim anh. Anh yêu em rất nhiều!\\n\\nChúc em một ngày 8/3 thật ý nghĩa và tràn đầy niềm vui. Mong rằng mỗi ngày trôi qua, nụ cười luôn nở trên môi em.\\n\\nMãi yêu em ❤️`;\n//")

with open("project/index.html", "w") as f:
    f.write(html)
