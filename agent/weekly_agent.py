"""WeeklyReport eslatma dasturi (Windows, faqat standart kutubxonalar).

Orqa fonda ishlaydi. Serverdan eslatma vaqtlarini oladi (11:00, 16:00, 19:00)
va shu vaqtda ekran ustida oyna chiqaradi. Brauzer yopiq bo'lsa ham ishlaydi.

Sozlama fayli:  %LOCALAPPDATA%\\WeeklyReport\\agent_config.ini
    [agent]
    server=http://192.168.1.10:8000
    username=ali

Sinash:  weekly_agent.exe --test   (eslatma oynasini darhol ko'rsatadi)
"""
import configparser
import datetime as dt
import json
import os
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser

APP_DIR = os.path.join(os.environ.get("LOCALAPPDATA") or os.path.expanduser("~"), "WeeklyReport")
CONFIG_PATH = os.path.join(APP_DIR, "agent_config.ini")
STATE_PATH = os.path.join(APP_DIR, "agent_state.json")
LOG_PATH = os.path.join(APP_DIR, "agent.log")
LOCK_PORT = 47653           # bitta nusxa ishlashi uchun
POLL_SECONDS = 20           # vaqtni tekshirish oralig'i
REFRESH_SECONDS = 300       # jadvalni serverdan yangilash oralig'i
RETRY_SECONDS = 60          # server javob bermasa, qayta urinish
LATE_WINDOW = dt.timedelta(hours=3)  # kompyuter kech yoqilsa, eslatma shu vaqtgacha ko'rsatiladi


def log(msg):
    try:
        os.makedirs(APP_DIR, exist_ok=True)
        if os.path.exists(LOG_PATH) and os.path.getsize(LOG_PATH) > 200_000:
            os.remove(LOG_PATH)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"{dt.datetime.now():%Y-%m-%d %H:%M:%S}  {msg}\n")
    except OSError:
        pass


# ------------------------------------------------------------------ sof mantiq

def slot_datetime(now, slot):
    h, m = (int(x) for x in slot["time"].split(":")[:2])
    return now.replace(hour=h, minute=m, second=0, microsecond=0)


def pick_due(now, slots, fired, window=LATE_WINDOW):
    """Hozirgi vaqtga ko'ra: (ko'rsatiladigan slot yoki None, jimgina yopiladigan slot id'lari)."""
    passed = [s for s in slots if s["id"] not in fired and slot_datetime(now, s) <= now]
    if not passed:
        return None, []
    passed.sort(key=lambda s: slot_datetime(now, s))
    latest = passed[-1]
    silent = [s["id"] for s in passed[:-1]]
    if now - slot_datetime(now, latest) > window:   # juda kech bo'lib qolgan
        silent.append(latest["id"])
        return None, silent
    return latest, silent


def load_state(today):
    try:
        with open(STATE_PATH, encoding="utf-8") as f:
            st = json.load(f)
        if st.get("date") == today:
            return {"date": today, "fired": list(st.get("fired", []))}
    except (OSError, ValueError):
        pass
    return {"date": today, "fired": []}


def save_state(st):
    try:
        os.makedirs(APP_DIR, exist_ok=True)
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(st, f)
    except OSError:
        pass


# ------------------------------------------------------------------ tarmoq

