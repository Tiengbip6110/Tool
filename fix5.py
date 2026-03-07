with open("project/index.html", "r") as f:
    html = f.read()

html = html.replace('''async function loadMessages() {
  window.messages = ["Mãi yêu em ❤️", "Chúc em 8/3 vui vẻ!", "Luôn xinh đẹp nhé!"];
} catch (error) {
                console.error("Error loading mess.txt:", error);
                // Fallback if file not found
                messages = ["Anh yêu em ❤️"];
        }
}''', '''async function loadMessages() {
  window.messages = ["Mãi yêu em ❤️", "Chúc em 8/3 vui vẻ!", "Luôn xinh đẹp nhé!"];
}''')

with open("project/index.html", "w") as f:
    f.write(html)
