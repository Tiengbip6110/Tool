import base64

with open('images.txt', 'r') as f:
    images = [line.strip() for line in f if line.strip()]

if len(images) != 12:
    print(f"Expected 12 images, found {len(images)}")
    exit(1)

with open('chucmung.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

for i, img_path in enumerate(images):
    with open(img_path, 'rb') as f:
        img_data = f.read()
    b64_data = base64.b64encode(img_data).decode('utf-8')
    data_uri = f"data:image/jpeg;base64,{b64_data}"

    target_str = f"img/new_{i+1}.jpg"
    html_content = html_content.replace(target_str, data_uri)

with open('chucmung.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("Images replaced with base64 data URIs.")
