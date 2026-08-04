# Queue Pop Notifier

**Never miss a World of Warcraft queue pop again.**

Queue Pop Notifier sends a notification to your smartphone as soon as your queue is ready—even when you are away from your computer.

The World of Warcraft add-on detects the queue pop, while the lightweight Windows desktop client forwards the notification through Pushover. The client runs quietly in the system tray and only requires a one-time setup.

![How QueuePopNotifier works](queuepop-client-flow.png)

## Desktop Client

The Windows executable is built reproducibly using GitHub Actions. All Pushover credentials and application settings are stored locally under:

```text
%APPDATA%\QueuePopNotifier
```

Personal data is never included in the repository or distributed build artifacts.
