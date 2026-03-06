import re

with open('project/script.js', 'r') as f:
    js_content = f.read()

# Replace the original image array generator
js_content = re.sub(
    r'const imageFiles = Array\.from\(\s*\{\s*length:\s*20\s*\},.*?\);\s*',
    '// Replaced with embedded images\nconst imageFiles = userImages;\n',
    js_content,
    flags=re.DOTALL
)

# Pick a random image for the lock screen on page load
# We need to add JS that dynamically sets the src of the .lock-image img tag.
lock_screen_js = """
document.addEventListener("DOMContentLoaded", () => {
    const lockImg = document.querySelector(".lock-image img");
    if (lockImg && typeof userImages !== 'undefined' && userImages.length > 0) {
        const randomIndex = Math.floor(Math.random() * userImages.length);
        lockImg.src = userImages[randomIndex];
    }
});
"""

js_content = lock_screen_js + "\n" + js_content

with open('project/script.js', 'w') as f:
    f.write(js_content)

print("Modified script.js to use embedded images and set random lock screen image.")
