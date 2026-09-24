[app]

# (str) Title of your application
title = LabMatrice Prof V9

# (str) Package name
package.name = labmatriceprof

# (str) Package domain (needed for android/ios packaging)
package.domain = org.labmatrice

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (python, kv, png, etc.)
source.include_exts = py,png,jpg,kv,atlas

# (list) Application requirements
requirements = python3,kivy,sqlite3,android

# (str) Application versioning
version = 9.0.0

# (list) Permissions
android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, MANAGE_EXTERNAL_STORAGE

# (int) Target Android API
android.api = 33

# (int) Minimum API supported
android.minapi = 21

# (str) Supported orientation
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) List of Android architectures to build for
android.archs = arm64-v8a, armeabi-v7a

# (bool) Accept SDK license automatically
android.accept_sdk_license = True

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = false, 1 = true)
warn_on_root = 1