def load_config():
    cp = configparser.ConfigParser()
    cp.read([CONFIG_PATH, os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_config.ini")], encoding="utf-8")
    server = cp.get("agent", "server", fallback="").strip().rstrip("/")
    username = cp.get("agent", "username", fallback="").strip()
    if not server or not username:
        raise SystemExit("agent_config.ini topilmadi yoki to'liq emas (server va username kerak).")
    return server, username


def fetch_schedule(server, username):
    url = f"{server}/eslatma/api/?" + urllib.parse.urlencode({"u": username})
    with urllib.request.urlopen(url, timeout=8) as r:
        return json.loads(r.read().decode("utf-8"))


# ------------------------------------------------------------------ oyna

def show_popup(slot_time, message, url):
    """Ekran ustida eslatma oynasi. tkinter bo'lmasa, oddiy Windows xabar oynasi."""
    try:
        import tkinter as tk
    except Exception:
        return _fallback_box(slot_time, message, url)
    try:
        BG, INK, MUTED, ACCENT = "#ffffff", "#151b26", "#6b7785", "#4f46e5"
        root = tk.Tk()
        root.title("WeeklyReport")
        root.configure(bg=BG)
        root.resizable(False, False)
        root.attributes("-topmost", True)
        w, h = 440, 250
        root.geometry(f"{w}x{h}+{(root.winfo_screenwidth() - w) // 2}+{(root.winfo_screenheight() - h) // 3}")

        tk.Frame(root, bg=ACCENT, height=6).pack(fill="x")
        tk.Label(root, text=f"ESLATMA · {slot_time}", bg=BG, fg=ACCENT, font=("Segoe UI", 10, "bold")).pack(pady=(18, 2))
        tk.Label(root, text="Hisobotni to'ldiring", bg=BG, fg=INK, font=("Segoe UI", 17, "bold")).pack()
        tk.Label(root, text=message, bg=BG, fg=MUTED, font=("Segoe UI", 10), wraplength=380, justify="center").pack(pady=(8, 0), padx=24)

        def go():
            try:
                webbrowser.open(url)
            finally:
                root.destroy()

        row = tk.Frame(root, bg=BG)
        row.pack(side="bottom", pady=22)
        tk.Button(row, text="Hisobotga o'tish", command=go, bg=ACCENT, fg="white", activebackground="#6d65f0",
                  activeforeground="white", relief="flat", font=("Segoe UI", 10, "bold"), padx=18, pady=7, cursor="hand2").pack(side="left", padx=6)
        tk.Button(row, text="Keyinroq", command=root.destroy, bg="#eef0f5", fg=INK, relief="flat",
                  font=("Segoe UI", 10), padx=18, pady=7, cursor="hand2").pack(side="left", padx=6)

        def keep_on_top():
            try:
                root.lift()
                root.attributes("-topmost", True)
                root.after(4000, keep_on_top)
            except tk.TclError:
                pass

        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except Exception:
            pass
        keep_on_top()
        root.focus_force()
        root.mainloop()
    except Exception as e:  # oyna ochilmasa ham dastur to'xtamasin
        log(f"tkinter xato: {e}")
        _fallback_box(slot_time, message, url)


def _fallback_box(slot_time, message, url):
    try:
        import ctypes

        MB_YESNO, MB_ICONINFORMATION, MB_TOPMOST = 0x4, 0x40, 0x40000
        res = ctypes.windll.user32.MessageBoxW(
            0, f"{message}\n\nHisobot sahifasi ochilsinmi?", f"WeeklyReport · eslatma {slot_time}",
            MB_YESNO | MB_ICONINFORMATION | MB_TOPMOST,
        )
        if res == 6:  # Ha
            webbrowser.open(url)
    except Exception as e:
        log(f"MessageBox xato: {e}")


# ------------------------------------------------------------------ asosiy sikl

def single_instance():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", LOCK_PORT))
    except OSError:
        return None
    return s


def main():
    server, username = load_config()
    if "--test" in sys.argv:
        show_popup(dt.datetime.now().strftime("%H:%M"), "Bu sinov eslatmasi. Dastur to'g'ri ishlayapti.", server + "/")
        return
    lock = single_instance()
    if lock is None:
        return
    log(f"ishga tushdi: server={server}, user={username}")
    schedule, last_fetch = None, 0.0
    while True:
        try:
            now = dt.datetime.now()
            today = now.strftime("%Y-%m-%d")
            state = load_state(today)
            if schedule is None or time.time() - last_fetch > REFRESH_SECONDS:
                try:
                    schedule = fetch_schedule(server, username)
                    last_fetch = time.time()
                except (urllib.error.URLError, OSError, ValueError) as e:
                    last_fetch = time.time() - REFRESH_SECONDS + RETRY_SECONDS
                    log(f"server javob bermadi: {e}")
            if schedule and now.weekday() in schedule.get("workdays", [0, 1, 2, 3, 4]):
                slot, silent = pick_due(now, schedule.get("slots", []), set(state["fired"]))
                if silent:
                    state["fired"] += silent
                if slot:
                    show = True
                    try:  # eng yangi holatni so'raymiz
                        fresh = fetch_schedule(server, username)
                        if fresh.get("only_if_no_report") and fresh.get("reported_today"):
                            show = False
                    except (urllib.error.URLError, OSError, ValueError):
                        pass
                    state["fired"].append(slot["id"])
                    save_state(state)  # oyna ochilishidan oldin saqlaymiz (takror chiqmasin)
                    if show:
                        log(f"eslatma: {slot['time']}")
                        show_popup(slot["time"], slot["message"], server + "/")
                save_state(state)
        except Exception as e:
            log(f"xato: {e}")
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
