# WiFiDiagnostic - Steam Deck WiFi Monitor Plugin
An advanced Decky Loader plugin for Steam Deck that provides intelligent WiFi monitoring with multiple automatic restart methods, real-time latency statistics, and Moonlight stream detection. Claude AI and Gemini were used to develop this plugin since I don't know a thing about coding. I wanted to either fix the wifi issues with the OLED Steam Deck, provide a workaround, or have a tool to gather potentially useful information for Valve. 


#Features

Real-time Monitoring
 * Live Latency Display: Shows the current ping to your selected target with a color-coded status indicator.
 * Configurable Thresholds: Set a custom ping threshold (0-100ms) to define what constitutes "high latency".
 * Adjustable Intervals: Configure how often the plugin checks your connection (1-15 seconds).
 * Selectable Ping Targets: Choose your ping target from a dropdown menu, including automatic router detection and public DNS servers.

Intelligent WiFi Management
 * Automatic WiFi Restart: Automatically restarts the WiFi adapter when the ping exceeds your threshold or fails completely.
 * Intelligent Moonlight Detection: Automatically detects when a Moonlight stream is active to use the safest restart method and prevent stream detachment.
 * Auto-Start with Moonlight: Can be configured to automatically start and stop monitoring whenever a Moonlight session begins or ends.
 * Multiple Restart Methods:
   * Gentle (D-Bus/nmcli): A software-level restart that is safe for game streaming and is used automatically when Moonlight is detected.
   * Forceful (rfkill): A hardware-level power cycle for resolving more stubborn connection issues.

Status and Diagnostics
 * Live Status: Clear "RUNNING" or "STOPPED" indicator.
 * Detected Ping Target: Shows the actual IP address being used for monitoring, even in "auto" mode.
 * Professional Diagnostic Reports: Generate comprehensive diagnostic logs with detailed hardware, driver, and network information for advanced troubleshooting.
 * Log Management: Automatically keeps the 10 most recent diagnostic logs, deleting the oldest when a new one is created.

Persistent Settings
 * Survives Standby: All your settings persist through the Steam Deck's sleep/wake cycles.
 * Settings Saved: All configurations are saved to a file for persistence across reboots.

Steam Deck Optimized UI
 * Keyboard-on-Top Fix: A fix is included to ensure the Steam Deck virtual keyboard always appears on top of the Quick Access Menu when using the plugin.
 * Color-coded Latency:
   * 🟢 Green: Normal latency (≤ threshold)
   * 🟠 Orange: High latency (> threshold)
   * 🔴 Red: Ping failed
 * Responsive Layout: Optimized for the Steam Deck's screen size and input methods.

Installation
 * Ensure you have Decky Loader installed.
 * Go to the Decky Store.
 * Search for "WiFiDiagnostic" and install.

Usage Guide
 * Open the WiFiDiagnostic plugin from the Decky Loader menu.
 * Monitor Section:
   * Press "Start Monitoring" to begin.
   * View the live "Status" and "Latency".
   * Use "Force WiFi Restart" to manually restart the connection at any time.
 * Settings Section:
   * Ping Target: Select "Auto-Detect Router" (recommended) or a public DNS for testing.
   * Toggles: Enable or disable "Auto-Start with Moonlight" and "Auto Restart on High Ping".
   * Sliders: Adjust the "Ping Threshold" and "Ping Interval".
 * Restart Method Section:
   * Select your preferred default restart method. Note that "Gentle" will always be used if Moonlight is running.

Technical Details
 * Monitoring Loop: A background thread pings the target at your specified interval.
 * Latency Check: It compares ping results against your defined threshold.
 * WiFi Restart: When the threshold is exceeded, it uses the selected method (nmcli radio wifi off/on OR Dbus to restart the adapter.
 * Root Privileges: The plugin uses the _root flag to execute network commands. 
