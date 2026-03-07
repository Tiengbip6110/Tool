with open("project/index.html", "r") as f:
    html = f.read()

# Replace any repeated let/const that were causing issues in the latter half.
# JS2 starts after: // --- GIFT INTEGRATION LOGIC ---
parts = html.split("// --- GIFT INTEGRATION LOGIC ---")
if len(parts) == 2:
    js2 = parts[1]

    js2 = js2.replace('const giftPopSound = document.getElementById("pop-sound");', 'var giftPopSoundEl = document.getElementById("pop-sound");')
    js2 = js2.replace('if (giftPopSound) {', 'if (giftPopSoundEl) {')
    js2 = js2.replace('const sound = giftPopSound.cloneNode();', 'const sound = giftPopSoundEl.cloneNode();')
    js2 = js2.replace('const popSound = document.getElementById("pop-sound");', 'var giftPopSoundEl = document.getElementById("pop-sound");')
    js2 = js2.replace('if (popSound) {', 'if (giftPopSoundEl) {')
    js2 = js2.replace('const sound = popSound.cloneNode();', 'const sound = giftPopSoundEl.cloneNode();')

    html = parts[0] + "// --- GIFT INTEGRATION LOGIC ---" + js2

with open("project/index.html", "w") as f:
    f.write(html)
