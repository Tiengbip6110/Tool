from PIL import Image, ImageEnhance
import io
import base64
import os

def process_image(filepath, target_size=(100, 100)):
    # Open the image
    img = Image.open(filepath).convert("RGBA")

    # Enhance sharpness
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(2.0)

    # Resize to make it smaller
    img = img.resize(target_size, Image.LANCZOS)

    # Save to bytes
    buffer = io.BytesBytesIO()
    # Save as WEBP to save space and support transparency
    img.save(buffer, format="WEBP", quality=80)

    # Encode to base64
    b64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/webp;base64,{b64_str}"
