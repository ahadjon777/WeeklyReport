"""Lokal tarmoq uchun server (Windows/Linux). Ishga tushirish: python serve.py"""
import os
import socket

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from waitress import serve  # noqa: E402

from config.wsgi import application  # noqa: E402

PORT = int(os.environ.get("HISOBOT_PORT", "8000"))


def local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"


if __name__ == "__main__":
    print("=" * 56)
    print(" WeeklyReport ishga tushdi")
    print(f" Xodimlar shu manzilni brauzerda ochadi:  http://{local_ip()}:{PORT}")
    print(" To'xtatish: Ctrl+C yoki oynani yoping")
    print("=" * 56)
    serve(application, host="0.0.0.0", port=PORT, threads=8)
