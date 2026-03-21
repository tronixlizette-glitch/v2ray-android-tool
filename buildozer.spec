[app]
title = V2Ray Node Tool
package.name = v2raytool
package.domain = org.v2raytool
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0.1
requirements = python3,kivy==2.3.0,requests,certifi
orientation = portrait
fullscreen = 0

android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a,armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1
