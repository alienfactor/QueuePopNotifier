"""Queue Pop Notifier – desktop client 0.4.0."""
from __future__ import annotations

import base64
import ctypes
from ctypes import wintypes
import hashlib
import json
import io
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

from PIL import Image, ImageOps, ImageTk

if os.name == "nt":
    import winreg

APP_VERSION = "0.4.0"
SIGNAL_PROTOCOL = 2
GITHUB_REPOSITORY = "alienfactor/QueuePopNotifier"
APP_DIR = Path(os.environ.get("APPDATA", Path.home())) / "QueuePopNotifier"
CONFIG_PATH = APP_DIR / "config.json"
CONFIG_BACKUP_PATH = APP_DIR / "config.backup.json"
ICON_PATH = Path(__file__).with_name("queuepop_notifier.ico")

PUSHOVER_SERVICE_ICON_B64 = """iVBORw0KGgoAAAANSUhEUgAAACoAAAAqCAYAAADFw8lbAAAHZklEQVR42u2YaYyVVxnHf885711mtcMqDBEodLAMxVKq4hIntU3NaGKo5g40NXFrrCC1MZpGg+EOwZiSqGl1iEZtmpgS60xNbGwaaF06gFJNq7TMgAilTtkHsNMZZrn3vu95/HDeO0vnDlyQWD/wfLsz7znnf/7n/6xwza7Z/7fJf7+FSqYd09vt9+psRAGa4t+zGtGODA4RfXuuqCpNWQ3K/TzTrpasmis9LriSRZl2tR0iUSeE8x/TdG3E+4hYJfBuVTcTNYLhDYSjIryYcOztaJFzo2uvgGG5XBZpRdgsbsmPdG4qzTrgbrEsMglAQePjRfzuGoErcA7ht5pn2/718hIAWTVsFnf1gY7beNlP9H4TsMmmmeFGwIU4FIcAGu8pqFcrYizWpCHKEanjZ/1DfKvna9KXaVfb0SLR1QMag1yyVWuSdfwiqGS1GwYXEopggAnaMxIzimcZT3SkijXViBvmUCHH2gMbZF+5YKWs5wau30ptdR07gipWFQYoCATIxPVWIFIYDmEk9OgkPsUaqExA0lAgScJF9OUHaf7HA/ICGbV0XByslBN6OoBl59mZqOH2cICCCAnGEWYFHNCfg7SB5bPgw++ChulKZQBnBoW/nVJ2HxNODkJNklACAufcuVxo3ntoHT1kvfavCGjxWZa16XeSdWws9E8ECZ6poYIH+8kblC+thIV1cPAsdPVCLoLmRTC9Sjg/iD70J5XfHBaqE4RSQRBeYM/+MzRlDiAdF2FVLq5L9Ma2/NJEKrkPh6CY8WusgYEcLL4Ottym3FoPu3tg0/PC0T6YXQnXpeHkAPzyU8pN7/TetuZJ2NcrVFpCqSLI90f3dn8leLQpq0HnZglLwZkyAGcaERBNmORGmyZQ78MTQF7Iw00z4fG7PMgf7IX1zwj3rVSevUfZ+0Vl3Url2AV45shY6LprCeRCEIPRPGrEfnv+Y5rubCUClfKBZtV0tEj0nh9rvRpWR0OogB19BoF8BDMqoK1ZmV4lPLEfWncJLUth7TJhyQzBGvjVQaEy4ZkX8ZqeXuGlAhiXxwVVLKjO8XFEtCk7ds4lgTbFf3dKc1BJhSrReDaNeDY33KrMrRVe71O+94IwswpuX+g93ykc7IUD5yAdwKzqMbWdG/bfjMZbQY1jTbE2uKynjzf5yGgkfAub9TXwsUX+OZ86JJy4AA11sGKOj/hGYOdRf6G0hQ/UM6qdv5wQzNjJxhUQhFWLH9GUj6mTn78kUK8VULhBI2Q8mwLkHcyu8p7sFF7u9Qx9cJ5SkRAUKETK8z1CQeHm2cotc/3ao/9W/vAvqE6OsioaAsLcFMzz0qMcoCqIaFzpTFM3MTo4hZSFnjfhyHnFGp/grcCd148F/v1noPssVAXwjVVgjaCqtHbCUBQLPgaKQ8USOMsMAA4g5T/9KSw6MbCPz0BDIdz7tPDd3cKxAaFhGqyY4xkGeKJb6BuBh26DlfWCc/Dgc8Lu40Jt0l94FI6gYiGAlA85ZWk0Lr9+SijCSKlIqzGrZ4fh0Zeh6yzcsUBJxkVjfw4KETx7D6y+EQ6fVz73FDx5COrSELpJtxeNwAnDAHRcRngCUVFOigF0srpVIWH8wVUJuGPh2P9qU/D9O6EmCVs6lTW/Fv58wn8buUlZRjGIhuSA0wAsnez5wVThqROcw/3dWvNRhCmL3MECLHgHrJjjf0cONv4RXjwNx/thJBKqkx58VCKTK6gNkCjite6ZnAQolfNLMlqMZZEzO1zoo03J2Ca+UvrQPCUdq7mrF7Z3w/EBSAWeRUNpkEX/lASK0kmLRFO1NyUBdLTgQKUQHd7jhnnVJhB8gTShSlAgIcVn9w/63KsQGC8H1XEApXRlIWC0gIQh268g4PtUduSBhpwKD0sKUZ0IVPD5en4t3DLX/y0fKZ2vQzIowaC+NXWAKpFNY6IR9h78KnuKqfuyMlPnZiKyagbS/LwwwKG4MInGP/tQAd5fr6RiYK+chiNv+EzkLt26qRhUHYSOb4KoL4RK20VSqGjmANLzeRlRxxc0QsWiqO+KVCFpoKURjIhag/7uNSEX+UuUYYWgmiAc5uGDG2TXpVqSS25Z3KBxm65P1rItGiJEMQ5MysBnl0NF7Ejbu+DMICTsuDaklPcohUQNicIAO7um84nMqF9M3UKXdfdiQdu4TR9MVLPV5UFDQoSgPx/XmQrVKQiEkt4gsSYRCGqwhX634/xp8+lTrXGQv0SfX3a7XAS7tE3vDiposwmmhUNgJe5EFYm0BCW+4HYANo1VhSjPI12/5+t0SITGtcXVHEAUZdDwQ12YSrFFhLW2Auvy4AqAEmmcHKRY7QWISXrGozx/dTk2dd8vOyH+ssyJyWUPycaLfmmb3myTfEagWZUGmyIYdU8F9bI4jbCLiMdf+TJPg6jf4+KavDrTvKwaWgGJU11WzfJ6FhthcaTMQgkQ+qzSY+GfL90nb46ubVdLmdORq2dZNeVM9DLtajPtaqdq3P5H89G42M4imUakOCcdnZW+rbPRa3bNrtkk+w+fkVSQBUiGKwAAAABJRU5ErkJggg=="""
TELEGRAM_SERVICE_ICON_B64 = """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"""

NTFY_SERVICE_ICON_B64 = """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"""

