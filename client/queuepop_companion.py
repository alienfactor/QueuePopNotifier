"""Queue Pop Notifier – desktop client 0.3.39."""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import hashlib
import json
import locale
import os
from pathlib import Path
import queue
import subprocess
import sys
import tempfile
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk
import urllib.parse
import urllib.request
import urllib.error
import webbrowser

if os.name == "nt":
    import winreg

APP_VERSION = "0.3.39"
SIGNAL_PROTOCOL = 2
GITHUB_REPOSITORY = "alienfactor/QueuePopNotifier"
APP_DIR = Path(os.environ.get("APPDATA", Path.home())) / "QueuePopNotifier"
CONFIG_PATH = APP_DIR / "config.json"
ICON_PATH = Path(__file__).with_name("queuepop_notifier.ico")

DEFAULTS = {
    "pushover_user_key": "",
    "pushover_app_token": "",
    "scan_interval_ms": 250,
    "confirm_frames": 3,
    "language": "auto",
    "pushover_priority": 1,
    "start_with_windows": False,
}

TEXTS = {
    "de": {
        "starting": "Wird gestartet …", "searching_window": "Suche nach dem WoW-Fenster …",
        "events": "EREIGNISSE", "notifications": "Benachrichtigungen",
        "active_ready": "Aktiv · bereit", "not_configured": "Nicht eingerichtet",
        "credentials_unverified": "Noch nicht geprüft", "credentials_checking": "Wird geprüft …",
        "credentials_invalid": "Zugangsdaten ungültig", "credentials_unavailable": "Prüfung nicht möglich",
        "settings": "Einstellungen ›", "configure": "Einrichten ›", "close": "Schließen ‹",
        "show": "Anzeigen", "hide": "Verbergen", "language": "Sprache",
        "language_auto": "Automatisch (Windows)", "language_de": "Deutsch", "language_en": "English",
        "priority": "Priorität", "priority_normal": "Normal", "priority_high": "Hoch",
        "settings_title": "Einstellungen", "settings_subtitle": "Queue Pop Notifier",
        "pushover_intro": "Verbindet den Client mit deinem Smartphone.",
        "user_key_help": "Dein persönlicher Empfängerschlüssel aus dem Pushover-Dashboard.",
        "app_token_help": "Der Token deiner Anwendung „Queue Pop Notifier“ bei Pushover.",
        "pushover_help": "Wo finde ich User Key und App-Token?  ↗",
        "notifications_intro": "Lege fest, wie auffällig Queue-Meldungen erscheinen.",
        "priority_normal_help": "Normal: Standardbenachrichtigung mit dem in Pushover gewählten Ton.",
        "priority_high_help": "Hoch: Auffälligere Zustellung ohne Bestätigung – für iOS empfohlen.",
        "general": "Allgemein",
        "start_with_windows": "Mit Windows starten",
        "test_pushover": "Testnachricht senden", "save": "Speichern", "saved": "Gespeichert ✓",
        "tray_settings": "Einstellungen …",
        "tray_status": "{indicator}  {status}", "tray_version": "Version {version} · Updates automatisch",
        "update_downloading": "Update {version} wird heruntergeladen …",
        "update_installing": "Update geprüft · Client wird neu gestartet",
        "update_notice_title": "Update wird installiert",
        "update_notice_message": "Version {version} wurde heruntergeladen und wird jetzt installiert. Der Client startet anschließend neu.",
        "update_install_failed_title": "Update fehlgeschlagen",
        "update_install_failed_message": "Das Update konnte nicht installiert werden: {error}",
        "update_checksum_failed": "Die Prüfsumme der heruntergeladenen EXE stimmt nicht.",
        "missing_title": "Fehlende Daten", "missing_message": "Bitte User Key und App/API Token eintragen.",
        "connection_test": "Verbindungstest", "connection_test_message": "Queue Pop Notifier ist verbunden.",
        "pushover_connected": "Pushover verbunden · Benachrichtigungen sind bereit",
        "pushover_failed": "Pushover fehlgeschlagen: {error}", "windows_required": "Windows erforderlich",
        "wow_missing_event": "WoW nicht gefunden · Der Client wartet auf ein laufendes WoW-Fenster",
        "wow_ready_event": "WoW erkannt · Überwachung bereit",
        "capture_restored": "Bildschirmprüfung wiederhergestellt · Überwachung bereit",
        "capture_failed": "WoW konnte vorübergehend nicht geprüft werden: {error}",
        "incompatible": "Addon nicht kompatibel · Signalprotokoll {protocol}, benötigt wird {required}",
        "unreadable": "unlesbar", "test_success": "Test erfolgreich",
        "test_success_message": "Addon, Client und Pushover funktionieren einwandfrei.",
        "test_detected": "Testsignal erkannt · Testnachricht wird gesendet",
        "requeued_title": "Wieder in der Warteschlange",
        "requeued_message": "Die Gruppensuche wurde nicht bestätigt. Du bist wieder für dieselbe Queue angemeldet.",
        "requeued_detected": "Wiedereinreihung erkannt · Korrekturmeldung wird gesendet",
        "queue_ready_named": "Queue bereit: {name}", "queue_ready_kind": "{kind}-Queue bereit",
        "confirm_in_wow": "Jetzt in WoW bestätigen.",
        "queue_detected": "Queue erkannt · Benachrichtigung wird gesendet",
        "queue_no_pushover": "Queue erkannt · Pushover ist noch nicht eingerichtet",
        "check_disturbed": "Überwachung gestört · WoW kann gerade nicht geprüft werden", "waiting_wow": "Warte auf WoW",
        "wow_not_open": "WoW ist nicht geöffnet oder wurde noch nicht erkannt.",
        "monitoring_active": "WoW erkannt · Queue-Überwachung aktiv", "wow_pop_ready": "WoW erkannt · bereit für Queue-Pops",
        "client_searching": "Client aktiv · wartet auf WoW", "client_started": "Client wird gestartet",
        "tray_open": "Öffnen", "tray_quit": "Beenden",
        "client_to_screen_failed": "Fensterposition konnte nicht ermittelt werden",
        "capture_error": "Bildschirmaufnahme fehlgeschlagen", "invalid_response": "Ungültige Antwort von Pushover",
        "pushover_rejected": "Pushover abgelehnt: {error}", "unknown_api_error": "unbekannter API-Fehler",
    },
    "en": {
        "starting": "Starting …", "searching_window": "Looking for the WoW window …",
        "events": "EVENTS", "notifications": "Notifications",
        "active_ready": "Active · ready", "not_configured": "Not configured",
        "credentials_unverified": "Not verified yet", "credentials_checking": "Checking …",
        "credentials_invalid": "Invalid credentials", "credentials_unavailable": "Could not verify",
        "settings": "Settings ›", "configure": "Set up ›", "close": "Close ‹",
        "show": "Show", "hide": "Hide", "language": "Language",
        "language_auto": "Automatic (Windows)", "language_de": "Deutsch", "language_en": "English",
        "priority": "Priority", "priority_normal": "Normal", "priority_high": "High",
        "settings_title": "Settings", "settings_subtitle": "Queue Pop Notifier",
        "pushover_intro": "Connects the client to your phone.",
        "user_key_help": "Your personal recipient key from the Pushover dashboard.",
        "app_token_help": "The token for your “Queue Pop Notifier” application in Pushover.",
        "pushover_help": "Where do I find the User Key and App Token?  ↗",
        "notifications_intro": "Choose how prominently queue alerts are delivered.",
        "priority_normal_help": "Normal: Standard notification using your selected Pushover sound.",
        "priority_high_help": "High: More prominent delivery without confirmation – recommended for iOS.",
        "general": "General",
        "start_with_windows": "Start with Windows",
        "test_pushover": "Send test notification", "save": "Save", "saved": "Saved ✓",
        "tray_settings": "Settings …",
        "tray_status": "{indicator}  {status}", "tray_version": "Version {version} · updates automatically",
        "update_downloading": "Downloading update {version} …",
        "update_installing": "Update verified · restarting client",
        "update_notice_title": "Installing update",
        "update_notice_message": "Version {version} has been downloaded and will now be installed. The client will then restart.",
        "update_install_failed_title": "Update failed",
        "update_install_failed_message": "The update could not be installed: {error}",
        "update_checksum_failed": "The downloaded EXE checksum does not match.",
        "missing_title": "Missing information", "missing_message": "Please enter the User Key and App/API Token.",
        "connection_test": "Connection test", "connection_test_message": "Queue Pop Notifier is connected.",
        "pushover_connected": "Pushover connected · notifications are ready",
        "pushover_failed": "Pushover failed: {error}", "windows_required": "Windows required",
        "wow_missing_event": "WoW not found · the client is waiting for a running WoW window",
        "wow_ready_event": "WoW detected · monitoring ready",
        "capture_restored": "Screen capture restored · monitoring ready",
        "capture_failed": "WoW could not be checked temporarily: {error}",
        "incompatible": "Add-on incompatible · signal protocol {protocol}, required: {required}",
        "unreadable": "unreadable", "test_success": "Test successful",
        "test_success_message": "Add-on, client and Pushover are working correctly.",
        "test_detected": "Test signal detected · sending test notification",
        "requeued_title": "Back in the queue",
        "requeued_message": "The group invite was not confirmed. You are queued for the same activity again.",
        "requeued_detected": "Requeue detected · sending correction notification",
        "queue_ready_named": "Queue ready: {name}", "queue_ready_kind": "{kind} queue ready",
        "confirm_in_wow": "Confirm in WoW now.",
        "queue_detected": "Queue detected · sending notification",
        "queue_no_pushover": "Queue detected · Pushover is not configured yet",
        "check_disturbed": "Monitoring interrupted · WoW cannot be checked right now", "waiting_wow": "Waiting for WoW",
        "wow_not_open": "WoW is not open or has not been detected yet.",
        "monitoring_active": "WoW detected · queue monitoring active", "wow_pop_ready": "WoW detected · ready for queue pops",
        "client_searching": "Client active · waiting for WoW", "client_started": "Client is starting",
        "tray_open": "Open", "tray_quit": "Quit",
        "client_to_screen_failed": "Could not determine the window position",
        "capture_error": "Screen capture failed", "invalid_response": "Invalid response from Pushover",
        "pushover_rejected": "Pushover rejected the request: {error}", "unknown_api_error": "unknown API error",
    },
}


