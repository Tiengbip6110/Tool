import urllib.request
import json
import os

filepath = "Projects C01.1 (8th3.html)"
with open(filepath, "rb") as f:
    data = f.read()

req = urllib.request.Request("https://api.file.io", data=data)
req.add_header('Content-Type', 'application/octet-stream')

try:
    with urllib.request.urlopen(req) as response:
        result = response.read().decode('utf-8')
        print(result)
except Exception as e:
    print(e)