DEFAULTS = {
    "pushover_user_key": "",
    "pushover_app_token": "",
    "scan_interval_ms": 250,
    "confirm_frames": 3,
    "language": "auto",
    "pushover_priority": 1,
    "ntfy_priority": 4,
    "ntfy_server": "https://ntfy.sh",
    "ntfy_topic": "",
    "ntfy_token": "",
    "telegram_bot_token": "",
    "telegram_chat_id": "",
    "default_service": "pushover",
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
        "priority": "Priorität", "priority_normal": "Normal (0)", "priority_high": "Hoch (1)",
        "ntfy_priority_default": "Standard (3)", "ntfy_priority_high": "Hoch (4)",
        "ntfy_priority_default_help": "Standardbenachrichtigung mit kurzer Vibration, normalem Ton und dem üblichen Benachrichtigungsverhalten.",
        "ntfy_priority_high_help": "Auffälligere Benachrichtigung mit längerer Vibration, normalem Ton und Pop-over-Anzeige.",
        "settings_title": "Einstellungen", "settings_subtitle": "Queue Pop Notifier",
        "services": "Dienste", "services_intro": "Wähle einen Dienst für Queue-Benachrichtigungen. Es kann nur ein Dienst gleichzeitig aktiv sein.",
        "pushover_intro": "Sendet Queue-Benachrichtigungen an dein Gerät über Pushover.",
        "user_key_help": "Dein persönlicher Empfängerschlüssel aus dem Pushover-Dashboard.",
        "app_token_help": "Der Token deiner Anwendung „Queue Pop Notifier“ bei Pushover.",
        "pushover_help": "Wo finde ich User Key und App-Token?  ↗",
        "ntfy_intro": "Sendet Queue-Benachrichtigungen an ein ntfy-Topic.",
        "ntfy_server": "Server-URL", "ntfy_server_help": "Standard: https://ntfy.sh – oder die URL deines eigenen ntfy-Servers.",
        "ntfy_topic": "Topic", "ntfy_topic_help": "Der eindeutige Topic-Name, den du in der ntfy-App abonnierst.",
        "ntfy_token": "Access Token (optional)", "ntfy_token_help": "Nur nötig, wenn dein Topic oder Server geschützt ist. Für normale öffentliche ntfy.sh-Topics leer lassen.",
        "ntfy_help": "ntfy-Dokumentation öffnen  ↗",
        "telegram_intro": "Sendet Queue-Benachrichtigungen über einen Telegram-Bot.",
        "telegram_bot_token": "Bot Token", "telegram_bot_token_help": "Den Bot-Token erhältst du beim BotFather in Telegram.",
        "telegram_chat_id": "Chat-ID", "telegram_chat_id_help": "Die numerische ID des privaten Chats oder der Gruppe, an die der Bot senden soll.",
        "telegram_help": "Telegram-Bot einrichten  ↗",
        "pushover_as_default": "Pushover als Standarddienst verwenden",
        "ntfy_as_default": "ntfy als Standarddienst verwenden", "telegram_as_default": "Telegram als Standarddienst verwenden", "disabled_service": "Deaktiviert",
        "configured_disabled": "Eingerichtet · deaktiviert", "incomplete_service": "Unvollständig", "service_error": "Fehlerhaft",
        "notifications_intro": "Lege fest, wie auffällig Queue-Meldungen erscheinen.",
        "priority_normal_help": "Standardbenachrichtigung mit Ton, Vibration und Hinweis gemäß den Geräteeinstellungen. Während festgelegter Ruhezeiten wird sie leise zugestellt.",
        "priority_high_help": "Umgeht die Pushover-Ruhezeiten und löst immer Ton und Vibration aus, sofern das Gerät entsprechend eingestellt ist. Wird in Pushover hervorgehoben.",
        "general": "Allgemein",
        "start_with_windows": "Mit Windows starten",
        "language_help": "Legt die Sprache der Benutzeroberfläche fest.",
        "start_with_windows_help": "Startet Queue Pop Notifier automatisch nach der Windows-Anmeldung.",
        "test_pushover": "Testnachricht senden", "test_service": "Dienst testen", "test_running": "Verbindung wird geprüft …", "test_ok": "Verbindung erfolgreich", "test_failed": "Test fehlgeschlagen: {error}", "save": "Speichern", "saved": "Gespeichert ✓",
        "tray_settings": "Einstellungen", "tray_report_issue": "Problem melden",
        "open_config_folder": "Konfigurationsordner öffnen",
        "tray_status": "{status}",
        "version": "Version {version} · Updates werden automatisch installiert",
        "update_install_failed_title": "Update fehlgeschlagen",
        "update_install_failed_message": "Das Update konnte nicht installiert werden: {error}",
        "update_checksum_failed": "Die Prüfsumme der heruntergeladenen EXE stimmt nicht.",
        "missing_title": "Dienst nicht eingerichtet", "missing_message": "{service} ist nicht vollständig eingerichtet. Bitte ergänze die erforderlichen Daten.",
        "connection_test": "Verbindungstest", "connection_test_message": "Queue Pop Notifier ist verbunden.",
        "pushover_connected": "Pushover verbunden · Benachrichtigungen sind bereit",
        "ntfy_connected": "ntfy verbunden · Benachrichtigungen sind bereit", "ntfy_failed": "ntfy fehlgeschlagen: {error}",
        "telegram_connected": "Telegram verbunden · Benachrichtigungen sind bereit", "telegram_failed": "Telegram fehlgeschlagen: {error}",
        "pushover_failed": "Pushover fehlgeschlagen: {error}", "windows_required": "Windows erforderlich",
        "wow_missing_event": "WoW nicht gefunden · Der Client wartet auf ein laufendes WoW-Fenster",
        "wow_ready_event": "WoW erkannt · Überwachung bereit",
        "capture_restored": "Bildschirmprüfung wiederhergestellt · Überwachung bereit",
        "capture_failed": "WoW konnte vorübergehend nicht geprüft werden: {error}",
        "incompatible": "Addon nicht kompatibel · Signalprotokoll {protocol}, benötigt wird {required}",
        "unreadable": "unlesbar", "test_success": "Test erfolgreich",
        "test_success_message": "Addon, Client und der Benachrichtigungsdienst funktionieren einwandfrei.",
        "test_detected": "Testsignal erkannt · Testnachricht wird gesendet",
        "requeued_title": "Wieder in der Warteschlange",
        "requeued_message": "Die Gruppensuche wurde nicht bestätigt. Du bist wieder für dieselbe Queue angemeldet.",
        "requeued_detected": "Wiedereinreihung erkannt · Korrekturmeldung wird gesendet",
        "queue_ready_named": "Queue bereit: {name}", "queue_ready_kind": "{kind}-Queue bereit",
        "confirm_in_wow": "Jetzt in WoW bestätigen.",
        "queue_detected": "Queue erkannt · Benachrichtigung wird gesendet",
        "queue_no_pushover": "Queue erkannt · Kein Benachrichtigungsdienst ist eingerichtet",
        "check_disturbed": "Erkennung gestört", "waiting_wow": "Spiel nicht erkannt",
        "wow_not_open": "WoW ist nicht geöffnet oder wurde noch nicht erkannt.",
        "monitoring_active": "Erkennung aktiv", "wow_pop_ready": "Erkennung aktiv",
        "client_searching": "Spiel nicht erkannt", "client_started": "Wird gestartet",
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
        "priority": "Priority", "priority_normal": "Normal (0)", "priority_high": "High (1)",
        "ntfy_priority_default": "Default (3)", "ntfy_priority_high": "High (4)",
        "ntfy_priority_default_help": "Standard notification with a short vibration, normal sound, and the usual notification behavior.",
        "ntfy_priority_high_help": "More prominent notification with a longer vibration, normal sound, and a pop-over alert.",
        "settings_title": "Settings", "settings_subtitle": "Queue Pop Notifier",
        "services": "Services", "services_intro": "Choose one service for queue notifications. Only one service can be active at a time.",
        "pushover_intro": "Sends queue notifications to your device through Pushover.",
        "user_key_help": "Your personal recipient key from the Pushover dashboard.",
        "app_token_help": "The token for your “Queue Pop Notifier” application in Pushover.",
        "pushover_help": "Where do I find the User Key and App Token?  ↗",
        "ntfy_intro": "Sends queue notifications to an ntfy topic.",
        "ntfy_server": "Server URL", "ntfy_server_help": "Default: https://ntfy.sh – or the URL of your own ntfy server.",
        "ntfy_topic": "Topic", "ntfy_topic_help": "The unique topic name subscribed to in the ntfy app.",
        "ntfy_token": "Access token (optional)", "ntfy_token_help": "Only needed when your topic or server is protected. Leave empty for normal public ntfy.sh topics.",
        "ntfy_help": "Open ntfy documentation  ↗",
        "telegram_intro": "Sends queue notifications through a Telegram bot.",
        "telegram_bot_token": "Bot token", "telegram_bot_token_help": "Get the bot token from BotFather in Telegram.",
        "telegram_chat_id": "Chat ID", "telegram_chat_id_help": "The numeric ID of the private chat or group the bot should send to.",
        "telegram_help": "Set up a Telegram bot  ↗",
        "pushover_as_default": "Use Pushover as default service",
        "ntfy_as_default": "Use ntfy as default service", "telegram_as_default": "Use Telegram as default service", "disabled_service": "Disabled",
        "configured_disabled": "Configured · disabled", "incomplete_service": "Incomplete", "service_error": "Invalid",
        "notifications_intro": "Choose how prominently queue alerts are delivered.",
        "priority_normal_help": "Standard notification with sound, vibration, and an alert according to the device settings. It is delivered quietly during configured quiet hours.",
        "priority_high_help": "Bypasses Pushover quiet hours and always triggers sound and vibration when the device is configured accordingly. Highlighted in Pushover.",
        "general": "General",
        "start_with_windows": "Start with Windows",
        "language_help": "Sets the language of the user interface.",
        "start_with_windows_help": "Starts Queue Pop Notifier automatically after signing in to Windows.",
        "test_pushover": "Send test notification", "test_service": "Test service", "test_running": "Checking connection …", "test_ok": "Connection successful", "test_failed": "Test failed: {error}", "save": "Save", "saved": "Saved ✓",
        "tray_settings": "Settings", "tray_report_issue": "Report an issue",
        "open_config_folder": "Open configuration folder",
        "tray_status": "{status}",
        "version": "Version {version} · Updates are installed automatically",
        "update_install_failed_title": "Update failed",
        "update_install_failed_message": "The update could not be installed: {error}",
        "update_checksum_failed": "The downloaded EXE checksum does not match.",
        "missing_title": "Service not configured", "missing_message": "{service} is not fully configured. Please complete the required information.",
        "connection_test": "Connection test", "connection_test_message": "Queue Pop Notifier is connected.",
        "pushover_connected": "Pushover connected · notifications are ready",
        "ntfy_connected": "ntfy connected · notifications are ready", "ntfy_failed": "ntfy failed: {error}",
        "telegram_connected": "Telegram connected · notifications are ready", "telegram_failed": "Telegram failed: {error}",
        "pushover_failed": "Pushover failed: {error}", "windows_required": "Windows required",
        "wow_missing_event": "WoW not found · the client is waiting for a running WoW window",
        "wow_ready_event": "WoW detected · monitoring ready",
        "capture_restored": "Screen capture restored · monitoring ready",
        "capture_failed": "WoW could not be checked temporarily: {error}",
        "incompatible": "Add-on incompatible · signal protocol {protocol}, required: {required}",
        "unreadable": "unreadable", "test_success": "Test successful",
        "test_success_message": "Add-on, client and the notification service are working correctly.",
        "test_detected": "Test signal detected · sending test notification",
        "requeued_title": "Back in the queue",
        "requeued_message": "The group invite was not confirmed. You are queued for the same activity again.",
        "requeued_detected": "Requeue detected · sending correction notification",
        "queue_ready_named": "Queue ready: {name}", "queue_ready_kind": "{kind} queue ready",
        "confirm_in_wow": "Confirm in WoW now.",
        "queue_detected": "Queue detected · sending notification",
        "queue_no_pushover": "Queue detected · no notification service is configured",
        "check_disturbed": "Detection disrupted", "waiting_wow": "Game not detected",
        "wow_not_open": "WoW is not open or has not been detected yet.",
        "monitoring_active": "Detection active", "wow_pop_ready": "Detection active",
        "client_searching": "Game not detected", "client_started": "Starting",
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
        saved = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        if isinstance(saved, dict):
            data.update({key: saved[key] for key in DEFAULTS if key in saved})
    except (OSError, ValueError):
        pass
    if data.get("pushover_priority") not in (0, 1):
        data["pushover_priority"] = 1
    if data.get("ntfy_priority") not in (3, 4):
        data["ntfy_priority"] = 4
    if data.get("default_service") not in ("pushover", "ntfy", "telegram"):
        data["default_service"] = "ntfy" if data.get("ntfy_topic") and not (data.get("pushover_user_key") and data.get("pushover_app_token")) else "pushover"
    return data


def save_config(data: dict) -> None:
    """Persist the configuration atomically and keep one recoverable backup."""
    APP_DIR.mkdir(parents=True, exist_ok=True)
    active_config = {key: data.get(key, default) for key, default in DEFAULTS.items()}
    temporary_path = CONFIG_PATH.with_suffix(".json.tmp")
    if CONFIG_PATH.exists():
        try:
            CONFIG_BACKUP_PATH.write_bytes(CONFIG_PATH.read_bytes())
        except OSError:
            pass
    temporary_path.write_text(json.dumps(active_config, indent=2), encoding="utf-8")
    os.replace(temporary_path, CONFIG_PATH)


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


def send_ntfy(config: dict, title: str, message: str) -> None:
    server = str(config.get("ntfy_server", "https://ntfy.sh")).strip().rstrip("/")
    topic = str(config.get("ntfy_topic", "")).strip().strip("/")
    if not server or not topic:
        raise RuntimeError("ntfy server or topic missing")
    url = f"{server}/{urllib.parse.quote(topic, safe='')}"
    headers = {
        "Title": title,
        "Priority": str(3 if config.get("ntfy_priority") == 3 else 4),
        "Tags": "video_game",
        "User-Agent": f"QueuePopNotifier/{APP_VERSION}",
    }
    token = str(config.get("ntfy_token", "")).strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=message.encode("utf-8"), headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=15) as response:
        if response.status < 200 or response.status >= 300:
            raise RuntimeError(f"ntfy HTTP {response.status}")


