import re

with open("project/index.html", "r") as f:
    content = f.read()

# Fix the explosionIcon variable in createHearts
content = content.replace(
    'const icons = Array.from(explosionIcon).filter(char => char.trim() !== "");',
    'const icons = ["💖", "💝", "💗", "💓", "💞"]; // Fallback icons'
)

# Fix isGifting variable missing
content = content.replace(
    'if (isGifting) return;',
    'if (typeof isGifting !== "undefined" && isGifting) return;'
)

with open("project/index.html", "w") as f:
    f.write(content)
