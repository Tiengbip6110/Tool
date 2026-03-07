import re

with open("project/index.html", "r") as f:
    content = f.read()

content = content.replace(
    'if (!isMessaging) return;',
    'if (typeof isMessaging === "undefined" || !isMessaging) return;'
)
content = content.replace(
    'if (isMessaging) return;',
    'if (typeof isMessaging !== "undefined" && isMessaging) return;'
)

with open("project/index.html", "w") as f:
    f.write(content)
