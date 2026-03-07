import re

with open("project/index.html", "r") as f:
    content = f.read()

# Replace any lingering "explosionIcon is not defined" or similar issues
content = re.sub(r'const explosionIcon = explosionIcon\.cloneNode\(true\);', r'const explosion = document.createElement("div");\n                explosion.className = "explosion-icon";', content)

content = content.replace('document.body.appendChild(explosionIcon);', 'document.body.appendChild(explosion);')
content = content.replace('explosionIcon.remove();', 'explosion.remove();')
content = content.replace('explosionIcon.style.', 'explosion.style.')

with open("project/index.html", "w") as f:
    f.write(content)
