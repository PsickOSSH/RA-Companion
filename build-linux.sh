#!/usr/bin/env bash
# Builds the Linux version of RA Companion as an AppImage: RA-Companion-<version>-x86_64.AppImage
#
# Needs Python 3 with Tkinter (sudo apt install python3-tk python3-venv), then, in a virtual environment:
#   python3 -m venv ~/venvs/ra && source ~/venvs/ra/bin/activate
#   pip install pyinstaller pillow
# Run this script from the project folder:  ./build-linux.sh
#
# The result is written to ./dist-linux/. For the widest compatibility build on an older Ubuntu (22.04): the AppImage
# needs at least the version of glibc of the machine that built it.
set -euo pipefail
cd "$(dirname "$0")"

VERSION=$(python3 -c "import appinfo; print(appinfo.__version__)")
HERE=$PWD
WORK=${WORK:-$HOME/.cache/ra-companion-build}      # outside the project (faster than /mnt/c when run in WSL)
OUT=$HERE/dist-linux
APPDIR=$WORK/AppDir

rm -rf "$WORK" "$OUT"
mkdir -p "$WORK" "$OUT"

# every skin is loaded by name: PyInstaller must be told about them
HIDDEN=()
for f in skins/*.py; do
  n=$(basename "$f" .py)
  [ "$n" = "__init__" ] && continue
  HIDDEN+=(--hidden-import "skins.$n")
done

python3 -m PyInstaller --clean --noconfirm --name RA-Companion \
  --add-data "$HERE/docs/icon.png:." --add-data "$HERE/skins:skins" --add-data "$HERE/fonts/NotoEmoji.ttf:fonts" "${HIDDEN[@]}" \
  --distpath "$WORK/dist" --workpath "$WORK/work" --specpath "$WORK" ra_companion.py

# AppDir: the program, a launcher (AppRun), the menu entry and the icon
mkdir -p "$APPDIR/usr/lib"
cp -r "$WORK/dist/RA-Companion" "$APPDIR/usr/lib/RA-Companion"
cp docs/icon.png "$APPDIR/ra-companion.png"
cat > "$APPDIR/AppRun" <<'EOF'
#!/bin/sh
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/lib/RA-Companion/RA-Companion" "$@"
EOF
chmod +x "$APPDIR/AppRun"
cat > "$APPDIR/RA-Companion.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=RA Companion
Comment=Companion app for RetroAchievements
Exec=RA-Companion
Icon=ra-companion
Categories=Game;Utility;
Terminal=false
X-AppImage-Version=$VERSION
EOF

# appimagetool (downloaded once); --appimage-extract-and-run works without FUSE (WSL, containers)
TOOL=$HOME/.cache/appimagetool-x86_64.AppImage
if [ ! -x "$TOOL" ]; then
  curl -L -o "$TOOL" https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage
  chmod +x "$TOOL"
fi
ARCH=x86_64 "$TOOL" --appimage-extract-and-run "$APPDIR" "$OUT/RA-Companion-$VERSION-x86_64.AppImage"

echo
echo "Done: $OUT/RA-Companion-$VERSION-x86_64.AppImage"
