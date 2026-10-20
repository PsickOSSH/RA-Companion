[app]
title = RA Companion
package.name = racompanion
package.domain = io.github.psickossh.racompanion
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf
source.exclude_dirs = tests, bin, build, dist, docs, gradle, .buildozer, .gradle, .idea, __pycache__
source.exclude_patterns = app.py, widgets.py, ra_companion.py, build-exe.bat
version.regex = __version__ = ['"](.*)['"]
version.filename = %(source.dir)s/appinfo.py
requirements = python3,kivy,requests,certifi
orientation = portrait
osx.python_version = 3
osx.kivy_version = 2.1.0
fullscreen = 0
android.accept_sdk_license = True
android.permissions = INTERNET,POST_NOTIFICATIONS
android.api = 33
android.minapi = 21
android.sdk = 33
android.ndk = 28c
android.archs = arm64-v8a,armeabi-v7a
icon.filename = %(source.dir)s/docs/icon.png
presplash.filename = %(source.dir)s/docs/logo.png
android.presplash_color = #0f1420
p4a.branch = develop