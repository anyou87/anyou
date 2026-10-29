# 连连看 - 50桌集成预测工具（Android 打包配置）
# 用于 buildozer 在 Linux 环境（本机 WSL 或 GitHub Actions）打包 APK

[app]

# 应用名（手机桌面显示的名称）
title = 连连看

# 包名：Android 唯一标识，如需发布请改成你自己的域名，如 com.yourname.lianliankan
package.name = lianliankan
package.domain = org.llk

# 源码目录（当前目录）
source.dir = .
# 需要打进 APK 的文件类型（py 脚本 + 图标 + 中文字体）
source.include_exts = py,png,jpg,kv,atlas,ttf,ttc,otf

# 版本号
version = 0.1

# 依赖：Python + Kivy 框架
requirements = python3,kivy

# 屏幕方向：竖屏（方便单手点按钮）
orientation = portrait

# 是否全屏（0=有状态栏/返回键，1=全屏沉浸）
fullscreen = 0

# 应用图标（512x512 PNG）
icon.filename = %(source.dir)s/icon.png
# 启动闪屏图（与图标同款）
presplash.filename = %(source.dir)s/icon.png

# ---------- Android 兼容性 ----------
# 支持 64 位和 32 位 ARM 手机（覆盖绝大多数机型）
android.archs = arm64-v8a, armeabi-v7a
# 最低安卓版本 5.0，目标版本 14
android.api = 34
android.minapi = 21
android.ndk = 25b
android.sdk = 34

# 允许系统备份数据
android.allow_backup = True
# 使用私有存储
android.private_storage = True
# 自动接受 Android SDK 许可协议（CI/无交互环境必需，否则 Build-Tools 装不上）
android.accept_sdk_license = True

[buildozer]

# 日志级别：2=警告以上
log_level = 2
warn_on_root = 1
