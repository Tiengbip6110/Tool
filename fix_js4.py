import re

with open("project/index.html", "r") as f:
    content = f.read()

content = content.replace(
    'if (!isGifting) return;',
    'if (typeof isGifting === "undefined" || !isGifting) return;'
)

with open("project/index.html", "w") as f:
    f.write(content)
