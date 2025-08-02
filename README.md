# LotusWiFi Enhanced - Steam Deck WiFi Monitor Plugin

An advanced Decky Loader plugin for Steam Deck that provides intelligent WiFi monitoring with automatic restart capabilities, real-time statistics, and persistent settings.

## ✨ Enhanced Features

### 🎯 Real-time Monitoring
- **Live Latency Display**: Shows current ping values with color-coded status
- **Configurable Thresholds**: Set custom ping thresholds (50-500ms) with visible numerical values
- **Adjustable Intervals**: Configure ping frequency (5-60 seconds) with real-time display
- **Custom Ping Targets**: Set any IP address or hostname for latency testing

### 🚀 Intelligent WiFi Management
- **Automatic WiFi Restart**: Uses `rfkill block/unblock` when ping exceeds threshold
- **Smart Timing**: 1-second delay between rfkill block and unblock operations
- **Manual Controls**: On-demand ping tests and WiFi restarts
- **Conditional Pinging**: Only pings at specified intervals when monitoring is active

### 📊 Advanced Statistics
- **Restart Counter**: Tracks total number of WiFi restarts
- **Last Ping Time**: Shows timestamp of most recent ping test
- **Last Restart Time**: Displays when WiFi was last restarted
- **Real-time Updates**: All statistics update live without page refresh

### 💾 Persistent Settings
- **Survives Standby**: Plugin state and settings persist through Steam Deck sleep/wake cycles
- **Auto-resume**: Monitoring automatically restarts if it was enabled before standby
- **Settings Backup**: All configurations saved to persistent storage

### 🎮 Steam Deck Optimized UI
- **Keyboard Fix**: Prevents Steam Deck virtual keyboard from appearing under the plugin interface
- **Proper Focus Management**: Smooth scrolling and focus handling for touch/controller input
- **Color-coded Status**: 
  - 🟢 Green: Normal latency (≤ threshold)
  - 🟠 Orange: High latency (> threshold)  
  - 🔴 Red: Ping failed
- **Responsive Layout**: Optimized for Steam Deck screen size and input methods

## 🔧 Installation

### Via Decky Store (Recommended)
1. Install Decky Loader on your Steam Deck
2. Open Decky Store
3. Search for "LotusWiFi"
4. Install the plugin

### Manual Installation
1. Download the latest release
2. Extract to your Decky Loader plugins directory: 
   ```
   ~/.local/share/Steam/steamapps/common/SteamDeck/plugins/
   ```
3. Restart Decky Loader or reload plugins

## 📖 Usage Guide

### Basic Setup
1. Open the LotusWiFi plugin from the Decky Loader menu
2. Configure your preferred settings:
   - **Ping Threshold**: Maximum acceptable latency (default: 100ms)
   - **Ping Interval**: Time between checks (default: 10s)
   - **Ping Host**: Target for testing (default: 8.8.8.8)
   - **Auto Restart**: Enable/disable automatic WiFi restarts
3. Click "Start Monitoring" to begin

### Understanding the Interface

#### Status Section
- **Status**: Shows if monitoring is RUNNING or STOPPED
- **Current Latency**: Real-time ping result with color coding
- **Last Ping Time**: Timestamp of most recent ping test
- **WiFi Restarts**: Total number of restarts performed
- **Last Restart**: When WiFi was last restarted (if applicable)

#### Controls
- **Start/Stop Monitoring**: Toggle the monitoring service
- **Manual Ping Test**: Perform immediate ping without waiting for next interval
- **Manual WiFi Restart**: Force WiFi restart regardless of current latency
- **Reset Statistics**: Clear restart counter and timestamps

#### Settings Section
- **Ping Threshold Slider**: Adjust trigger point with real-time value display
- **Ping Interval Slider**: Set check frequency with live updates
- **Ping Host Field**: Enter custom IP address or hostname
- **Auto Restart Toggle**: Enable/disable automatic WiFi management

## 🔍 Technical Details

### How It Works
1. **Monitoring Loop**: Runs in background thread, pinging target at specified intervals
2. **Latency Check**: Compares ping results against user-defined threshold
3. **WiFi Restart**: When threshold exceeded, uses `rfkill block wifi` → wait 1s → `rfkill unblock wifi`
4. **State Persistence**: Settings and monitoring state saved to disk, restored after standby/reboot

### System Requirements
- Steam Deck with Decky Loader installed
- Root privileges (plugin uses `_root` flag)
- `ping` utility (pre-installed on SteamOS)
- `rfkill` utility (pre-installed on SteamOS)

### File Locations
- **Settings**: `~/.local/share/decky-loader/settings/lotus_wifi_settings.json`
- **Logs**: Available through Decky Loader log viewer
- **Plugin Files**: `~/.local/share/Steam/steamapps/common/SteamDeck/plugins/LotusWiFi/`

