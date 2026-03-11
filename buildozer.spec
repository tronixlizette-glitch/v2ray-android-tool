[app]

# (str) Title of your application
title = V2Ray Node Tool

# (str) Package name
package.name = v2raytool

# (str) Package domain (needed for android/ios packaging)
package.domain = org.v2raytool

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas

# (str) Application versioning (method 1)
version = 1.0.0

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy==2.3.0,requests,certifi,urllib3,charset-normalizer,idna

# (str) Supported orientation (landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (string) Presplash background color (for new android toolchain)
android.presplash_color = #0D1117

# (list) Permissions
android.permissions = INTERNET,ACCESS_NETWORK_STATE

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK / AAB will support.
android.minapi = 21

# (str) Android build tools version to use
android.build_tools_version = 33.0.0

# (bool) If True, then skip trying to update the Android sdk
android.skip_update = False

# (int) Android NDK version to use
android.ndk = 25b

# (str) Android app theme, default is ok for Kivy-based app
android.apptheme = @android:style/Theme.NoTitleBar

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
