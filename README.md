# Queue Pop Notifier

[![Windows](https://img.shields.io/badge/Windows-Supported-0078D4)](#requirements)
[![Pushover](https://img.shields.io/badge/Pushover-Supported-2ea44f)](https://pushover.net/)
[![ntfy](https://img.shields.io/badge/ntfy-Supported-2ea44f)](https://ntfy.sh/)
[![Telegram](https://img.shields.io/badge/Telegram-Supported-2ea44f)](https://telegram.org/)
[![WoW Add-on](https://img.shields.io/curseforge/v/1638570?label=WoW%20Add-on&color=C79C6E)](https://www.curseforge.com/wow/addons/queue-pop-notifier)

![Services](integrations.png)

> **Never miss a World of Warcraft queue pop again.**

Queue Pop Notifier sends an instant notification to your smartphone when your World of Warcraft queue is ready, even if you are away from your computer.

## New in 0.4.0 — more notification services

**Pushover is no longer the only option. Queue Pop Notifier now also supports ntfy and Telegram.**

Choose the notification service that fits you best:

* **Pushover** — simple and reliable push notifications
* **ntfy** — lightweight notifications with free public or self-hosted servers
* **Telegram** — queue alerts directly through your Telegram bot

Only one service is active at a time, and each provider can be configured and tested directly in the Windows client.

The WoW add-on detects the queue pop and passes the event to the lightweight Windows desktop client. The client then sends the notification through your selected service.

![User interface](interface.png)

## Features

* Instant smartphone notifications for World of Warcraft queue pops
* **Pushover, ntfy and Telegram support**
* Automatic queue detection through the WoW add-on
* Lightweight Windows desktop client
* Runs quietly in the Windows system tray
* Automatic client updates
* Optional automatic startup with Windows
* Provider-specific connection testing
* Local storage of credentials and settings

## How It Works

1. Your World of Warcraft queue becomes ready.
2. The add-on detects the queue pop.
3. The desktop client receives the event.
4. Your selected notification service sends the alert to your smartphone.

![How Queue Pop Notifier works](client_howto.png)

You can step away from your computer without constantly watching the screen.

## Requirements

* World of Warcraft Classic with the [Queue Pop Notifier add-on](https://www.curseforge.com/wow/addons/queue-pop-notifier) installed
* Windows 10 or Windows 11
* The Queue Pop Notifier desktop client
* At least one supported notification service: [Pushover](https://pushover.net/), [ntfy](https://ntfy.sh/) or [Telegram](https://telegram.org/)

## Desktop Client

The desktop client runs in the Windows system tray and remains unobtrusive during normal use. Configure Pushover, ntfy or Telegram once, select it as the active service, and the client handles queue notifications automatically.

## Optional queue-pop sound

Pushover users can use the original queue-pop sound for notifications on their phone.

1. [Download the Queue Pop sound](queue_popup.mp3).
2. Open your [Pushover dashboard](https://pushover.net).
3. Under **Your Custom Sounds**, click **Upload a Sound**.
4. Select the downloaded sound file and give it a short name, such as **Queue**.
5. After uploading, select **Queue** as the notification sound in your Pushover app.

Your phone will now play the queue-pop sound whenever a queue is ready.

## Privacy and Local Storage

Notification-service credentials and application settings are stored locally under:

```text
%APPDATA%\QueuePopNotifier
```

Personal data and credentials are never included in the repository or distributed build artifacts.
