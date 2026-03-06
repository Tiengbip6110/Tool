with open("Projects C01.1 (8th3.html)", "r", encoding="utf-8") as f:
    content = f.read()

# Fix the script to properly wait for DOM to load before setting lock image
# Re-inject the lock image randomizer script. The previous one might have failed or executed too early.
# Find the exact place where userImages is defined
content = content.replace("document.addEventListener(\"DOMContentLoaded\", () => {\n    const lockImg = document.querySelector(\".lock-image img\");\n    if (lockImg && typeof userImages !== 'undefined' && userImages.length > 0) {\n        const randomIndex = Math.floor(Math.random() * userImages.length);\n        lockImg.src = userImages[randomIndex];\n    }\n});", "")

script_injection = """
document.addEventListener("DOMContentLoaded", () => {
    const lockImg = document.querySelector(".lock-image img");
    if (lockImg && typeof userImages !== 'undefined' && userImages.length > 0) {
        const randomIndex = Math.floor(Math.random() * userImages.length);
        lockImg.src = userImages[randomIndex];
    }
});
"""

content = content.replace("const userImages =", script_injection + "\nconst userImages =")

# Also fix Font Awesome cross-origin error just in case
content = content.replace('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css" />', '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css" crossorigin="anonymous" referrerpolicy="no-referrer" />')

with open("Projects C01.1 (8th3.html)", "w", encoding="utf-8") as f:
    f.write(content)
