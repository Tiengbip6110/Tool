from PIL import Image, ImageEnhance
import io
import base64
import os
import json

def process_image(filepath, target_size=None, crop_pixels=0):
    img = Image.open(filepath).convert("RGBA")

    # Crop borders to remove background grid/noise if any
    if crop_pixels > 0:
        w, h = img.size
        img = img.crop((crop_pixels, crop_pixels, w - crop_pixels, h - crop_pixels))

    # Enhance sharpness
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(3.0)  # Enhance sharpness

    # Enhance contrast
    enhancer2 = ImageEnhance.Contrast(img)
    img = enhancer2.enhance(1.2)

    # Resize if needed
    if target_size:
        img = img.resize(target_size, Image.LANCZOS)

    buffer = io.BytesIO()
    # Save as PNG to maintain transparency (if any, though these are JPEGs originally)
    img.save(buffer, format="PNG")
    b64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64_str}"

files = {
    "music_1": "/tmp/file_attachments/Screenshot_20260308_205308_com_hihonor_photos_SlotAlbumActivity.jpg",
    "music_2": "/tmp/file_attachments/Screenshot_20260308_205431_com_hihonor_photos_SlotAlbumActivity.jpg",
    "letter_3": "/tmp/file_attachments/Screenshot_20260308_205330_com_hihonor_photos_SlotAlbumActivity.jpg",
    "image_4": "/tmp/file_attachments/Screenshot_20260308_205405_com_hihonor_photos_SlotAlbumActivity.jpg"
}

results = {}
for key, filepath in files.items():
    # We will resize to something reasonable like 80x80 or 100x100 for icons to save space
    # and crop 5 pixels to remove boundaries
    results[key] = process_image(filepath, target_size=(100, 100), crop_pixels=10)

with open("images_base64.json", "w") as f:
    json.dump(results, f)

print("Images processed and saved to images_base64.json")
