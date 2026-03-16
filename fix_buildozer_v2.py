# -*- coding: utf-8 -*-
import os

# 修复buildozer的__init__.py
buildozer_path = r"C:\Users\Administrator\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\buildozer\__init__.py"

print(f"Fixing: {buildozer_path}")

with open(buildozer_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 修复重复的try块
broken_import = """try:
    try:
    from urllib.request import FancyURLopener
except ImportError:
    # Python 3.14+ removed FancyURLopener
    from urllib.request import urlretrieve
    FancyURLopener = None
except ImportError:
    # Python 3.14+ removed FancyURLopener
    from urllib.request import urlretrieve
    FancyURLopener = None"""

fixed_import = """try:
    from urllib.request import FancyURLopener
except ImportError:
    # Python 3.14+ removed FancyURLopener
    from urllib.request import urlretrieve
    FancyURLopener = None"""

if broken_import in content:
    content = content.replace(broken_import, fixed_import)
    with open(buildozer_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed broken import!")
else:
    print("Import section not found or already fixed")

# 检查urlretrieve是否正确定义
if "def urlretrieve" not in content:
    print("WARNING: urlretrieve function might be missing")
else:
    print("urlretrieve function exists")
