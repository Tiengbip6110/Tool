import re

with open('replit_source.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove Vite injected scripts
content = re.sub(r'<script type="module">.*?</script>\s*', '', content, flags=re.DOTALL)
content = re.sub(r'<script type="module" src="/@vite/client"></script>\s*', '', content)
content = re.sub(r'<script src="https://replit-cdn\.com/replit-pill/replit-pill\.global\.js"[^>]*></script>', '', content)
# Also remove the specific runtime-error-plugin
content = re.sub(r'<script type="module">\s*import \{ createHotContext \}.*?</script>\s*', '', content, flags=re.DOTALL)

with open('chucmung.html', 'w', encoding='utf-8') as f:
    f.write(content.strip() + '\n')
