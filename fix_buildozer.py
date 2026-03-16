# -*- coding: utf-8 -*-
import os
import sys

# 找到buildozer安装路径
python_path = sys.executable
buildozer_path = os.path.join(os.path.dirname(python_path), 'Lib', 'site-packages', 'buildozer', '__init__.py')

print(f"Fixing: {buildozer_path}")

with open(buildozer_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 替换导入语句
old_import = "from urllib.request import FancyURLopener"
new_import = """try:
    from urllib.request import FancyURLopener
except ImportError:
    # Python 3.14+ removed FancyURLopener
    from urllib.request import urlretrieve
    FancyURLopener = None"""

if old_import in content:
    content = content.replace(old_import, new_import)
    with open(buildozer_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed FancyURLopener import!")
else:
    print("Import not found or already fixed")

# 还需要修复 urlretrieve 的使用部分
old_class = """class ChromeDownloader(FancyURLopener):
    version = (
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/28.0.1500.71 Safari/537.36')


urlretrieve = ChromeDownloader().retrieve"""

new_class = """if FancyURLopener:
    class ChromeDownloader(FancyURLopener):
        version = (
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/28.0.1500.71 Safari/537.36')

    urlretrieve = ChromeDownloader().retrieve
else:
    def urlretrieve(url, filename=None, reporthook=None, data=None):
        import urllib.request
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-Agent', 
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/28.0.1500.71 Safari/537.36')]
        urllib.request.install_opener(opener)
        return urllib.request.urlretrieve(url, filename, reporthook, data)"""

if old_class in content:
    content = content.replace(old_class, new_class)
    with open(buildozer_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed ChromeDownloader class!")
else:
    print("ChromeDownloader class not found or already fixed")
