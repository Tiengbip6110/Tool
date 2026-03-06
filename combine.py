import re
import urllib.parse
import base64

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

# Load all components
index_html = read_file('project/index.html')
style_css = read_file('project/style.css')
script_js = read_file('project/script.js')
image_data = read_file('project/image_data.js')

gift_html = read_file('project/gift.html')
gift_style = read_file('project/gift_style.css')
gift_script = read_file('project/gift_script.js')

# Fix asset paths in CSS and JS to absolute URL pointing to https://gift-surprise-v2.vercel.app/style/...
def make_absolute_url(match):
    path = match.group(1)
    if path.startswith('http') or path.startswith('data:'):
        return f"url('{path}')"
    # Ensure it's pointing to the correct base
    # Most paths like style/img/... should be https://gift-surprise-v2.vercel.app/style/img/...
    if path.startswith('../'):
        path = path[3:]
    if not path.startswith('style/'):
        path = 'style/' + path
    return f"url('https://gift-surprise-v2.vercel.app/{path}')"

style_css = re.sub(r"url\(['\"]?(.*?)['\"]?\)", make_absolute_url, style_css)
gift_style = re.sub(r"url\(['\"]?(.*?)['\"]?\)", make_absolute_url, gift_style)

# Fix script.js assets like sounds and cover images
def make_absolute_src(match):
    path = match.group(1)
    if path.startswith('http') or path.startswith('data:'):
        return f'"{path}"'
    if not path.startswith('style/'):
        path = 'style/' + path
    return f'"https://gift-surprise-v2.vercel.app/{path}"'

script_js = re.sub(r'"(style/[^"]+)"', make_absolute_src, script_js)
gift_html = re.sub(r'"(style/[^"]+)"', make_absolute_src, gift_html)

# Inject gift iframe fully encoded to avoid loading external files
gift_combined = gift_html
# Inject CSS into gift.html
gift_combined = gift_combined.replace('<link rel="stylesheet" href="./style/style.css">', f'<style>{gift_style}</style>')
gift_combined = gift_combined.replace('<link rel="stylesheet" href="../style.css">', '')
# Inject JS into gift.html
gift_combined = gift_combined.replace('<script src="./style/script.js"></script>', f'<script>{gift_script}</script>')

# Convert gift_combined to base64 data URI to put in main HTML iframe src
encoded_gift_html = base64.b64encode(gift_combined.encode('utf-8')).decode('utf-8')
gift_iframe_src = f"data:text/html;base64,{encoded_gift_html}"

# Replace iframe src in index_html
index_html = re.sub(r'<iframe src="style/gift/gift\.html"[^>]*></iframe>', f'<iframe src="{gift_iframe_src}" frameborder="0" class="gift-iframe"></iframe>', index_html)

# Inject Letter text
letter_text = read_file('project/letter.txt')
# Replace fetch logic with hardcoded text logic
script_js = re.sub(
    r'async function loadLetter\(\) \{.*?\n\}',
    f'async function loadLetter() {{ letterText = `{letter_text}`.split(/\\n\\s*\\n/).map((p) => p.trim()).filter((p) => p !== ""); }}',
    script_js,
    flags=re.DOTALL
)

# Replace links in main index_html
# CSS
index_html = index_html.replace('<link rel="stylesheet" href="style/style.css" />', f'<style>\n{style_css}\n</style>')
# Img
index_html = index_html.replace('src="style/img/Anh Pass.jpg"', 'src=""') # the JS will load this

# Replace static img src in HTML
index_html = re.sub(r'src="style/img/asset/([^"]+)"', r'src="https://gift-surprise-v2.vercel.app/style/img/asset/\1"', index_html)
index_html = index_html.replace('src="style/pop.mp3"', 'src="https://gift-surprise-v2.vercel.app/style/pop.mp3"')

# Finally, Javascript
final_js = f"<script>\n{image_data}\n\n{script_js}\n</script>\n"
index_html = index_html.replace('<script src="style/script.js"></script>', final_js)

with open('Projects C01.1 (8th3.html)', 'w', encoding='utf-8') as f:
    f.write(index_html)

print("Created final combined HTML file.")
