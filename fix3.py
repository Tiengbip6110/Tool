import base64
import glob
import re

html_file = '8th3.html'
with open(html_file, 'r', encoding='utf-8') as f:
    html_content = f.read()

# Use compressed images
image_files = glob.glob('/tmp/compressed_images/*.jpg')
image_files.sort()

base64_images = []
for file in image_files:
    with open(file, 'rb') as img_f:
        encoded = base64.b64encode(img_f.read()).decode('utf-8')
        base64_images.append(f'"data:image/jpeg;base64,{encoded}"')

# We need 20 images. Duplicate the 15 images to reach 20.
extended_images = base64_images.copy()
while len(extended_images) < 20:
    extended_images.append(base64_images[len(extended_images) % len(base64_images)])

images_js_array = "[\n  " + ",\n  ".join(extended_images) + "\n]"

html_content = re.sub(
    r'const imageFiles\s*=\s*Array\.from\([\s\S]*?\);',
    f'const imageFiles = {images_js_array};',
    html_content
)

html_content = re.sub(
    r'<img src="https://picsum.photos/350/350" alt="Pass Image">',
    f'<img src={base64_images[0]} alt="Pass Image">',
    html_content
)

html_content = re.sub(
    r'img\.src = `https://gift-surprise-v2.vercel\.app/style/img/Anh \(\$\{randomNum\}\)\.jpg`;',
    r'img.src = imageFiles[Math.floor(Math.random() * imageFiles.length)];',
    html_content
)

with open('8th3.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("Updated HTML with compressed images saved.")