def windows_language() -> str:
    """Return the supported Windows UI language, falling back to English."""
    if os.name == "nt":
        try:
            buffer = ctypes.create_unicode_buffer(85)
            if ctypes.windll.kernel32.GetUserDefaultLocaleName(buffer, len(buffer)):
                return "de" if buffer.value.lower().startswith("de") else "en"
        except (AttributeError, OSError):
            pass
    try:
        value = locale.getlocale()[0] or ""
    except (ValueError, TypeError):
        value = ""
    return "de" if value.lower().startswith("de") else "en"

user32 = ctypes.windll.user32 if os.name == "nt" else None
gdi32 = ctypes.windll.gdi32 if os.name == "nt" else None


def load_config() -> dict:
    data = dict(DEFAULTS)
    try:
        data.update(json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        pass
    if data.get("pushover_priority") not in (0, 1):
        data["pushover_priority"] = 1
    return data


def save_config(data: dict) -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def set_windows_startup(enabled: bool) -> None:
    """Create or remove the per-user Windows startup entry."""
    if os.name != "nt":
        return
    run_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, run_key, 0, winreg.KEY_SET_VALUE) as key:
            if enabled:
                executable = Path(sys.executable if getattr(sys, "frozen", False) else __file__).resolve()
                command = f'"{executable}"'
                if not getattr(sys, "frozen", False):
                    command = f'"{Path(sys.executable).resolve()}" "{executable}"'
                winreg.SetValueEx(key, "QueuePopNotifier", 0, winreg.REG_SZ, command)
            else:
                try:
                    winreg.DeleteValue(key, "QueuePopNotifier")
                except FileNotFoundError:
                    pass
    except OSError:
        # Startup integration must never prevent the notifier from running.
        pass


def acquire_single_instance():
    """Keep exactly one client process alive per Windows user session."""
    if os.name != "nt":
        return None
    kernel32 = ctypes.windll.kernel32
    kernel32.CreateMutexW.argtypes = (ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR)
    kernel32.CreateMutexW.restype = wintypes.HANDLE
    handle = kernel32.CreateMutexW(None, False, "Local\\QueuePopNotifier.Client")
    if not handle:
        return None
    if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        kernel32.CloseHandle(handle)
        return False
    return handle


def remove_stale_backup() -> None:
    """Remove a backup left by an interrupted older updater, when possible."""
    if os.name != "nt" or not getattr(sys, "frozen", False):
        return
    backup = Path(str(Path(sys.executable).resolve()) + ".old")
    try:
        backup.unlink(missing_ok=True)
    except OSError:
        # A legacy process may still hold the file. A later start retries.
        pass


def find_wow_window() -> tuple[int, str] | tuple[None, None]:
    if os.name != "nt":
        return None, None
    candidates: list[tuple[int, str]] = []
    callback_type = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

    def callback(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length:
            title = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, title, length + 1)
            value = title.value
            if "world of warcraft" in value.lower():
                candidates.append((int(hwnd), value))
        return True

    user32.EnumWindows(callback_type(callback), 0)
    return candidates[0] if candidates else (None, None)