def send_telegram(config: dict, title: str, message: str) -> None:
    token = str(config.get("telegram_bot_token", "")).strip()
    chat_id = str(config.get("telegram_chat_id", "")).strip()
    if not token or not chat_id:
        raise RuntimeError("Telegram bot token or chat ID missing")
    payload = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": f"{title}\n\n{message}",
        "disable_web_page_preview": "true",
    }).encode("utf-8")
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=payload,
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        body = response.read().decode("utf-8", errors="replace")
    try:
        result = json.loads(body)
    except ValueError as exc:
        raise RuntimeError("Invalid response from Telegram") from exc
    if not result.get("ok"):
        raise RuntimeError(str(result.get("description") or "unknown Telegram API error"))


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
        self.geometry("410x260")
        self.minsize(400, 1)
        self.resizable(False, False)
        self.config_data = load_config()
        if self.config_data.get("start_with_windows", False):
            set_windows_startup(True)
        self.is_configured = bool(
            (self.config_data["pushover_user_key"] and self.config_data["pushover_app_token"])
            or self.config_data.get("ntfy_topic")
            or (self.config_data.get("telegram_bot_token") and self.config_data.get("telegram_chat_id"))
        )
        if self.is_configured:
            self.withdraw()
        configured_language = self.config_data.get("language", "auto")
        self.language = windows_language() if configured_language == "auto" else configured_language
        if self.language not in TEXTS:
            self.language = "en"
        self.title(self._t("settings_title"))
        self.messages: queue.Queue[tuple[str, str]] = queue.Queue()
        self.validation_results: queue.Queue[tuple[int, str, str]] = queue.Queue()
        self.validation_generation = 0
        self.pushover_validation_state = "unverified" if (self.config_data["pushover_user_key"] and self.config_data["pushover_app_token"]) else "not_configured"
        self.ntfy_validation_state = "unverified" if (self.config_data.get("ntfy_server") and self.config_data.get("ntfy_topic")) else "not_configured"
        self.telegram_validation_state = "unverified" if (self.config_data.get("telegram_bot_token") and self.config_data.get("telegram_chat_id")) else "not_configured"
        self.service_validation_results: queue.Queue[tuple[str, str, str]] = queue.Queue()
        self.service_icon_images = {}
        self.service_icon_specs = {}
        self.stop_event = threading.Event()
        self.worker = None
        self.tray_icon = None
        self.window_icon_photo = None
        self._apply_application_icon()
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
        configured = getattr(self, "selected_language_code", self.config_data.get("language", "auto"))
        index = {"auto": 0, "de": 1, "en": 2}.get(configured, 0)
        self.selected_language_code = ("auto", "de", "en")[index]
        self.language_var.set(values[index])

    def _language_selected(self, _event=None):
        """Keep the language code independent from the translated combobox text."""
        index = self.language_combo.current()
        if index >= 0:
            self.selected_language_code = ("auto", "de", "en")[index]
        self.after_idle(lambda: self._clear_combo_selection(self.language_combo))

    @staticmethod
    def _clear_combo_selection(combo):
        """Keep a readonly combobox legible after Tk selects its displayed text."""
        try:
            combo.selection_clear()
        except tk.TclError:
            pass

    def _set_priority_combo(self):
        values = [self._t("priority_normal"), self._t("priority_high")]
        self.priority_combo.configure(values=values)
        priority = int(self.config_data.get("pushover_priority", 1))
        index = 0 if priority == 0 else 1
        self.selected_priority = index
        self.priority_var.set(values[index])

    def _priority_selected(self, _event=None):
        """Keep priority independent from the translated combobox text."""
        index = self.priority_combo.current()
        if index >= 0:
            self.selected_priority = index
        self._update_priority_help()
        self.after_idle(lambda: self._clear_combo_selection(self.priority_combo))

    def _refresh_language(self):
        """Apply the selected language to every persistent UI element."""
        self.title(self._t("settings_title"))
        self.services_label.configure(text=self._t("services"))
        self.services_intro_label.configure(text=self._t("services_intro"))
        self.pushover_intro_label.configure(text=self._t("pushover_intro"))
        self.user_help_label.configure(text=self._t("user_key_help"))
        self.token_help_label.configure(text=self._t("app_token_help"))
        self.pushover_help_label.configure(text=self._t("pushover_help"))
        self.ntfy_intro_label.configure(text=self._t("ntfy_intro"))
        self.ntfy_server_label.configure(text=self._t("ntfy_server"))
        self.ntfy_server_help_label.configure(text=self._t("ntfy_server_help"))
        self.ntfy_topic_label.configure(text=self._t("ntfy_topic"))
        self.ntfy_topic_help_label.configure(text=self._t("ntfy_topic_help"))
        self.ntfy_token_label.configure(text=self._t("ntfy_token"))
        self.ntfy_token_help_label.configure(text=self._t("ntfy_token_help"))
        self.ntfy_help_label.configure(text=self._t("ntfy_help"))
        self.telegram_intro_label.configure(text=self._t("telegram_intro"))
        self.telegram_bot_token_label.configure(text=self._t("telegram_bot_token"))
        self.telegram_bot_token_help_label.configure(text=self._t("telegram_bot_token_help"))
        self.telegram_chat_id_label.configure(text=self._t("telegram_chat_id"))
        self.telegram_chat_id_help_label.configure(text=self._t("telegram_chat_id_help"))
        self.telegram_help_label.configure(text=self._t("telegram_help"))
        self.pushover_default_label.configure(text=self._t("pushover_as_default"))
        self.ntfy_default_label.configure(text=self._t("ntfy_as_default"))
        self.telegram_default_label.configure(text=self._t("telegram_as_default"))
        self.pushover_priority_label.configure(text=self._t("priority"))
        self.ntfy_priority_label.configure(text=self._t("priority"))
        self.general_label.configure(text=self._t("general"))
        self.language_label.configure(text=self._t("language"))
        self.language_help_label.configure(text=self._t("language_help"))
        self.start_with_windows_label.configure(text=self._t("start_with_windows"))
        self.start_with_windows_help_label.configure(text=self._t("start_with_windows_help"))
        self.pushover_test_link.configure(text=self._t("test_service"))
        self.ntfy_test_link.configure(text=self._t("test_service"))
        self.telegram_test_link.configure(text=self._t("test_service"))
        self.save_button.configure(text=self._t("save"))
        self.config_folder_link.configure(text=self._t("open_config_folder"))
        self.version_label.configure(text=self._t("version", version=APP_VERSION))
        self._update_eye_button("user")
        self._update_eye_button("token")
        self._update_eye_button("telegram")
        configured = bool(self.config_data["pushover_user_key"] and self.config_data["pushover_app_token"])
        self._set_pushover_state(self.pushover_validation_state if configured else "not_configured")
        self._update_ntfy_state()
        self._update_telegram_state()
        self._set_language_combo()
        self._set_priority_combo()
        self._set_ntfy_priority_combo()
        self._update_priority_help()
        self._update_ntfy_priority_help()
        self._draw_service_toggles()
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
        pushover_configured = bool(self.config_data["pushover_user_key"] and self.config_data["pushover_app_token"])
        ntfy_configured = bool(self.config_data.get("ntfy_topic"))
        telegram_configured = bool(self.config_data.get("telegram_bot_token") and self.config_data.get("telegram_chat_id"))
        self.expanded_service = None if (pushover_configured or ntfy_configured or telegram_configured) else "pushover"

        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Dark.TEntry", fieldbackground="#ffffff", foreground=fg,
                        insertcolor=fg, bordercolor=border, lightcolor=border, darkcolor=border,
                        padding=(9, 7))
        # Extra right padding keeps text clear of the eye button overlaid inside secret fields.
        style.configure("Secret.TEntry", fieldbackground="#ffffff", foreground=fg,
                        insertcolor=fg, bordercolor=border, lightcolor=border, darkcolor=border,
                        padding=(9, 7, 34, 7))
        style.configure("Dark.TCombobox", fieldbackground="#ffffff", background="#dddddd",
                        foreground=fg, arrowcolor=fg, bordercolor=border, lightcolor=border,
                        darkcolor=border, selectbackground="#ffffff", selectforeground=fg,
                        padding=(8, 6))
        style.map("Dark.TCombobox", fieldbackground=[("readonly", "#ffffff")],
                  foreground=[("readonly", fg)], selectbackground=[("readonly", "#ffffff")],
                  selectforeground=[("readonly", fg)])
        style.configure("Secondary.TButton", background="#e2e2e2", foreground=fg,
                        bordercolor="#bdbdbd", padding=(12, 7), font=("Segoe UI", 9))
        style.map("Secondary.TButton", background=[("active", "#d5d5d5")])
        style.configure("Primary.TButton", background="#3977bd", foreground="#ffffff",
                        bordercolor="#3977bd", padding=(15, 7), font=("Segoe UI", 9, "bold"))
        style.map("Primary.TButton", background=[("active", "#4788d1")])

        root = tk.Frame(self, bg=bg, padx=14, pady=14)
        root.pack(fill="both", expand=True)
        def card_frame():
            shell = tk.Frame(root, bg=border, padx=1, pady=1)
            shell.pack(fill="x", pady=(0, 10))
            body = tk.Frame(shell, bg=card, padx=16, pady=14)
            body.pack(fill="both")
            return body

        # Services section: only one provider panel can be expanded at a time.
        services_shell = tk.Frame(root, bg=border, padx=1, pady=1)
        services_shell.pack(fill="x", pady=(0, 10))
        services_body = tk.Frame(services_shell, bg=card, padx=12, pady=12)
        services_body.pack(fill="both")
        self.services_label = tk.Label(services_body, text=self._t("services"), bg=card, fg=fg,
                                       font=("Segoe UI", 11, "bold"))
        self.services_label.pack(anchor="w")
        self.services_intro_label = tk.Label(services_body, text=self._t("services_intro"), bg=card,
                                              fg=muted, font=("Segoe UI", 8))
        self.services_intro_label.pack(anchor="w", pady=(2, 10))

        self.default_service_var = tk.StringVar(value=self.config_data.get("default_service", "pushover"))

        def service_row(name, service_key, icon_b64, fallback_text, fallback_fill):
            row = tk.Frame(services_body, bg="#ededed", highlightthickness=1,
                           highlightbackground="#c7c7c7", cursor="hand2")
            row.pack(fill="x", pady=(0, 6))
            row.columnconfigure(1, weight=1)
            canvas = tk.Canvas(row, width=48, height=48, bg="#ededed", bd=0, highlightthickness=0)
            canvas.grid(row=0, column=0, padx=(10, 10), pady=8)
            self.service_icon_specs[service_key] = (canvas, icon_b64, fallback_text, fallback_fill)
            self._draw_service_icon(canvas, service_key, icon_b64, fallback_text, fallback_fill, muted=False)
            label = tk.Label(row, text=name, bg="#ededed", fg=fg, font=("Segoe UI", 10, "bold"), anchor="w")
            label.grid(row=0, column=1, sticky="ew")
            state = tk.Label(row, bg="#ededed", fg=muted, font=("Segoe UI", 9), anchor="e")
            state.grid(row=0, column=2, sticky="e", padx=(10, 8))
            chevron = tk.Label(row, text="›", bg="#ededed", fg=muted, font=("Segoe UI Symbol", 14), width=2)
            chevron.grid(row=0, column=3, padx=(0, 6))
            return row, canvas, label, state, chevron

        self.pushover_row, pushover_icon, self.pushover_name_label, self.pushover_state, self.pushover_chevron = service_row("Pushover", "pushover", PUSHOVER_SERVICE_ICON_B64, "P", "#2f8fd8")
        configured = bool(self.config_data["pushover_user_key"] and self.config_data["pushover_app_token"])
        self.pushover_state.configure(text=self._t("credentials_unverified") if configured else self._t("not_configured"))
        self.settings_frame = tk.Frame(services_body, bg=card, padx=4, pady=2)
        self.pushover_intro_label = tk.Label(self.settings_frame, text=self._t("pushover_intro"), bg=card, fg=muted, font=("Segoe UI", 8))
        self.pushover_intro_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        tk.Label(self.settings_frame, text="User Key", bg=card, fg=fg, font=("Segoe UI", 9, "bold")).grid(row=1, column=0, columnspan=2, sticky="w")
        self.user_help_label = tk.Label(self.settings_frame, text=self._t("user_key_help"), bg=card, fg=muted, font=("Segoe UI", 8))
        self.user_help_label.grid(row=2, column=0, columnspan=2, sticky="w", pady=(1, 6))
        self.user_var = tk.StringVar(value=self.config_data["pushover_user_key"])
        user_entry_row = tk.Frame(self.settings_frame, bg=card)
        user_entry_row.grid(row=3, column=0, columnspan=2, sticky="ew")
        user_entry_row.columnconfigure(0, weight=1)
        self.user_entry = ttk.Entry(user_entry_row, textvariable=self.user_var, show="•", style="Secret.TEntry")
        self.user_entry.grid(row=1, column=0, sticky="ew")
        self.user_eye = tk.Button(user_entry_row, text="", relief="flat", bd=0, bg="#ffffff", fg=muted,
                                  activebackground="#ffffff", activeforeground=accent, cursor="hand2",
                                  font=("Segoe MDL2 Assets", 11), padx=6, pady=0,
                                  command=lambda: self._toggle_secret("user"))
        self.user_eye.place(relx=1.0, rely=0.5, x=-4, anchor="e")
        tk.Label(self.settings_frame, text="App/API Token", bg=card, fg=fg, font=("Segoe UI", 9, "bold")).grid(row=4, column=0, columnspan=2, sticky="w", pady=(13, 0))
        self.token_help_label = tk.Label(self.settings_frame, text=self._t("app_token_help"), bg=card, fg=muted, font=("Segoe UI", 8))
        self.token_help_label.grid(row=5, column=0, columnspan=2, sticky="w", pady=(1, 6))
        self.token_var = tk.StringVar(value=self.config_data["pushover_app_token"])
        token_entry_row = tk.Frame(self.settings_frame, bg=card)
        token_entry_row.grid(row=6, column=0, columnspan=2, sticky="ew")
        token_entry_row.columnconfigure(0, weight=1)
        self.token_entry = ttk.Entry(token_entry_row, textvariable=self.token_var, show="•", style="Secret.TEntry")
        self.token_entry.grid(row=1, column=0, sticky="ew")
        self.token_eye = tk.Button(token_entry_row, text="", relief="flat", bd=0, bg="#ffffff", fg=muted,
                                   activebackground="#ffffff", activeforeground=accent, cursor="hand2",
                                   font=("Segoe MDL2 Assets", 11), padx=6, pady=0,
                                   command=lambda: self._toggle_secret("token"))
        self.token_eye.place(relx=1.0, rely=0.5, x=-4, anchor="e")
        self.pushover_help_label = tk.Label(self.settings_frame, text=self._t("pushover_help"), bg=card, fg=accent, cursor="hand2", font=("Segoe UI", 8, "underline"))
        self.pushover_help_label.grid(row=7, column=0, columnspan=2, sticky="w", pady=(11, 0))
        self.pushover_help_label.bind("<Button-1>", lambda _event: webbrowser.open("https://pushover.net/apps/build"))
        self.pushover_priority_label = tk.Label(self.settings_frame, text=self._t("priority"), bg=card, fg=fg, font=("Segoe UI", 9, "bold"))
        self.pushover_priority_label.grid(row=8, column=0, sticky="w", pady=(13, 0))
        self.priority_var = tk.StringVar()
        self.selected_priority = 0 if self.config_data.get("pushover_priority") == 0 else 1
        self.priority_combo = ttk.Combobox(self.settings_frame, textvariable=self.priority_var, state="readonly", width=18, style="Dark.TCombobox")
        self.priority_combo.grid(row=9, column=0, columnspan=2, sticky="w", pady=(5, 0))
        self.priority_help_label = tk.Label(self.settings_frame, text="", bg=card, fg=muted, justify="left", anchor="w", wraplength=500, font=("Segoe UI", 8))
        self.priority_help_label.grid(row=10, column=0, columnspan=2, sticky="ew", pady=(5, 0))
        self._set_priority_combo()
        self.priority_combo.bind("<<ComboboxSelected>>", self._priority_selected)
        self._update_priority_help()
        tk.Frame(self.settings_frame, bg="#d7d7d7", height=1).grid(row=11, column=0, columnspan=2, sticky="ew", pady=(13, 10))
        pushover_default_row = tk.Frame(self.settings_frame, bg=card)
        pushover_default_row.grid(row=12, column=0, columnspan=2, sticky="ew")
        pushover_default_row.columnconfigure(0, weight=1)
        self.pushover_default_label = tk.Label(pushover_default_row, text=self._t("pushover_as_default"), bg=card, fg=fg, font=("Segoe UI", 9, "bold"), anchor="w")
        self.pushover_default_label.grid(row=1, column=0, sticky="ew")
        self.pushover_default_toggle = tk.Canvas(pushover_default_row, width=38, height=20, bg=card, highlightthickness=0, bd=0, cursor="hand2", takefocus=True)
        self.pushover_default_toggle.grid(row=1, column=1, sticky="e", padx=(24, 3))
        for widget in (self.pushover_default_label, self.pushover_default_toggle):
            widget.bind("<Button-1>", lambda _event: self._set_default_service("pushover"))
        tk.Frame(self.settings_frame, bg="#d7d7d7", height=1).grid(row=13, column=0, columnspan=2, sticky="ew", pady=(13, 10))
        self.pushover_test_link = tk.Label(self.settings_frame, text=self._t("test_service"), bg=card, fg=accent, cursor="hand2", font=("Segoe UI", 9, "underline"))
        self.pushover_test_link.grid(row=14, column=0, columnspan=2, sticky="w")
        self.pushover_test_link.bind("<Button-1>", lambda _event: self._test_service("pushover"))
        self.pushover_test_status = tk.Label(self.settings_frame, text="", bg=card, fg=muted, font=("Segoe UI", 8), anchor="w", justify="left", wraplength=500)
        self.pushover_test_status.grid(row=15, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        self.settings_frame.columnconfigure(0, weight=1)

        self.ntfy_row, ntfy_icon, self.ntfy_name_label, self.ntfy_state, self.ntfy_chevron = service_row("ntfy", "ntfy", NTFY_SERVICE_ICON_B64, "□", "#2d9b68")
        self.ntfy_frame = tk.Frame(services_body, bg=card, padx=4, pady=2)
        self.ntfy_intro_label = tk.Label(self.ntfy_frame, text=self._t("ntfy_intro"), bg=card, fg=muted, font=("Segoe UI", 8))
        self.ntfy_intro_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        self.ntfy_server_label = tk.Label(self.ntfy_frame, text=self._t("ntfy_server"), bg=card, fg=fg, font=("Segoe UI", 9, "bold"))
        self.ntfy_server_label.grid(row=1, column=0, columnspan=2, sticky="w")
        self.ntfy_server_help_label = tk.Label(self.ntfy_frame, text=self._t("ntfy_server_help"), bg=card, fg=muted, font=("Segoe UI", 8))
        self.ntfy_server_help_label.grid(row=2, column=0, columnspan=2, sticky="w", pady=(1, 6))
        self.ntfy_server_var = tk.StringVar(value=self.config_data.get("ntfy_server", "https://ntfy.sh"))
        self.ntfy_server_entry = ttk.Entry(self.ntfy_frame, textvariable=self.ntfy_server_var, style="Dark.TEntry")
        self.ntfy_server_entry.grid(row=3, column=0, columnspan=2, sticky="ew")
        self.ntfy_topic_label = tk.Label(self.ntfy_frame, text=self._t("ntfy_topic"), bg=card, fg=fg, font=("Segoe UI", 9, "bold"))
        self.ntfy_topic_label.grid(row=4, column=0, columnspan=2, sticky="w", pady=(13, 0))
        self.ntfy_topic_help_label = tk.Label(self.ntfy_frame, text=self._t("ntfy_topic_help"), bg=card, fg=muted, font=("Segoe UI", 8))
        self.ntfy_topic_help_label.grid(row=5, column=0, columnspan=2, sticky="w", pady=(1, 6))
        self.ntfy_topic_var = tk.StringVar(value=self.config_data.get("ntfy_topic", ""))
        self.ntfy_topic_entry = ttk.Entry(self.ntfy_frame, textvariable=self.ntfy_topic_var, style="Dark.TEntry")
        self.ntfy_topic_entry.grid(row=6, column=0, columnspan=2, sticky="ew")
        self.ntfy_token_label = tk.Label(self.ntfy_frame, text=self._t("ntfy_token"), bg=card, fg=fg, font=("Segoe UI", 9, "bold"))
        self.ntfy_token_label.grid(row=7, column=0, columnspan=2, sticky="w", pady=(13, 0))
        self.ntfy_token_help_label = tk.Label(self.ntfy_frame, text=self._t("ntfy_token_help"), bg=card, fg=muted, font=("Segoe UI", 8), wraplength=470, justify="left")
        self.ntfy_token_help_label.grid(row=8, column=0, columnspan=2, sticky="w", pady=(1, 6))
        self.ntfy_token_var = tk.StringVar(value=self.config_data.get("ntfy_token", ""))
        ntfy_token_entry_row = tk.Frame(self.ntfy_frame, bg=card)
        ntfy_token_entry_row.grid(row=9, column=0, columnspan=2, sticky="ew")
        ntfy_token_entry_row.columnconfigure(0, weight=1)
        self.ntfy_token_entry = ttk.Entry(ntfy_token_entry_row, textvariable=self.ntfy_token_var, show="•", style="Secret.TEntry")
        self.ntfy_token_entry.grid(row=0, column=0, sticky="ew")
        self.ntfy_token_eye = tk.Button(ntfy_token_entry_row, text="", relief="flat", bd=0, bg="#ffffff", fg=muted,
                                        activebackground="#ffffff", activeforeground=accent, cursor="hand2",
                                        font=("Segoe MDL2 Assets", 11), padx=6, pady=0,
                                        command=lambda: self._toggle_secret("ntfy"))
        self.ntfy_token_eye.place(relx=1.0, rely=0.5, x=-4, anchor="e")
        self.ntfy_help_label = tk.Label(self.ntfy_frame, text=self._t("ntfy_help"), bg=card, fg=accent, cursor="hand2", font=("Segoe UI", 8, "underline"))
        self.ntfy_help_label.grid(row=10, column=0, columnspan=2, sticky="w", pady=(11, 0))
        self.ntfy_help_label.bind("<Button-1>", lambda _event: webbrowser.open("https://docs.ntfy.sh/publish/"))
        self.ntfy_priority_label = tk.Label(self.ntfy_frame, text=self._t("priority"), bg=card, fg=fg, font=("Segoe UI", 9, "bold"))
        self.ntfy_priority_label.grid(row=11, column=0, sticky="w", pady=(13, 0))
        self.ntfy_priority_var = tk.StringVar()
        self.selected_ntfy_priority = 3 if self.config_data.get("ntfy_priority") == 3 else 4
        self.ntfy_priority_combo = ttk.Combobox(self.ntfy_frame, textvariable=self.ntfy_priority_var, state="readonly", width=18, style="Dark.TCombobox")
        self.ntfy_priority_combo.grid(row=12, column=0, columnspan=2, sticky="w", pady=(5, 0))
        self.ntfy_priority_help_label = tk.Label(self.ntfy_frame, text="", bg=card, fg=muted, justify="left", anchor="w", wraplength=500, font=("Segoe UI", 8))
        self.ntfy_priority_help_label.grid(row=13, column=0, columnspan=2, sticky="ew", pady=(5, 0))
        self._set_ntfy_priority_combo()
        self.ntfy_priority_combo.bind("<<ComboboxSelected>>", self._ntfy_priority_selected)
        self._update_ntfy_priority_help()
        tk.Frame(self.ntfy_frame, bg="#d7d7d7", height=1).grid(row=14, column=0, columnspan=2, sticky="ew", pady=(13, 10))
        ntfy_default_row = tk.Frame(self.ntfy_frame, bg=card)
        ntfy_default_row.grid(row=15, column=0, columnspan=2, sticky="ew")
        ntfy_default_row.columnconfigure(0, weight=1)
        self.ntfy_default_label = tk.Label(ntfy_default_row, text=self._t("ntfy_as_default"), bg=card, fg=fg, font=("Segoe UI", 9, "bold"), anchor="w")
        self.ntfy_default_label.grid(row=0, column=0, sticky="ew")
        self.ntfy_default_toggle = tk.Canvas(ntfy_default_row, width=38, height=20, bg=card, highlightthickness=0, bd=0, cursor="hand2", takefocus=True)
        self.ntfy_default_toggle.grid(row=0, column=1, sticky="e", padx=(24, 3))
        for widget in (self.ntfy_default_label, self.ntfy_default_toggle):
            widget.bind("<Button-1>", lambda _event: self._set_default_service("ntfy"))
        tk.Frame(self.ntfy_frame, bg="#d7d7d7", height=1).grid(row=16, column=0, columnspan=2, sticky="ew", pady=(13, 10))
        self.ntfy_test_link = tk.Label(self.ntfy_frame, text=self._t("test_service"), bg=card, fg=accent, cursor="hand2", font=("Segoe UI", 9, "underline"))
        self.ntfy_test_link.grid(row=17, column=0, columnspan=2, sticky="w")
        self.ntfy_test_link.bind("<Button-1>", lambda _event: self._test_service("ntfy"))
        self.ntfy_test_status = tk.Label(self.ntfy_frame, text="", bg=card, fg=muted, font=("Segoe UI", 8), anchor="w", justify="left", wraplength=500)
        self.ntfy_test_status.grid(row=18, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        self.ntfy_frame.columnconfigure(0, weight=1)

        self.telegram_row, telegram_icon, self.telegram_name_label, self.telegram_state, self.telegram_chevron = service_row("Telegram", "telegram", TELEGRAM_SERVICE_ICON_B64, "T", "#2ca5e0")
        self.telegram_frame = tk.Frame(services_body, bg=card, padx=4, pady=2)
        self.telegram_intro_label = tk.Label(self.telegram_frame, text=self._t("telegram_intro"), bg=card, fg=muted, font=("Segoe UI", 8))
        self.telegram_intro_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        self.telegram_bot_token_label = tk.Label(self.telegram_frame, text=self._t("telegram_bot_token"), bg=card, fg=fg, font=("Segoe UI", 9, "bold"))
        self.telegram_bot_token_label.grid(row=1, column=0, columnspan=2, sticky="w")
        self.telegram_bot_token_help_label = tk.Label(self.telegram_frame, text=self._t("telegram_bot_token_help"), bg=card, fg=muted, font=("Segoe UI", 8))
        self.telegram_bot_token_help_label.grid(row=2, column=0, columnspan=2, sticky="w", pady=(1, 6))
        self.telegram_bot_token_var = tk.StringVar(value=self.config_data.get("telegram_bot_token", ""))
        telegram_token_row = tk.Frame(self.telegram_frame, bg=card)
        telegram_token_row.grid(row=3, column=0, columnspan=2, sticky="ew")
        telegram_token_row.columnconfigure(0, weight=1)
        self.telegram_bot_token_entry = ttk.Entry(telegram_token_row, textvariable=self.telegram_bot_token_var, show="•", style="Secret.TEntry")
        self.telegram_bot_token_entry.grid(row=0, column=0, sticky="ew")
        self.telegram_token_eye = tk.Button(telegram_token_row, text="", relief="flat", bd=0, bg="#ffffff", fg=muted,
                                            activebackground="#ffffff", activeforeground=accent, cursor="hand2",
                                            font=("Segoe MDL2 Assets", 11), padx=6, pady=0,
                                            command=lambda: self._toggle_secret("telegram"))
        self.telegram_token_eye.place(relx=1.0, rely=0.5, x=-4, anchor="e")
        self.telegram_chat_id_label = tk.Label(self.telegram_frame, text=self._t("telegram_chat_id"), bg=card, fg=fg, font=("Segoe UI", 9, "bold"))
        self.telegram_chat_id_label.grid(row=4, column=0, columnspan=2, sticky="w", pady=(13, 0))
        self.telegram_chat_id_help_label = tk.Label(self.telegram_frame, text=self._t("telegram_chat_id_help"), bg=card, fg=muted, font=("Segoe UI", 8), wraplength=500, justify="left")
        self.telegram_chat_id_help_label.grid(row=5, column=0, columnspan=2, sticky="w", pady=(1, 6))
        self.telegram_chat_id_var = tk.StringVar(value=self.config_data.get("telegram_chat_id", ""))
        self.telegram_chat_id_entry = ttk.Entry(self.telegram_frame, textvariable=self.telegram_chat_id_var, style="Dark.TEntry")
        self.telegram_chat_id_entry.grid(row=6, column=0, columnspan=2, sticky="ew")
        self.telegram_help_label = tk.Label(self.telegram_frame, text=self._t("telegram_help"), bg=card, fg=accent, cursor="hand2", font=("Segoe UI", 8, "underline"))
        self.telegram_help_label.grid(row=7, column=0, columnspan=2, sticky="w", pady=(11, 0))
        self.telegram_help_label.bind("<Button-1>", lambda _event: webbrowser.open("https://core.telegram.org/bots/tutorial"))
        tk.Frame(self.telegram_frame, bg="#d7d7d7", height=1).grid(row=8, column=0, columnspan=2, sticky="ew", pady=(13, 10))
        telegram_default_row = tk.Frame(self.telegram_frame, bg=card)
        telegram_default_row.grid(row=9, column=0, columnspan=2, sticky="ew")
        telegram_default_row.columnconfigure(0, weight=1)
        self.telegram_default_label = tk.Label(telegram_default_row, text=self._t("telegram_as_default"), bg=card, fg=fg, font=("Segoe UI", 9, "bold"), anchor="w")
        self.telegram_default_label.grid(row=0, column=0, sticky="ew")
        self.telegram_default_toggle = tk.Canvas(telegram_default_row, width=38, height=20, bg=card, highlightthickness=0, bd=0, cursor="hand2", takefocus=True)
        self.telegram_default_toggle.grid(row=0, column=1, sticky="e", padx=(24, 3))
        for widget in (self.telegram_default_label, self.telegram_default_toggle):
            widget.bind("<Button-1>", lambda _event: self._set_default_service("telegram"))
        tk.Frame(self.telegram_frame, bg="#d7d7d7", height=1).grid(row=10, column=0, columnspan=2, sticky="ew", pady=(13, 10))
        self.telegram_test_link = tk.Label(self.telegram_frame, text=self._t("test_service"), bg=card, fg=accent, cursor="hand2", font=("Segoe UI", 9, "underline"))
        self.telegram_test_link.grid(row=11, column=0, columnspan=2, sticky="w")
        self.telegram_test_link.bind("<Button-1>", lambda _event: self._test_service("telegram"))
        self.telegram_test_status = tk.Label(self.telegram_frame, text="", bg=card, fg=muted, font=("Segoe UI", 8), anchor="w", justify="left", wraplength=500)
        self.telegram_test_status.grid(row=12, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        self.telegram_frame.columnconfigure(0, weight=1)

        for widget in (self.pushover_row, pushover_icon, self.pushover_name_label, self.pushover_state, self.pushover_chevron):
            widget.bind("<Button-1>", lambda _event: self._toggle_service_panel("pushover"))
        for widget in (self.ntfy_row, ntfy_icon, self.ntfy_name_label, self.ntfy_state, self.ntfy_chevron):
            widget.bind("<Button-1>", lambda _event: self._toggle_service_panel("ntfy"))
        for widget in (self.telegram_row, telegram_icon, self.telegram_name_label, self.telegram_state, self.telegram_chevron):
            widget.bind("<Button-1>", lambda _event: self._toggle_service_panel("telegram"))
        self.ntfy_server_var.trace_add("write", self._ntfy_changed)
        self.ntfy_topic_var.trace_add("write", self._ntfy_changed)
        self.ntfy_token_var.trace_add("write", self._ntfy_changed)
        self.telegram_bot_token_var.trace_add("write", self._telegram_changed)
        self.telegram_chat_id_var.trace_add("write", self._telegram_changed)
        self._update_ntfy_state()
        self._update_telegram_state()
        self._show_service_panel()
        self._draw_service_toggles()

        self.language_var = tk.StringVar()
        self.selected_language_code = self.config_data.get("language", "auto")

        general_card = card_frame()
        self.general_label = tk.Label(general_card, text=self._t("general"), bg=card, fg=fg,
                                      font=("Segoe UI", 11, "bold"))
        self.general_label.pack(anchor="w")
        self.start_with_windows_var = tk.BooleanVar(value=bool(self.config_data.get("start_with_windows", False)))
        language_row = tk.Frame(general_card, bg=card)
        language_row.pack(fill="x", pady=(13, 12))
        language_row.columnconfigure(0, weight=1)
        self.language_label = tk.Label(language_row, text=self._t("language"), bg=card, fg=fg,
                                       font=("Segoe UI", 9, "bold"), anchor="w")
        self.language_label.grid(row=0, column=0, sticky="ew")
        self.language_help_label = tk.Label(language_row, text=self._t("language_help"), bg=card, fg=muted,
                                             justify="left", anchor="w", width=1, font=("Segoe UI", 8))
        self.language_help_label.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(3, 0))
        self.language_combo = ttk.Combobox(language_row, textvariable=self.language_var,
                                           state="readonly", width=22, style="Dark.TCombobox")
        self.language_combo.grid(row=0, column=1, sticky="e", padx=(24, 0))
        self._set_language_combo()
        self.language_combo.bind("<<ComboboxSelected>>", self._language_selected)
        tk.Frame(general_card, bg="#d7d7d7", height=1).pack(fill="x")
        autostart_row = tk.Frame(general_card, bg=card)
        autostart_row.pack(fill="x", pady=(12, 0))
        autostart_row.columnconfigure(0, weight=1)
        self.start_with_windows_toggle = tk.Canvas(autostart_row, width=38, height=20, bg=card,
                                                    highlightthickness=0, bd=0, cursor="hand2", takefocus=True)
        self.start_with_windows_label = tk.Label(autostart_row, text=self._t("start_with_windows"), bg=card,
                                                  fg=fg, font=("Segoe UI", 9, "bold"), anchor="w")
        self.start_with_windows_label.grid(row=0, column=0, sticky="ew")
        self.start_with_windows_help_label = tk.Label(autostart_row, text=self._t("start_with_windows_help"),
                                                       bg=card, fg=muted, justify="left", anchor="w", width=1,
                                                       font=("Segoe UI", 8))
        self.start_with_windows_help_label.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(3, 0))
        self.start_with_windows_toggle.grid(row=0, column=1, sticky="e", padx=(24, 3))
        self.start_with_windows_var.trace_add("write", self._draw_autostart_toggle)
        self._draw_autostart_toggle()
        for widget in (autostart_row, self.start_with_windows_label, self.start_with_windows_help_label,
                       self.start_with_windows_toggle):
            widget.bind("<Button-1>", self._toggle_autostart)
        self.start_with_windows_toggle.bind("<space>", self._toggle_autostart)
        self.start_with_windows_toggle.bind("<Return>", self._toggle_autostart)

        actions = tk.Frame(root, bg=bg)
        actions.pack(fill="x", pady=(2, 0))
        self.save_button = ttk.Button(actions, text=self._t("save"), style="Primary.TButton", command=self._save)
        self.save_button.pack(side="right")
        footer = tk.Frame(root, bg=bg)
        footer.pack(fill="x", pady=(8, 0))
        self.config_folder_link = tk.Label(footer, text=self._t("open_config_folder"), bg=bg, fg=accent,
                                           cursor="hand2", font=("Segoe UI", 8, "underline"))
        self.config_folder_link.pack(side="left")
        self.config_folder_link.bind("<Button-1>", self._open_config_folder)
        self.version_label = tk.Label(footer, text=self._t("version", version=APP_VERSION), bg=bg, fg=muted,
                                      font=("Segoe UI", 8), anchor="e")
        self.version_label.pack(side="right")
        self.user_var.trace_add("write", self._credentials_changed)
        self.token_var.trace_add("write", self._credentials_changed)

    def _toggle_service_panel(self, service):
        self.expanded_service = None if self.expanded_service == service else service
        self._show_service_panel()
        self.after_idle(self._fit_window_height)

    def _show_service_panel(self):
        self.settings_frame.pack_forget()
        self.ntfy_frame.pack_forget()
        self.telegram_frame.pack_forget()
        self.pushover_chevron.configure(text="›")
        self.ntfy_chevron.configure(text="›")
        self.telegram_chevron.configure(text="›")
        if self.expanded_service == "pushover":
            self.settings_frame.pack(fill="x", pady=(4, 8), before=self.ntfy_row)
            self.pushover_chevron.configure(text="⌄")
        elif self.expanded_service == "ntfy":
            self.ntfy_frame.pack(fill="x", pady=(4, 8), before=self.telegram_row)
            self.ntfy_chevron.configure(text="⌄")
        elif self.expanded_service == "telegram":
            self.telegram_frame.pack(fill="x", pady=(4, 2))
            self.telegram_chevron.configure(text="⌄")
        self._refresh_service_icons()

    def _refresh_service_icons(self):
        """Emphasize the open service and mute the other service icons."""
        for key, (canvas, image_b64, fallback_text, fallback_fill) in self.service_icon_specs.items():
            muted = self.expanded_service is not None and key != self.expanded_service
            self._draw_service_icon(canvas, key, image_b64, fallback_text, fallback_fill, muted=muted)

    def _draw_service_icon(self, canvas, key, image_b64, fallback_text, fallback_fill, muted=False):
        canvas.delete("all")
        try:
            image_bytes = base64.b64decode(image_b64)
            image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
            image = ImageOps.fit(image, (42, 42), method=Image.LANCZOS)
            if muted:
                alpha = image.getchannel("A")
                grey = ImageOps.grayscale(image.convert("RGB")).convert("RGBA")
                grey.putalpha(alpha)
                image = grey
            mask = Image.new("L", (42, 42), 0)
            mask_draw = Image.new("RGBA", (42, 42), (0, 0, 0, 0))
            # Create a crisp circular alpha mask.
            from PIL import ImageDraw
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, 41, 41), fill=255)
            circular = Image.new("RGBA", (42, 42), (0, 0, 0, 0))
            circular.paste(image, (0, 0), mask)
            photo = ImageTk.PhotoImage(circular)
            canvas.create_image(24, 24, image=photo)
            canvas.image = photo
            self.service_icon_images[key] = photo
        except Exception:
            fill = "#9aa0a6" if muted else fallback_fill
            canvas.create_oval(3, 3, 45, 45, fill=fill, outline=fill)
            canvas.create_text(24, 24, text=fallback_text, fill="white", font=("Segoe UI", 17, "bold"))

    def _apply_application_icon(self):
        """Use the fixed queuepop_notifier.ico for the settings window and dialogs."""
        if not ICON_PATH.exists():
            return
        try:
            if os.name == "nt":
                self.iconbitmap(default=str(ICON_PATH))
            # Keep an iconphoto reference as a fallback for Tk dialogs and
            # non-Windows environments.
            image = Image.open(ICON_PATH).convert("RGBA")
            self.window_icon_photo = ImageTk.PhotoImage(image.resize((32, 32), Image.LANCZOS))
            self.iconphoto(True, self.window_icon_photo)
        except Exception:
            pass

    @staticmethod
    def _required_field_state(values):
        stripped = [str(value).strip() for value in values]
        if all(stripped):
            return "complete"
        if any(stripped):
            return "incomplete"
        return "empty"

    def _set_default_service(self, service):
        if service not in ("pushover", "ntfy", "telegram"):
            return "break"
        self.default_service_var.set(service)
        self._draw_service_toggles()
        self._set_pushover_state(self.pushover_validation_state)
        self._update_ntfy_state()
        self._update_telegram_state()
        save_config(self._current_config())
        return "break"

    @staticmethod
    def _draw_switch(canvas, enabled):
        canvas.delete("all")
        track = "#3977bd" if enabled else "#aeb3b8"
        outline = "#2f639e" if enabled else "#979da3"
        canvas.create_oval(1, 1, 19, 19, fill=track, outline=outline)
        canvas.create_oval(19, 1, 37, 19, fill=track, outline=outline)
        canvas.create_rectangle(10, 1, 28, 19, fill=track, outline=track)
        knob_x = 27 if enabled else 11
        canvas.create_oval(knob_x - 7, 3, knob_x + 7, 17, fill="#ffffff", outline="#e7e7e7")

    def _draw_service_toggles(self):
        selected = self.default_service_var.get()
        self._draw_switch(self.pushover_default_toggle, selected == "pushover")
        self._draw_switch(self.ntfy_default_toggle, selected == "ntfy")
        self._draw_switch(self.telegram_default_toggle, selected == "telegram")

    def _set_ntfy_priority_combo(self):
        values = [self._t("ntfy_priority_default"), self._t("ntfy_priority_high")]
        self.ntfy_priority_combo.configure(values=values)
        index = 0 if self.selected_ntfy_priority == 3 else 1
        self.ntfy_priority_var.set(values[index])

    def _ntfy_priority_selected(self, _event=None):
        index = self.ntfy_priority_combo.current()
        if index >= 0:
            self.selected_ntfy_priority = 3 if index == 0 else 4
        self._update_ntfy_priority_help()
        self.after_idle(lambda: self._clear_combo_selection(self.ntfy_priority_combo))

    def _update_ntfy_priority_help(self):
        key = "ntfy_priority_default_help" if self.selected_ntfy_priority == 3 else "ntfy_priority_high_help"
        self.ntfy_priority_help_label.configure(text=self._t(key))


    def _ntfy_changed(self, *_args):
        self.ntfy_validation_state = "unverified"
        self._update_ntfy_state()

    def _update_ntfy_state(self):
        field_state = self._required_field_state((self.ntfy_server_var.get(), self.ntfy_topic_var.get()))
        selected = self.default_service_var.get() == "ntfy"
        if field_state == "empty":
            text, color = self._t("not_configured"), self._ui_colors["muted"]
        elif field_state == "incomplete":
            text, color = self._t("incomplete_service"), self._ui_colors["warning"]
        elif self.ntfy_validation_state == "invalid":
            text, color = self._t("service_error"), self._ui_colors["error"]
        elif selected:
            text, color = self._t("active_ready"), self._ui_colors["green"]
        else:
            text, color = self._t("configured_disabled"), self._ui_colors["muted"]
        self.ntfy_state.configure(text=text, fg=color)

    def _telegram_changed(self, *_args):
        self.telegram_validation_state = "unverified"
        self._update_telegram_state()

    def _update_telegram_state(self):
        field_state = self._required_field_state((self.telegram_bot_token_var.get(), self.telegram_chat_id_var.get()))
        selected = self.default_service_var.get() == "telegram"
        if field_state == "empty":
            text, color = self._t("not_configured"), self._ui_colors["muted"]
        elif field_state == "incomplete":
            text, color = self._t("incomplete_service"), self._ui_colors["warning"]
        elif self.telegram_validation_state == "invalid":
            text, color = self._t("service_error"), self._ui_colors["error"]
        elif selected:
            text, color = self._t("active_ready"), self._ui_colors["green"]
        else:
            text, color = self._t("configured_disabled"), self._ui_colors["muted"]
        self.telegram_state.configure(text=text, fg=color)

    def _update_priority_help(self):
        key = "priority_normal_help" if self.selected_priority == 0 else "priority_high_help"
        self.priority_help_label.configure(text=self._t(key))

    def _draw_autostart_toggle(self, *_args):
        """Draw the autostart switch consistently, independent of the Tk theme."""
        self._draw_switch(self.start_with_windows_toggle, bool(self.start_with_windows_var.get()))

    def _toggle_autostart(self, _event=None):
        """Toggle autostart from the switch or anywhere in its settings row."""
        self.start_with_windows_var.set(not self.start_with_windows_var.get())
        return "break"

    def _set_pushover_state(self, state):
        self.pushover_validation_state = state
        field_state = self._required_field_state((self.user_var.get(), self.token_var.get())) if hasattr(self, "user_var") else "empty"
        if field_state == "empty":
            self.pushover_state.configure(text=self._t("not_configured"), fg=self._ui_colors["muted"])
            return
        if field_state == "incomplete":
            self.pushover_state.configure(text=self._t("incomplete_service"), fg=self._ui_colors["warning"])
            return
        if getattr(self, "default_service_var", None) is not None and self.default_service_var.get() != "pushover":
            if state == "invalid":
                self.pushover_state.configure(text=self._t("credentials_invalid"), fg=self._ui_colors["error"])
            elif state == "unavailable":
                self.pushover_state.configure(text=self._t("credentials_unavailable"), fg=self._ui_colors["warning"])
            else:
                self.pushover_state.configure(text=self._t("configured_disabled"), fg=self._ui_colors["muted"])
            return
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
        if which == "user":
            entry = self.user_entry
        elif which == "token":
            entry = self.token_entry
        elif which == "ntfy":
            entry = self.ntfy_token_entry
        else:
            entry = self.telegram_bot_token_entry
        visible = entry.cget("show") == ""
        entry.configure(show="•" if visible else "")
        self._update_eye_button(which)

    def _update_eye_button(self, which):
        """Hebt das Auge dezent hervor, solange der jeweilige Schlüssel sichtbar ist."""
        if which == "user":
            entry, button = self.user_entry, self.user_eye
        elif which == "token":
            entry, button = self.token_entry, self.token_eye
        elif which == "ntfy":
            entry, button = self.ntfy_token_entry, self.ntfy_token_eye
        else:
            entry, button = self.telegram_bot_token_entry, self.telegram_token_eye
        button.configure(fg="#1769aa" if entry.cget("show") == "" else self._ui_colors["muted"])

    def _open_settings(self):
        self._show_window()

    def _fit_window_height(self):
        """Passt die feste Fensterhöhe ohne ungenutzten Leerraum an den Inhalt an."""
        self.update_idletasks()
        wanted_height = self.winfo_reqheight()
        self.minsize(570, wanted_height)
        self.geometry(f"570x{wanted_height}")

    def _open_config_folder(self, _event=None):
        """Open the configuration directory and select config.json when it exists."""
        APP_DIR.mkdir(parents=True, exist_ok=True)
        if os.name == "nt":
            if CONFIG_PATH.exists():
                subprocess.Popen(["explorer.exe", "/select,", str(CONFIG_PATH)])
            else:
                os.startfile(APP_DIR)
        else:
            webbrowser.open(APP_DIR.as_uri())

    def _current_config(self):
        self.config_data["pushover_user_key"] = self.user_var.get().strip()
        self.config_data["pushover_app_token"] = self.token_var.get().strip()
        self.config_data["ntfy_server"] = self.ntfy_server_var.get().strip().rstrip("/") or "https://ntfy.sh"
        self.config_data["ntfy_topic"] = self.ntfy_topic_var.get().strip().strip("/")
        self.config_data["ntfy_token"] = self.ntfy_token_var.get().strip()
        self.config_data["telegram_bot_token"] = self.telegram_bot_token_var.get().strip()
        self.config_data["telegram_chat_id"] = self.telegram_chat_id_var.get().strip()
        self.config_data["default_service"] = self.default_service_var.get()
        self._language_selected()
        self.config_data["language"] = self.selected_language_code
        self.config_data["pushover_priority"] = self.selected_priority
        self.config_data["ntfy_priority"] = self.selected_ntfy_priority
        self.config_data["start_with_windows"] = bool(self.start_with_windows_var.get())
        return self.config_data

    def _save(self):
        save_config(self._current_config())
        set_windows_startup(self.config_data.get("start_with_windows", False))
        pushover_configured = bool(self.config_data["pushover_user_key"] and self.config_data["pushover_app_token"])
        requested = self.config_data.get("language", "auto")
        self.language = windows_language() if requested == "auto" else requested
        self._refresh_language()
        if self.config_data.get("default_service") == "pushover" and pushover_configured:
            self._validate_pushover_async()
        else:
            self._set_pushover_state("unverified" if pushover_configured else "not_configured")
            self._update_ntfy_state()
            self._update_telegram_state()
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

    def _set_service_test_status(self, service, state, detail=""):
        label = {
            "pushover": self.pushover_test_status,
            "ntfy": self.ntfy_test_status,
            "telegram": self.telegram_test_status,
        }.get(service)
        if label is None:
            return
        if state == "running":
            text, color = self._t("test_running"), self._ui_colors["muted"]
        elif state == "valid":
            text, color = self._t("test_ok"), self._ui_colors["green"]
        else:
            text = self._t("test_failed", error=detail or self._t("service_error"))
            color = self._ui_colors["error"]
        label.configure(text=text, fg=color)
        self._fit_window_height()

    def _test_service(self, service):
        """Test the selected service with its current fields, even when inactive."""
        config = dict(self._current_config())
        config["default_service"] = service
        pushover_ready = bool(config["pushover_user_key"] and config["pushover_app_token"])
        ntfy_ready = bool(config.get("ntfy_server") and config.get("ntfy_topic"))
        telegram_ready = bool(config.get("telegram_bot_token") and config.get("telegram_chat_id"))
        ready = {"pushover": pushover_ready, "ntfy": ntfy_ready, "telegram": telegram_ready}.get(service, False)
        if not ready:
            service_name = {"pushover": "Pushover", "ntfy": "ntfy", "telegram": "Telegram"}.get(service, service)
            self._set_service_test_status(service, "invalid", self._t("missing_message", service=service_name))
            return
        self._set_service_test_status(service, "running")
        save_config(self._current_config())
        threading.Thread(
            target=self._send_selected_service,
            args=(config, self._t("connection_test"), self._t("connection_test_message")),
            daemon=True,
        ).start()

    def _send_selected_service(self, config, title, message):
        service = config.get("default_service", "pushover")
        if service == "ntfy":
            try:
                send_ntfy(config, title, message)
                self.service_validation_results.put(("ntfy", "valid", ""))
                self.messages.put(("status", self._t("ntfy_connected")))
                return True
            except Exception as exc:
                self.service_validation_results.put(("ntfy", "invalid", str(exc)))
                self.messages.put(("error", self._t("ntfy_failed", error=exc)))
                return False
        if service == "telegram":
            try:
                send_telegram(config, title, message)
                self.service_validation_results.put(("telegram", "valid", ""))
                self.messages.put(("status", self._t("telegram_connected")))
                return True
            except Exception as exc:
                self.service_validation_results.put(("telegram", "invalid", str(exc)))
                self.messages.put(("error", self._t("telegram_failed", error=exc)))
                return False
        self._send_and_report(config, title, message)
        return True

    def _send_and_report(self, config, title, message):
        last_error = None
        for attempt in range(1, 4):
            try:
                send_pushover(config, title, message, self.language)
                self.service_validation_results.put(("pushover", "valid", ""))
                self.messages.put(("status", self._t("pushover_connected")))
                return
            except Exception as exc:
                last_error = exc
                if attempt < 3:
                    time.sleep(2 * attempt)
        self.service_validation_results.put(("pushover", "invalid", str(last_error)))
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
        service = config.get("default_service", "pushover")
        readiness = {
            "pushover": bool(config.get("pushover_user_key") and config.get("pushover_app_token")),
            "ntfy": bool(config.get("ntfy_server") and config.get("ntfy_topic")),
            "telegram": bool(config.get("telegram_bot_token") and config.get("telegram_chat_id")),
        }
        ready = readiness.get(service, False)
        if ready:
            threading.Thread(target=self._send_selected_service, args=(config, title, message), daemon=True).start()
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
        try:
            while True:
                service, state, detail = self.service_validation_results.get_nowait()
                self._set_service_test_status(service, state, detail)
                if service == "pushover":
                    self.pushover_validation_state = state
                    self._set_pushover_state(state)
                elif service == "ntfy":
                    self.ntfy_validation_state = state
                    self._update_ntfy_state()
                elif service == "telegram":
                    self.telegram_validation_state = state
                    self._update_telegram_state()
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

    def _load_standard_tray_icon(self):
        """Load the bundled application icon without status recoloring."""
        if ICON_PATH.exists():
            return Image.open(ICON_PATH).convert("RGBA").resize((64, 64), Image.LANCZOS)
        return Image.new("RGBA", (64, 64), (0, 0, 0, 0))

    def _start_tray(self):
        try:
            import pystray
            image = self._load_standard_tray_icon()
            menu = pystray.Menu(
                pystray.MenuItem(lambda _item: self._tray_status_text(), lambda *_: None),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(self._t("tray_settings"), lambda *_: self.after(0, self._open_settings), default=True),
                pystray.MenuItem(self._t("tray_report_issue"), lambda *_: webbrowser.open(
                    f"https://github.com/{GITHUB_REPOSITORY}/issues"
                )),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(self._t("tray_quit"), lambda *_: self.after(0, self._quit_app)),
            )
            self.tray_icon = pystray.Icon("QueuePopNotifier", image, "Queue Pop Notifier", menu)
            self.tray_icon.run_detached()
        except Exception:
            self.tray_icon = None

    def _tray_status_text(self):
        kind = getattr(self, "current_status_kind", None)
        if kind == "error":
            status = self._t("check_disturbed")
        elif kind == "waiting":
            status = self._t("client_searching")
        elif kind is None:
            status = self._t("client_started")
        elif not self.wow_available:
            status = self._t("client_searching")
        else:
            status = self._t("monitoring_active")
        return self._t("tray_status", status=status)

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
        threading.Thread(target=self._download_update_worker, daemon=True).start()

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
    $env:PYINSTALLER_RESET_ENVIRONMENT = '1'
    $newProcess = Start-Process -FilePath $Target -PassThru
    Start-Sleep -Seconds 3
    if ($newProcess.HasExited) { throw 'Der aktualisierte Client wurde unerwartet beendet.' }
  } catch {
    if ($newProcess -and -not $newProcess.HasExited) {
      Stop-Process -Id $newProcess.Id -Force -ErrorAction SilentlyContinue
      $newProcess.WaitForExit(5000) | Out-Null
    }
    if (Test-Path -LiteralPath $Target) { Remove-Item -LiteralPath $Target -Force }
    Move-Item -LiteralPath $backup -Destination $Target -Force
    $env:PYINSTALLER_RESET_ENVIRONMENT = '1'
    Start-Process -FilePath $Target
    throw
  }
  # The update is already successful at this point. A locked backup is harmless
  # and will be removed by the client on a later start.
  Remove-Item -LiteralPath $backup -Force -ErrorAction SilentlyContinue
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
            subprocess.Popen(
                [
                    "powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                    "-File", str(updater_script), "-CurrentPid", str(os.getpid()),
                    "-Source", str(downloaded_exe), "-Target", str(target_exe),
                ],
                close_fds=True,
                creationflags=creation_flags,
            )
            self._terminate_for_update()
        except Exception as exc:
            self._update_install_failed(str(exc))

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
            parent=self,
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
