import re

with open("project/index.html", "r") as f:
    content = f.read()

content = content.replace('const sound = popSound.cloneNode(true);', 'const sound = giftPopSoundEl.cloneNode(true);')
content = content.replace('const explosionIcon = explosionIcon.cloneNode(true);', 'const expIcon = document.createElement("div");\n                expIcon.className = "explosion-icon";\n                // Using empty as we do not have explosionIcon defined properly here unless we redefine it.')

content = re.sub(r'const explosionIcon = explosionIcon\.cloneNode\(true\);', r'const explosion = document.createElement("div");\n                explosion.className = "explosion-icon";', content)

with open("project/index.html", "w") as f:
    f.write(content)
