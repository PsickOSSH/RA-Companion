"""Regenerate the Buy Me a Coffee icons embedded in config.py from docs/bmc-logo-yellow.png.

Usage (from anywhere):  python docs/embed_icon.py
Needs Pillow (pip install pillow). Not packaged in the APK (docs/ is excluded).
"""
import base64
import io
import os
import re

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "bmc-logo-yellow.png")
CONFIG = os.path.join(HERE, os.pardir, "config.py")
# constant name in config.py -> size in pixels
TARGETS = {"BMC_ICON_B64": 128, "BMC_ICON_SMALL_B64": 36}


def block(name, size, image):
    buf = io.BytesIO()
    image.resize((size, size), Image.LANCZOS).save(buf, "PNG", optimize=True)
    text = base64.b64encode(buf.getvalue()).decode()
    lines = ['    "%s"' % text[i:i + 76] for i in range(0, len(text), 76)]
    return "%s = (\n%s\n)" % (name, "\n".join(lines))


def main():
    image = Image.open(SOURCE).convert("RGBA")
    with open(CONFIG, "rb") as f:
        raw = f.read().decode("utf-8")
    crlf = "\r\n" in raw
    data = raw.replace("\r\n", "\n")
    for name, size in TARGETS.items():
        pattern = re.compile(r"^%s = \(\n(?:    \".*\"\n)+\)" % name, re.M)
        if not pattern.search(data):
            raise SystemExit("%s not found in config.py" % name)
        data = pattern.sub(lambda m: block(name, size, image), data, count=1)
    if crlf:
        data = data.replace("\n", "\r\n")
    with open(CONFIG, "wb") as f:
        f.write(data.encode("utf-8"))
    print("config.py updated from", os.path.basename(SOURCE), "(%s)" % ", ".join("%s=%dpx" % t for t in TARGETS.items()))


if __name__ == "__main__":
    main()
