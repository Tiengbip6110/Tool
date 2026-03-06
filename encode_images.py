import os
import base64

image_dir = '/tmp/file_attachments/'
output_file = 'project/image_data.js'

images = []
# Ensure stable order
files = sorted([f for f in os.listdir(image_dir) if f.endswith('.jpg') or f.endswith('.png')])

if not files:
    print("No images found in", image_dir)
    exit(1)

for file in files:
    with open(os.path.join(image_dir, file), 'rb') as f:
        encoded = base64.b64encode(f.read()).decode('utf-8')
        ext = file.split('.')[-1].lower()
        mime = f"image/{ext}" if ext != 'jpg' else 'image/jpeg'
        images.append(f"data:{mime};base64,{encoded}")

with open(output_file, 'w') as f:
    f.write("const userImages = [\n")
    for img in images:
        f.write(f"  '{img}',\n")
    f.write("];\n")

print(f"Encoded {len(images)} images to {output_file}")