def client_origin(hwnd: int) -> tuple[int, int]:
    point = wintypes.POINT(0, 0)
    if not user32.ClientToScreen(hwnd, ctypes.byref(point)):
        raise OSError("ClientToScreen fehlgeschlagen")
    return point.x, point.y


def capture_region(x: int, y: int, width: int, height: int) -> list[tuple[int, int, int]]:
    screen_dc = user32.GetDC(0)
    memory_dc = gdi32.CreateCompatibleDC(screen_dc)
    bitmap = gdi32.CreateCompatibleBitmap(screen_dc, width, height)
    old = gdi32.SelectObject(memory_dc, bitmap)
    try:
        if not gdi32.BitBlt(memory_dc, 0, 0, width, height, screen_dc, x, y, 0x00CC0020):
            raise OSError("Bildschirmaufnahme fehlgeschlagen")
        pixels = []
        for py in range(height):
            for px in range(width):
                color = gdi32.GetPixel(memory_dc, px, py)
                pixels.append((color & 255, (color >> 8) & 255, (color >> 16) & 255))
        return pixels
    finally:
        gdi32.SelectObject(memory_dc, old)
        gdi32.DeleteObject(bitmap)
        gdi32.DeleteDC(memory_dc)
        user32.ReleaseDC(0, screen_dc)


def close_color(actual, expected, tolerance=28):
    return all(abs(a - e) <= tolerance for a, e in zip(actual, expected))


def _six_bit(rgb):
    levels = [round(channel / 85) for channel in rgb]
    if any(level < 0 or level > 3 or abs(channel - level * 85) > 35
           for channel, level in zip(rgb, levels)):
        return None
    return levels[0] + levels[1] * 4 + levels[2] * 16


def decode_signal(pixels, width=180, height=30):
    def at(x, y):
        return pixels[y * width + x]

    # Nur am Beginn des magentafarbenen Markierungsfelds suchen. In älteren
    # Versionen konnte die Suche mitten in dessen vier Pixel breiter Fläche
    # beginnen und dadurch einen falschen Zellabstand ableiten.
    for y in range(height):
        for x in range(width - 16):
            if not close_color(at(x, y), (255, 0, 255)):
                continue
            if x > 0 and close_color(at(x - 1, y), (255, 0, 255)):
                continue
            cyan_x = None
            for offset in range(3, 12):
                candidate_x = x + offset
                if (close_color(at(candidate_x, y), (0, 255, 255))
                        and not close_color(at(candidate_x - 1, y), (0, 255, 255))):
                    cyan_x = x + offset
                    break
            if cyan_x is None:
                continue
            step = cyan_x - x
            if x + step * 8 > width:
                continue

            # Evaluate the whole cell instead of its left edge. With some WoW
            # UI scales the rounded edge coordinate falls into the one-pixel
            # gap and its grey background happens to decode as value 21.
            values = []
            for cell in range(8):
                start = x + step * cell
                end = min(x + step * (cell + 1), width)
                candidates = [at(px, y) for px in range(start, end)]
                counts = {}
                samples = {}
                for rgb in candidates:
                    code = _six_bit(rgb)
                    if code is not None:
                        counts[code] = counts.get(code, 0) + 1
                        samples.setdefault(code, rgb)
                if not counts:
                    values = []
                    break
                # The coloured texture occupies 4/5 of every cell; the gap can
                # therefore never win this majority vote.
                code = max(counts, key=counts.get)
                values.append(samples[code])
            if len(values) != 8:
                continue

            protocol = _six_bit(values[2])
            status = values[3]
            event_code = _six_bit(values[4])
            # Das Addon zeigt dieses Signal nur bei einem Queue-Ereignis oder
            # Test. Andere sichtbare Farbmuster werden verworfen.
            if not close_color(status, (255, 0, 0)):
                continue
            if not close_color(values[7], (255, 255, 0)):
                continue
            if protocol != SIGNAL_PROTOCOL:
                return {"error": "incompatible", "protocol": protocol}
            state = "pop"
            events = {
                1: ("pop", "PvE"),
                2: ("pop", "PvP"),
                3: ("test", "TEST"),
                4: ("requeued", "PvE"),
            }
            if event_code not in events:
                continue
            state, kind = events[event_code]
            sequence = _six_bit(values[5])
            checksum = _six_bit(values[6])
            if sequence is None or checksum is None:
                continue
            if checksum != (SIGNAL_PROTOCOL + 7 + event_code + sequence + 37) % 64:
                continue
            return {"state": state, "kind": kind, "sequence": sequence, "name": ""}
    return None


def send_pushover(config: dict, title: str, message: str, language: str = "en") -> str:
    texts = TEXTS.get(language, TEXTS["en"])
    priority = 0 if config.get("pushover_priority") == 0 else 1
    parameters = {
        "token": config["pushover_app_token"].strip(),
        "user": config["pushover_user_key"].strip(),
        "title": title,
        "message": message,
        "priority": priority,
        "sound": "siren",
    }
    payload = urllib.parse.urlencode(parameters).encode("utf-8")
    request = urllib.request.Request("https://api.pushover.net/1/messages.json", data=payload)
    with urllib.request.urlopen(request, timeout=15) as response:
        body = response.read().decode("utf-8", errors="replace")
        if response.status != 200:
            raise RuntimeError(f"Pushover HTTP {response.status}")
    try:
        result = json.loads(body)
    except ValueError as exc:
        raise RuntimeError(texts["invalid_response"]) from exc
    if result.get("status") != 1:
        errors = ", ".join(result.get("errors", [])) or texts["unknown_api_error"]
        raise RuntimeError(texts["pushover_rejected"].format(error=errors))
    return str(result.get("request", "ohne Request-ID"))


def validate_pushover(config: dict, language: str = "en") -> tuple[str, str]:
    """Validate Pushover credentials without sending a notification."""
    texts = TEXTS.get(language, TEXTS["en"])
    payload = urllib.parse.urlencode({
        "token": config["pushover_app_token"].strip(),
        "user": config["pushover_user_key"].strip(),
    }).encode("utf-8")
    request = urllib.request.Request("https://api.pushover.net/1/users/validate.json", data=payload)
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            body = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            result = json.loads(body)
            error = ", ".join(result.get("errors", [])) or f"HTTP {exc.code}"
        except ValueError:
            error = f"HTTP {exc.code}"
        return "invalid", error
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return "unavailable", str(exc)
    try:
        result = json.loads(body)
    except ValueError:
        return "unavailable", texts["invalid_response"]
    if result.get("status") == 1:
        return "valid", ""
    error = ", ".join(result.get("errors", [])) or texts["unknown_api_error"]
    return "invalid", error


class CompanionApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Queue Pop Notifier")
        self.geometry("410x260")
        self.minsize(400, 1)
        self.resizable(False, False)
        if ICON_PATH.exists():
            try:
                self.iconbitmap(default=str(ICON_PATH))
            except tk.TclError:
                pass
        self.config_data = load_config()
        if self.config_data.get("start_with_windows", False):
            set_windows_startup(True)
        self.is_configured = bool(
            self.config_data["pushover_user_key"] and self.config_data["pushover_app_token"])
        if self.is_configured:
            self.withdraw()
        configured_language = self.config_data.get("language", "auto")
        self.language = windows_language() if configured_language == "auto" else configured_language
        if self.language not in TEXTS:
            self.language = "en"
        self.messages: queue.Queue[tuple[str, str]] = queue.Queue()
        self.validation_results: queue.Queue[tuple[int, str, str]] = queue.Queue()
        self.validation_generation = 0
        self.pushover_validation_state = "unverified" if self.is_configured else "not_configured"
        self.stop_event = threading.Event()
        self.worker = None
        self.tray_icon = None
        self.last_sent = None
        self.stable_key = None
        self.stable_count = 0
        self.wow_available = False
        self.last_history_text = None
        self.history_entries = []
        self.available_version = None
        self.update_asset_url = None
        self.update_checksum_url = None
        self.update_in_progress = False
        self._build_ui()
        if self.is_configured:
            self.after(150, self._validate_pushover_async)
        self._fit_window_height()
        self.after(0, self._disable_maximize_button)
        self.after(100, self._drain_messages)
        self.protocol("WM_DELETE_WINDOW", self._hide_window)
        self.bind("<Unmap>", self._on_window_unmap, add="+")
        self._start_tray()
        self._start_monitoring()
        if not self.is_configured:
            self.after(100, self._open_settings)
        if GITHUB_REPOSITORY:
            self.after(1000, self._check_for_updates)

    def _t(self, key, **values):
        return TEXTS[self.language][key].format(**values)

    def _set_language_combo(self):
        values = [self._t("language_auto"), self._t("language_de"), self._t("language_en")]
        self.language_combo.configure(values=values)
        configured = self.config_data.get("language", "auto")
        index = {"auto": 0, "de": 1, "en": 2}.get(configured, 0)
        self.language_var.set(values[index])

    def _set_priority_combo(self):
        values = [self._t("priority_normal"), self._t("priority_high")]
        self.priority_combo.configure(values=values)
        priority = int(self.config_data.get("pushover_priority", 1))
        index = 0 if priority == 0 else 1
        self.priority_var.set(values[index])

    def _refresh_language(self):
        """Apply the selected language to every persistent UI element."""
        self.heading_label.configure(text=self._t("settings_title"))
        self.pushover_intro_label.configure(text=self._t("pushover_intro"))
        self.user_help_label.configure(text=self._t("user_key_help"))
        self.token_help_label.configure(text=self._t("app_token_help"))
        self.pushover_help_label.configure(text=self._t("pushover_help"))
        self.notifications_intro_label.configure(text=self._t("notifications_intro"))
        self.general_label.configure(text=self._t("general"))
        self.language_label.configure(text=self._t("language"))
        self.priority_label.configure(text=self._t("priority"))
        self.start_with_windows_check.configure(text=self._t("start_with_windows"))
        self.test_button.configure(text=self._t("test_pushover"))
        self.save_button.configure(text=self._t("save"))
        self._update_eye_button("user")
        self._update_eye_button("token")
        configured = bool(self.config_data["pushover_user_key"] and self.config_data["pushover_app_token"])
        self._set_pushover_state(self.pushover_validation_state if configured else "not_configured")
        self._set_language_combo()
        self._set_priority_combo()
        self._update_priority_help()
        self._restart_tray()
        self._fit_window_height()

    def _disable_maximize_button(self):
        """Entfernt unter Windows die Maximieren-Funktion der Titelleiste."""
        if os.name != "nt":
            return
        try:
            user32.GetParent.argtypes = [wintypes.HWND]
            user32.GetParent.restype = wintypes.HWND
            hwnd = user32.GetParent(wintypes.HWND(self.winfo_id()))
            get_window_long = user32.GetWindowLongPtrW
            set_window_long = user32.SetWindowLongPtrW
            get_window_long.argtypes = [wintypes.HWND, ctypes.c_int]
            get_window_long.restype = ctypes.c_ssize_t
            set_window_long.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]
            set_window_long.restype = ctypes.c_ssize_t
            user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT]
            user32.SetWindowPos.restype = wintypes.BOOL
            style = get_window_long(hwnd, -16)  # GWL_STYLE
            # Fixed settings window: no minimize, maximize or resize controls.
            set_window_long(hwnd, -16, style & ~0x00020000 & ~0x00010000 & ~0x00040000)
            user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0027)
        except (AttributeError, OSError):
            pass

    def _build_ui(self):
        self.configure(bg="#e7e7e7")
        self.geometry("570x620")
        self.minsize(570, 1)
        bg, card, border = "#e7e7e7", "#f3f3f3", "#cccccc"
        fg, muted, green, accent = "#202020", "#666666", "#287a3e", "#1769aa"
        self._ui_colors = {"muted": muted, "green": green, "warning": "#9a6500", "error": "#b3261e"}

        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Dark.TEntry", fieldbackground="#ffffff", foreground=fg,
                        insertcolor=fg, bordercolor=border, lightcolor=border, darkcolor=border,
                        padding=(9, 7))
        style.configure("Dark.TCombobox", fieldbackground="#ffffff", background="#dddddd",
                        foreground=fg, arrowcolor=fg, bordercolor=border, lightcolor=border,
                        darkcolor=border, padding=(8, 6))
        style.map("Dark.TCombobox", fieldbackground=[("readonly", "#ffffff")],
                  foreground=[("readonly", fg)], selectbackground=[("readonly", "#ffffff")])
        style.configure("Dark.TCheckbutton", background=card, foreground=fg, font=("Segoe UI", 9))
        style.map("Dark.TCheckbutton", background=[("active", card)], foreground=[("active", fg)])
        style.configure("Secondary.TButton", background="#e2e2e2", foreground=fg,
                        bordercolor="#bdbdbd", padding=(12, 7), font=("Segoe UI", 9))
        style.map("Secondary.TButton", background=[("active", "#d5d5d5")])
        style.configure("Primary.TButton", background="#3977bd", foreground="#ffffff",
                        bordercolor="#3977bd", padding=(15, 7), font=("Segoe UI", 9, "bold"))
        style.map("Primary.TButton", background=[("active", "#4788d1")])

        root = tk.Frame(self, bg=bg, padx=14, pady=14)
        root.pack(fill="both", expand=True)
        header = tk.Frame(root, bg=bg)
        header.pack(fill="x", padx=4, pady=(0, 13))
        self.heading_label = tk.Label(header, text=self._t("settings_title"), bg=bg, fg=fg,
                                      font=("Segoe UI", 15, "bold"))
        self.heading_label.pack(anchor="w")

        def card_frame():
            shell = tk.Frame(root, bg=border, padx=1, pady=1)
            shell.pack(fill="x", pady=(0, 10))
            body = tk.Frame(shell, bg=card, padx=16, pady=14)
            body.pack(fill="both")
            return body

        self.settings_frame = card_frame()
        top = tk.Frame(self.settings_frame, bg=card)
        top.grid(row=0, column=0, columnspan=2, sticky="ew")
        tk.Label(top, text="Pushover", bg=card, fg=fg, font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.pushover_intro_label = tk.Label(top, text=self._t("pushover_intro"), bg=card, fg=muted,
                                             font=("Segoe UI", 8))
        self.pushover_intro_label.pack(anchor="w", pady=(2, 0))
        configured = bool(self.config_data["pushover_user_key"] and self.config_data["pushover_app_token"])
        self.pushover_state = tk.Label(top, bg=card, fg=muted, font=("Segoe UI", 8),
                                       text=self._t("credentials_unverified") if configured else self._t("not_configured"))
        self.pushover_state.place(relx=1.0, x=0, y=2, anchor="ne")

        tk.Label(self.settings_frame, text="User Key", bg=card, fg=fg,
                 font=("Segoe UI", 9, "bold")).grid(row=1, column=0, columnspan=2, sticky="w", pady=(14, 0))
        self.user_help_label = tk.Label(self.settings_frame, text=self._t("user_key_help"), bg=card, fg=muted,
                                        font=("Segoe UI", 8))
        self.user_help_label.grid(row=2, column=0, columnspan=2, sticky="w", pady=(1, 6))
        self.user_var = tk.StringVar(value=self.config_data["pushover_user_key"])
        self.user_entry = ttk.Entry(self.settings_frame, textvariable=self.user_var, show="•", style="Dark.TEntry")
        self.user_entry.grid(row=3, column=0, sticky="ew")
        self.user_eye = tk.Button(self.settings_frame, text="\ue7b3", width=3, relief="flat", bd=0,
                                  bg=card, fg=muted, activebackground="#dddddd", activeforeground=accent,
                                  cursor="hand2", font=("Segoe MDL2 Assets", 11),
                                  command=lambda: self._toggle_secret("user"))
        self.user_eye.grid(row=3, column=1, padx=(7, 0))
        tk.Label(self.settings_frame, text="App/API Token", bg=card, fg=fg,
                 font=("Segoe UI", 9, "bold")).grid(row=4, column=0, columnspan=2, sticky="w", pady=(13, 0))
        self.token_help_label = tk.Label(self.settings_frame, text=self._t("app_token_help"), bg=card, fg=muted,
                                         font=("Segoe UI", 8))
        self.token_help_label.grid(row=5, column=0, columnspan=2, sticky="w", pady=(1, 6))
        self.token_var = tk.StringVar(value=self.config_data["pushover_app_token"])
        self.token_entry = ttk.Entry(self.settings_frame, textvariable=self.token_var, show="•", style="Dark.TEntry")
        self.token_entry.grid(row=6, column=0, sticky="ew")
        self.token_eye = tk.Button(self.settings_frame, text="\ue7b3", width=3, relief="flat", bd=0,
                                   bg=card, fg=muted, activebackground="#dddddd", activeforeground=accent,
                                   cursor="hand2", font=("Segoe MDL2 Assets", 11),
                                   command=lambda: self._toggle_secret("token"))
        self.token_eye.grid(row=6, column=1, padx=(7, 0))
        self.pushover_help_label = tk.Label(self.settings_frame, text=self._t("pushover_help"), bg=card,
                                            fg=accent, cursor="hand2", font=("Segoe UI", 8, "underline"))
        self.pushover_help_label.grid(row=7, column=0, columnspan=2, sticky="w", pady=(11, 0))
        self.pushover_help_label.bind("<Button-1>", lambda _event: webbrowser.open("https://pushover.net/apps/build"))
        self.settings_frame.columnconfigure(0, weight=1)

        notification_card = card_frame()
        tk.Label(notification_card, text=self._t("notifications"), bg=card, fg=fg,
                 font=("Segoe UI", 11, "bold")).grid(row=0, column=0, columnspan=2, sticky="w")
        self.notifications_intro_label = tk.Label(notification_card, text=self._t("notifications_intro"),
                                                   bg=card, fg=muted, font=("Segoe UI", 8))
        self.notifications_intro_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=(2, 12))
        self.priority_label = tk.Label(notification_card, text=self._t("priority"), bg=card, fg=fg,
                                       font=("Segoe UI", 9, "bold"))
        self.priority_label.grid(row=2, column=0, sticky="w")
        self.priority_help_label = tk.Label(notification_card, text="", bg=card, fg=muted,
                                            justify="left", wraplength=310, font=("Segoe UI", 8))
        self.priority_help_label.grid(row=2, column=1, rowspan=2, sticky="sw", padx=(18, 0))
        self.language_var = tk.StringVar()
        self.priority_var = tk.StringVar()
        self.priority_combo = ttk.Combobox(notification_card, textvariable=self.priority_var,
                                           state="readonly", width=18, style="Dark.TCombobox")
        self.priority_combo.grid(row=3, column=0, sticky="w", pady=(5, 0))
        self._set_priority_combo()
        self.priority_combo.bind("<<ComboboxSelected>>", lambda _event: self._update_priority_help())
        self._update_priority_help()

        general_card = card_frame()
        self.general_label = tk.Label(general_card, text=self._t("general"), bg=card, fg=fg,
                                      font=("Segoe UI", 11, "bold"))
        self.general_label.grid(row=0, column=0, sticky="w")
        self.start_with_windows_var = tk.BooleanVar(
            value=bool(self.config_data.get("start_with_windows", False))
        )
        self.start_with_windows_check = ttk.Checkbutton(
            general_card,
            text=self._t("start_with_windows"),
            variable=self.start_with_windows_var,
            style="Dark.TCheckbutton",
        )
        self.start_with_windows_check.grid(row=1, column=0, sticky="w", pady=(10, 0))
        self.language_label = tk.Label(general_card, text=self._t("language"), bg=card, fg=fg,
                                       font=("Segoe UI", 9, "bold"))
        self.language_label.grid(row=0, column=1, sticky="w", padx=(30, 0))
        self.language_combo = ttk.Combobox(general_card, textvariable=self.language_var,
                                           state="readonly", width=22, style="Dark.TCombobox")
        self.language_combo.grid(row=1, column=1, sticky="e", padx=(30, 0), pady=(5, 0))
        self._set_language_combo()
        general_card.columnconfigure(0, weight=1)

        actions = tk.Frame(root, bg=bg)
        actions.pack(fill="x", pady=(2, 0))
        self.test_button = ttk.Button(actions, text=self._t("test_pushover"), style="Secondary.TButton",
                                      command=self._test_push)
        self.test_button.pack(side="left", padx=(0, 8))
        self.save_button = ttk.Button(actions, text=self._t("save"), style="Primary.TButton", command=self._save)
        self.save_button.pack(side="right")
        self.user_var.trace_add("write", self._credentials_changed)
        self.token_var.trace_add("write", self._credentials_changed)

    def _update_priority_help(self):
        key = "priority_normal_help" if self.priority_var.get() == self._t("priority_normal") else "priority_high_help"
        self.priority_help_label.configure(text=self._t(key))

    def _set_pushover_state(self, state):
        self.pushover_validation_state = state
        styles = {
            "valid": ("active_ready", self._ui_colors["green"]),
            "invalid": ("credentials_invalid", self._ui_colors["error"]),
            "unavailable": ("credentials_unavailable", self._ui_colors["warning"]),
            "checking": ("credentials_checking", self._ui_colors["muted"]),
            "unverified": ("credentials_unverified", self._ui_colors["muted"]),
            "not_configured": ("not_configured", self._ui_colors["muted"]),
        }
        key, color = styles[state]
        self.pushover_state.configure(text=self._t(key), fg=color)

    def _credentials_changed(self, *_args):
        self.validation_generation += 1
        configured = bool(self.user_var.get().strip() and self.token_var.get().strip())
        self._set_pushover_state("unverified" if configured else "not_configured")

    def _toggle_secret(self, which):
        """Blendet User Key oder Token ein und wieder aus."""
        entry = self.user_entry if which == "user" else self.token_entry
        visible = entry.cget("show") == ""
        entry.configure(show="•" if visible else "")
        self._update_eye_button(which)

    def _update_eye_button(self, which):
        """Hebt das Auge dezent hervor, solange der jeweilige Schlüssel sichtbar ist."""
        entry = self.user_entry if which == "user" else self.token_entry
        button = self.user_eye if which == "user" else self.token_eye
        button.configure(fg="#1769aa" if entry.cget("show") == "" else self._ui_colors["muted"])

    def _open_settings(self):
        self._show_window()

    def _fit_window_height(self):
        """Passt die feste Fensterhöhe ohne ungenutzten Leerraum an den Inhalt an."""
        self.update_idletasks()
        wanted_height = self.winfo_reqheight()
        self.minsize(570, wanted_height)
        self.geometry(f"570x{wanted_height}")

    def _current_config(self):
        self.config_data["pushover_user_key"] = self.user_var.get().strip()
        self.config_data["pushover_app_token"] = self.token_var.get().strip()
        selected = self.language_var.get()
        language_values = {
            self._t("language_auto"): "auto", self._t("language_de"): "de", self._t("language_en"): "en",
        }
        self.config_data["language"] = language_values.get(selected, "auto")
        priority_values = {
            self._t("priority_normal"): 0, self._t("priority_high"): 1,
        }
        self.config_data["pushover_priority"] = priority_values.get(self.priority_var.get(), 1)
        self.config_data["start_with_windows"] = bool(self.start_with_windows_var.get())
        return self.config_data

    def _save(self):
        save_config(self._current_config())
        set_windows_startup(self.config_data.get("start_with_windows", False))
        configured = bool(self.config_data["pushover_user_key"] and self.config_data["pushover_app_token"])
        requested = self.config_data.get("language", "auto")
        self.language = windows_language() if requested == "auto" else requested
        self._refresh_language()
        if configured:
            self._validate_pushover_async()
        else:
            self._set_pushover_state("not_configured")
        self.save_button.configure(text=self._t("saved"))
        if getattr(self, "save_feedback_job", None):
            self.after_cancel(self.save_feedback_job)
        self.save_feedback_job = self.after(
            1800, lambda: self.save_button.configure(text=self._t("save"))
        )

    def _validate_pushover_async(self):
        config = dict(self._current_config())
        if not config["pushover_user_key"] or not config["pushover_app_token"]:
            self._set_pushover_state("not_configured")
            return
        self.validation_generation += 1
        generation = self.validation_generation
        self._set_pushover_state("checking")
        threading.Thread(
            target=self._validation_worker, args=(generation, config, self.language), daemon=True
        ).start()

    def _validation_worker(self, generation, config, language):
        state, detail = validate_pushover(config, language)
        self.validation_results.put((generation, state, detail))

    def _save_silent(self):
        save_config(self._current_config())

    def _test_push(self):
        config = dict(self._current_config())
        if not config["pushover_user_key"] or not config["pushover_app_token"]:
            messagebox.showwarning(self._t("missing_title"), self._t("missing_message"))
            return
        threading.Thread(target=self._send_and_report, args=(config, self._t("connection_test"), self._t("connection_test_message")), daemon=True).start()

    def _send_and_report(self, config, title, message):
        last_error = None
        for attempt in range(1, 4):
            try:
                send_pushover(config, title, message, self.language)
                self.messages.put(("status", self._t("pushover_connected")))
                return
            except Exception as exc:
                last_error = exc
                if attempt < 3:
                    time.sleep(2 * attempt)
        self.messages.put(("error", self._t("pushover_failed", error=last_error)))

    def _start_monitoring(self):
        if os.name != "nt":
            self._set_status("error", self._t("windows_required"))
            return
        self._save_silent()
        self.worker = threading.Thread(target=self._monitor, daemon=True)
        self.worker.start()

    def _monitor(self):
        missing_reported = False
        found_reported = False
        capture_error_reported = False
        while not self.stop_event.is_set():
            hwnd, _ = find_wow_window()
            if not hwnd:
                if not missing_reported:
                    self.messages.put(("waiting", self._t("wow_missing_event")))
                    missing_reported = True
                    found_reported = False
                time.sleep(1)
                continue
            missing_reported = False
            if not found_reported:
                self.messages.put(("ready", self._t("wow_ready_event")))
                found_reported = True
            try:
                x, y = client_origin(hwnd)
                decoded = decode_signal(capture_region(x, y, 180, 30))
                if capture_error_reported:
                    self.messages.put(("ready", self._t("capture_restored")))
                    capture_error_reported = False
                self._handle_decoded(decoded)
            except Exception as exc:
                if not capture_error_reported:
                    error_text = str(exc)
                    if "ClientToScreen" in error_text:
                        error_text = self._t("client_to_screen_failed")
                    elif "Bildschirmaufnahme" in error_text:
                        error_text = self._t("capture_error")
                    self.messages.put(("error", self._t("capture_failed", error=error_text)))
                    capture_error_reported = True
            time.sleep(max(0.1, self.config_data["scan_interval_ms"] / 1000))

    def _handle_decoded(self, decoded):
        if decoded is None:
            self.stable_key, self.stable_count = None, 0
            return
        if decoded.get("error") == "incompatible":
            protocol = decoded.get("protocol")
            detail = self._t("unreadable") if protocol is None else str(protocol)
            self.messages.put(("error", self._t("incompatible", protocol=detail, required=SIGNAL_PROTOCOL)))
            self.stable_key, self.stable_count = None, 0
            return
        key = (decoded["state"], decoded["kind"], decoded["sequence"], decoded["name"])
        if key == self.stable_key:
            self.stable_count += 1
        else:
            self.stable_key, self.stable_count = key, 1
        if decoded["state"] not in ("pop", "test", "requeued") or self.stable_count < self.config_data["confirm_frames"] or key == self.last_sent:
            return
        self.last_sent = key
        destination = decoded["name"].strip()
        if decoded["state"] == "test":
            title = self._t("test_success")
            message = self._t("test_success_message")
            status = self._t("test_detected")
        elif decoded["state"] == "requeued":
            title = self._t("requeued_title")
            message = self._t("requeued_message")
            status = self._t("requeued_detected")
        else:
            title = self._t("queue_ready_named", name=destination) if destination else self._t("queue_ready_kind", kind=decoded["kind"])
            message = self._t("confirm_in_wow")
            status = self._t("queue_detected")
        self.messages.put(("status", status))
        config = dict(self.config_data)
        if config["pushover_user_key"] and config["pushover_app_token"]:
            threading.Thread(target=self._send_and_report, args=(config, title, message), daemon=True).start()
        else:
            self.messages.put(("error", self._t("queue_no_pushover")))

    def _drain_messages(self):
        try:
            while True:
                kind, text = self.messages.get_nowait()
                self._set_status(kind, text)
        except queue.Empty:
            pass
        try:
            while True:
                generation, state, _detail = self.validation_results.get_nowait()
                if generation == self.validation_generation:
                    self._set_pushover_state(state)
        except queue.Empty:
            pass
        self.after(100, self._drain_messages)

    def _set_status(self, kind, text):
        self._add_history(text)
        self.current_status_kind = kind
        self.current_status_text = text
        if kind == "waiting":
            self.wow_available = False
        elif kind == "ready":
            self.wow_available = True
        if self.tray_icon:
            try:
                self.tray_icon.update_menu()
            except Exception:
                pass

    def _add_history(self, text):
        """Keep a short internal event history without cluttering the settings window."""
        if text == self.last_history_text:
            return
        self.last_history_text = text
        self.history_entries.insert(0, (time.strftime("%H:%M:%S"), text))
        self.history_entries = self.history_entries[:4]

    def _start_tray(self):
        try:
            import pystray
            from PIL import Image
            image = Image.open(ICON_PATH)
            menu = pystray.Menu(
                pystray.MenuItem(lambda _item: self._tray_status_text(), lambda *_: None),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(self._t("tray_settings"), lambda *_: self.after(0, self._open_settings), default=True),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(self._t("tray_version", version=APP_VERSION), None, enabled=False),
                pystray.MenuItem(self._t("tray_quit"), lambda *_: self.after(0, self._quit_app)),
            )
            self.tray_icon = pystray.Icon("QueuePopNotifier", image, "Queue Pop Notifier", menu)
            self.tray_icon.run_detached()
        except Exception:
            self.tray_icon = None

    def _tray_status_text(self):
        if self.update_in_progress:
            return self._t(
                "tray_status",
                indicator="↻",
                status=getattr(
                    self, "current_status_text",
                    self._t("update_downloading", version=self.available_version),
                ),
            )
        kind = getattr(self, "current_status_kind", None)
        if kind == "error":
            indicator = "!"
            status = self._t("check_disturbed")
        elif kind == "waiting":
            indicator = "…"
            status = self._t("client_searching")
        elif kind is None:
            indicator = "…"
            status = self._t("client_started")
        elif not self.wow_available:
            indicator = "…"
            status = self._t("client_searching")
        else:
            indicator = "✓"
            status = self._t("monitoring_active")
        return self._t("tray_status", indicator=indicator, status=status)

    @staticmethod
    def _version_tuple(value):
        try:
            return tuple(int(part) for part in value.strip().lstrip("vV").split("."))
        except (AttributeError, ValueError):
            return ()

    def _check_for_updates(self):
        threading.Thread(target=self._update_worker, daemon=True).start()

    def _update_worker(self):
        try:
            api_url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/releases/latest"
            request = urllib.request.Request(api_url, headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": f"QueuePopNotifier/{APP_VERSION}",
            })
            with urllib.request.urlopen(request, timeout=10) as response:
                release = json.loads(response.read().decode("utf-8"))
            latest = str(release.get("tag_name", "")).lstrip("vV")
            if not self._version_tuple(latest):
                raise RuntimeError("invalid release version")
            if self._version_tuple(latest) > self._version_tuple(APP_VERSION):
                assets = release.get("assets") or []
                exe_asset = next(
                    (asset for asset in assets if str(asset.get("name", "")).lower() == "queuepopnotifier.exe"),
                    None,
                )
                checksum_asset = next(
                    (asset for asset in assets if str(asset.get("name", "")).lower() == "queuepopnotifier.exe.sha256"),
                    None,
                )
                self.available_version = latest
                self.update_asset_url = exe_asset.get("browser_download_url") if exe_asset else None
                self.update_checksum_url = checksum_asset.get("browser_download_url") if checksum_asset else None
                self.after(0, self._start_automatic_update)
        except Exception:
            # Startup checks are intentionally silent. A temporary network or
            # GitHub failure must not interrupt the notifier.
            pass

    def _start_automatic_update(self):
        if self.update_in_progress:
            return
        if not getattr(sys, "frozen", False) or os.name != "nt":
            return
        if not self.update_asset_url or not self.update_checksum_url:
            return
        self.update_in_progress = True
        self._set_status("status", self._t("update_downloading", version=self.available_version))
        self._notify_tray(
            self._t("update_notice_title"),
            self._t("update_downloading", version=self.available_version),
        )
        threading.Thread(target=self._download_update_worker, daemon=True).start()

    def _notify_tray(self, title, message):
        if not self.tray_icon:
            return
        try:
            self.tray_icon.notify(message, title)
        except Exception:
            pass

    def _download_update_worker(self):
        try:
            headers = {"User-Agent": f"QueuePopNotifier/{APP_VERSION}"}
            checksum_request = urllib.request.Request(self.update_checksum_url, headers=headers)
            with urllib.request.urlopen(checksum_request, timeout=20) as response:
                checksum_text = response.read(4096).decode("ascii", errors="strict").strip()
            expected_hash = checksum_text.split()[0].lower()
            if len(expected_hash) != 64 or any(char not in "0123456789abcdef" for char in expected_hash):
                raise RuntimeError(self._t("update_checksum_failed"))

            update_dir = Path(tempfile.mkdtemp(prefix="QueuePopNotifier-update-"))
            downloaded_exe = update_dir / "QueuePopNotifier.exe"
            digest = hashlib.sha256()
            exe_request = urllib.request.Request(self.update_asset_url, headers=headers)
            with urllib.request.urlopen(exe_request, timeout=60) as response, downloaded_exe.open("wb") as output:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    output.write(chunk)
                    digest.update(chunk)
            if digest.hexdigest().lower() != expected_hash:
                raise RuntimeError(self._t("update_checksum_failed"))

            updater_script = update_dir / "install-update.ps1"
            updater_script.write_text(
                """param([int]$CurrentPid, [string]$Source, [string]$Target)
$ErrorActionPreference = 'Stop'
$backup = "$Target.old"
$mutex = New-Object System.Threading.Mutex($false, 'Local\\QueuePopNotifier.Update')
$hasMutex = $false
try {
  $hasMutex = $mutex.WaitOne(0)
  if (-not $hasMutex) { exit 0 }

  $deadline = [DateTime]::UtcNow.AddSeconds(60)
  while (Get-Process -Id $CurrentPid -ErrorAction SilentlyContinue) {
    if ([DateTime]::UtcNow -ge $deadline) {
      throw 'Der bisherige Client konnte nicht beendet werden.'
    }
    Start-Sleep -Milliseconds 200
  }

  if (Test-Path -LiteralPath $backup) { Remove-Item -LiteralPath $backup -Force }
  Move-Item -LiteralPath $Target -Destination $backup -Force
  try {
    Move-Item -LiteralPath $Source -Destination $Target -Force
    $newProcess = Start-Process -FilePath $Target -PassThru
    Start-Sleep -Seconds 3
    if ($newProcess.HasExited) { throw 'Der aktualisierte Client wurde unerwartet beendet.' }
    Remove-Item -LiteralPath $backup -Force -ErrorAction Stop
  } catch {
    if ($newProcess -and -not $newProcess.HasExited) {
      Stop-Process -Id $newProcess.Id -Force -ErrorAction SilentlyContinue
      $newProcess.WaitForExit(5000) | Out-Null
    }
    if (Test-Path -LiteralPath $Target) { Remove-Item -LiteralPath $Target -Force }
    Move-Item -LiteralPath $backup -Destination $Target -Force
    Start-Process -FilePath $Target
    throw
  }
} catch {
  Add-Type -AssemblyName PresentationFramework
  [System.Windows.MessageBox]::Show("Update fehlgeschlagen: $($_.Exception.Message)", 'Queue Pop Notifier') | Out-Null
} finally {
  if ($hasMutex) { $mutex.ReleaseMutex() }
  $mutex.Dispose()
}
""",
                encoding="utf-8-sig",
            )
            self.after(0, lambda: self._launch_updater(updater_script, downloaded_exe))
        except Exception as exc:
            self.after(0, lambda error=str(exc): self._update_install_failed(error))

    def _launch_updater(self, updater_script, downloaded_exe):
        try:
            target_exe = Path(sys.executable).resolve()
            creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            self._show_update_notice()
            subprocess.Popen(
                [
                    "powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                    "-File", str(updater_script), "-CurrentPid", str(os.getpid()),
                    "-Source", str(downloaded_exe), "-Target", str(target_exe),
                ],
                close_fds=True,
                creationflags=creation_flags,
            )
            self._set_status("status", self._t("update_installing"))
            self._notify_tray(
                self._t("update_notice_title"),
                self._t("update_notice_message", version=self.available_version),
            )
            self._terminate_for_update()
        except Exception as exc:
            self._update_install_failed(str(exc))

    def _show_update_notice(self):
        """Show a foreground notice that cannot disappear with a hidden tray window."""
        title = self._t("update_notice_title")
        message = self._t("update_notice_message", version=self.available_version)
        if os.name == "nt":
            # MB_OK | MB_ICONINFORMATION | MB_SYSTEMMODAL | MB_SETFOREGROUND
            ctypes.windll.user32.MessageBoxW(None, message, title, 0x00000040 | 0x00001000 | 0x00010000)
        else:
            messagebox.showinfo(title, message)

    def _terminate_for_update(self):
        """Guarantee that no Python or tray thread keeps the old executable alive."""
        self.stop_event.set()
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
        try:
            self.destroy()
        finally:
            os._exit(0)

    def _update_install_failed(self, error):
        self.update_in_progress = False
        messagebox.showerror(
            self._t("update_install_failed_title"),
            self._t("update_install_failed_message", error=error),
        )

    def _restart_tray(self):
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None
        self._start_tray()

    def _hide_window(self):
        if self.tray_icon:
            self.withdraw()
        else:
            self.iconify()

    def _on_window_unmap(self, _event=None):
        # Das normale Minimieren-Symbol der Titelleiste führt direkt in den Tray.
        if self.tray_icon:
            self.after(20, self._hide_if_iconic)

    def _hide_if_iconic(self):
        if self.state() == "iconic" and self.tray_icon:
            self.withdraw()

    def _show_window(self):
        self.deiconify()
        self.lift()
        self.focus_force()

    def _quit_app(self):
        self.stop_event.set()
        if self.tray_icon:
            self.tray_icon.stop()
        self.destroy()


if __name__ == "__main__":
    _instance_mutex = acquire_single_instance()
    if _instance_mutex is False:
        raise SystemExit(0)
    remove_stale_backup()
    try:
        CompanionApp().mainloop()
    finally:
        if os.name == "nt" and _instance_mutex:
            ctypes.windll.kernel32.CloseHandle(_instance_mutex)