## ⚙️ Advanced Configuration

### Custom Ping Targets
The plugin supports various ping targets:
- **Public DNS**: `8.8.8.8` (Google), `1.1.1.1` (Cloudflare)
- **Local Gateway**: Your router's IP (e.g., `192.168.1.1`)
- **Game Servers**: Specific server IPs for your favorite games
- **Hostnames**: Domain names like `google.com` or `steamcommunity.com`

### Optimal Settings
- **Gaming**: 50-100ms threshold, 5-10s interval
- **General Use**: 100-200ms threshold, 10-30s interval
- **Battery Saving**: 200ms+ threshold, 30-60s interval

### Troubleshooting

#### Plugin Not Starting Monitor
- Check Decky Loader logs for error messages
- Verify `ping` and `rfkill` commands work in terminal
- Ensure plugin has root privileges

#### High False Positives
- Increase ping threshold (current networks may have higher baseline latency)
- Change ping target to closer server
- Increase ping interval to reduce sensitivity

#### Settings Not Persisting
- Check file permissions on settings directory
- Verify disk space availability
- Restart Decky Loader if settings appear corrupted

#### Keyboard Issues
- Plugin automatically handles focus to prevent keyboard overlay
- If keyboard still appears, try using controller navigation
- Restart Steam if input issues persist

## 🔄 Standby/Resume Behavior

The enhanced plugin handles Steam Deck standby gracefully:

1. **Before Standby**: Settings and monitoring state saved to disk
2. **During Standby**: Background monitoring thread suspended
3. **After Resume**: 
   - Settings automatically restored
   - Monitoring resumes if it was previously enabled
   - Statistics and counters preserved
   - First ping may take slightly longer as network reconnects

## 🚨 Important Notes

### Root Privileges
This plugin requires root access to execute `rfkill` commands. The `_root` flag in `plugin.json` ensures proper permissions.

### Network Interruption
WiFi restarts cause brief network disconnections (1-5 seconds). This is normal and necessary for resolving connection issues.

### Battery Impact
Continuous monitoring has minimal battery impact, but frequent WiFi restarts may slightly reduce battery life. Adjust intervals accordingly.

## 🛠️ Development

### Building from Source
```bash
# Clone repository
git clone https://github.com/itsmikethetech/LotusWiFi.git
cd LotusWiFi

# Install dependencies
pnpm install

# Build plugin
pnpm run build

# Development mode with hot reload
pnpm run watch
```

### Project Structure
```
LotusWiFi/
├── main.py                 # Python backend with monitoring logic
├── src/
│   └── index.tsx          # React frontend component
├── plugin.json           # Plugin metadata and permissions
├── package.json          # Node.js dependencies and scripts
└── defaults/
    └── settings.json     # Default configuration values
```

### API Methods
The plugin exposes these methods for frontend communication:

- `get_status()` - Returns current monitoring status and statistics
- `get_settings()` - Returns current plugin configuration
- `update_settings(settings)` - Updates plugin configuration
- `start_monitoring()` - Begins WiFi monitoring
- `stop_monitoring()` - Stops WiFi monitoring
- `manual_ping()` - Performs single ping test
- `manual_restart()` - Forces WiFi restart
- `reset_stats()` - Clears statistics counters

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

### Areas for Improvement
- Additional network diagnostics
- Custom notification sounds
- Integration with other network tools
- Advanced logging and debugging features
- Multiple ping target support

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Original `wifitoggler` script by wanderingxlotus
- Decky Loader team for the plugin framework
- Steam Deck community for testing and feedback

## 📞 Support

If you encounter issues or have questions:

1. **Check the logs**: Use Decky Loader's log viewer for error messages
2. **Verify commands**: Test `ping` and `rfkill` work in terminal
3. **GitHub Issues**: Submit detailed bug reports at [GitHub Issues](https://github.com/itsmikethetech/LotusWiFi/issues)
4. **Community**: Join discussions in Steam Deck modding communities

## 🔮 Roadmap

### Planned Features
- **Multiple Ping Targets**: Test multiple servers simultaneously
- **Network Quality Metrics**: Jitter, packet loss, and connection stability
- **Custom Notifications**: Audio/visual alerts for network events
- **Scheduling**: Time-based monitoring profiles
- **Advanced Logging**: Detailed network performance history
- **Integration**: Compatibility with other networking plugins

### Version History
- **v2.0.0**: Enhanced UI, persistent settings, standby support, real-time statistics
- **v1.x.x**: Original wifitoggler wrapper implementation

---

**⚡ Enjoy stable WiFi gaming on your Steam Deck! ⚡**
# WiFiDiagnostic
