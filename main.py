import os
import sys
import json
import logging
import subprocess
import time
import threading
import re
import glob
from datetime import datetime
from typing import Dict, Any, Optional, List

sys.path.append(os.path.join(os.path.dirname(__file__), "py_modules"))
import decky_plugin

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# The single, global instance of our plugin's logic
plugin_logic_instance: Optional['WiFiDiagnosticPlugin'] = None

class DiagnosticReporter:
    def __init__(self, settings_dir):
        self.logs_dir = os.path.join(settings_dir, "diagnostic_logs")
        self.max_logs = 10
        os.makedirs(self.logs_dir, exist_ok=True)

    def _run_command(self, command, timeout=10, shell=False):
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=timeout, shell=shell, check=False)
            return {"success": result.returncode == 0, "stdout": result.stdout, "stderr": result.stderr}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def collect_diagnostic_info(self):
        logger.info("Starting comprehensive WiFi diagnostic collection...")
        info = {"report_metadata": {"timestamp": datetime.now().isoformat()}}
        info["system_analysis"] = self._run_command("uname -a")
        info["network_configuration"] = self._run_command(["ip", "addr"])
        info["routing_table"] = self._run_command(["ip", "route"])
        info["nmcli_status"] = self._run_command(["nmcli", "general", "status"])
        info["nmcli_devices"] = self._run_command(["nmcli", "device", "status"])
        info["dmesg_wifi"] = self._run_command("dmesg | grep -i -E 'wifi|wlan|iwl|firmware' | tail -n 50", shell=True)
        info["journal_networkmanager"] = self._run_command("journalctl -u NetworkManager --no-pager -n 100", shell=True)
        info["pci_info"] = self._run_command("lspci -nnv | grep -A 20 -i network", shell=True)
        info["lsmod"] = self._run_command("lsmod")
        logger.info("Diagnostic collection completed.")
        return info

    def generate_diagnostic_report(self):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"wifi_diagnostic_{timestamp}.json"
        filepath = os.path.join(self.logs_dir, filename)
        try:
            diagnostic_info = self.collect_diagnostic_info()
            with open(filepath, 'w') as f: json.dump(diagnostic_info, f, indent=2)
            self.cleanup_old_logs()
            return {"success": True}
        except Exception as e:
            logger.error(f"Error generating report: {e}"); return {"success": False, "error": str(e)}

    def cleanup_old_logs(self):
        try:
            log_files = sorted(glob.glob(os.path.join(self.logs_dir, "*.json")), key=os.path.getctime)
            if len(log_files) > self.max_logs:
                logger.info(f"Found {len(log_files)} reports (max {self.max_logs}). Cleaning up.")
                while len(log_files) > self.max_logs:
                    oldest = log_files.pop(0); os.remove(oldest)
                    logger.info(f"Deleted old report: {os.path.basename(oldest)}")
        except Exception as e:
            logger.error(f"Error cleaning up logs: {e}")

    def get_log_list(self) -> List[Dict[str, Any]]:
        try:
            log_files = sorted(glob.glob(os.path.join(self.logs_dir, "*.json")), key=os.path.getctime, reverse=True)
            logs = []
            for f in log_files:
                try:
                    ts_str = os.path.basename(f).replace("wifi_diagnostic_", "").replace(".json", "")
                    ts = datetime.strptime(ts_str, "%Y-%m-%d_%H-%M-%S")
                    logs.append({"filename": os.path.basename(f), "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"), "size": os.path.getsize(f)})
                except (ValueError, IndexError): continue
            return logs
        except Exception as e:
            logger.error(f"Error getting log list: {e}"); return []

    def delete_all_logs(self):
        try:
            for f in glob.glob(os.path.join(self.logs_dir, "*.json")): os.remove(f)
            return True
        except Exception as e:
            logger.error(f"Error deleting logs: {e}"); return False

class WiFiDiagnosticPlugin:
    def __init__(self):
        self.settings_dir = decky_plugin.DECKY_PLUGIN_SETTINGS_DIR
        self.settings_file = os.path.join(self.settings_dir, "settings.json")
        self.settings = {}
        self.status = {"is_running": False, "restart_count": 0, "current_latency": None, "ping_failed": False, "is_moonlight_running": False, "detected_ping_host": "N/A"}

        self.stop_event = threading.Event()
        self.monitor_thread: Optional[threading.Thread] = None
        self.watcher_thread: Optional[threading.Thread] = None
        self.monitoring_started_by_moonlight = False
        self.best_ping_host_cache = None
        self.diagnostic_reporter = DiagnosticReporter(self.settings_dir)

        self.load_settings()

        self.watcher_thread = threading.Thread(target=self.moonlight_watcher_loop, daemon=True); self.watcher_thread.start()

    def _run_command(self, command, timeout=10, shell=False):
        cmd_str = ' '.join(command) if isinstance(command, list) else command
        try:
            result = subprocess.run(
                command, capture_output=True, text=True, timeout=timeout, shell=shell, check=False
            )
            if result.returncode != 0:
                logger.warning(f"Command failed with code {result.returncode}. Stderr: {result.stderr.strip()}")
                return {"success": False, "stdout": result.stdout, "stderr": result.stderr}
            return {"success": True, "stdout": result.stdout, "stderr": result.stderr}
        except Exception as e:
            logger.error(f"An unexpected error occurred running command '{cmd_str}': {e}")
            return {"success": False, "error": str(e)}

    def load_settings(self):
        defaults = {"ping_host": "auto", "ping_threshold": 50, "ping_interval": 5, "auto_restart": True, "restartMethod": "dbus", "auto_start_with_moonlight": True}
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f: self.settings = json.load(f)
                for key, value in defaults.items():
                    if key not in self.settings: self.settings[key] = value
            else: self.settings = defaults; self.save_settings()
        except: self.settings = defaults

    def save_settings(self):
        try:
            with open(self.settings_file, 'w') as f: json.dump(self.settings, f, indent=4)
        except: pass

    def update_and_save_settings(self, **kwargs):
        if 'ping_host' in kwargs and kwargs['ping_host'] != self.settings.get('ping_host'): self.best_ping_host_cache = None
        self.settings.update(kwargs); self.save_settings()

    def _is_moonlight_running(self):
        is_running = self._run_command(["pgrep", "-x", "moonlight"])["success"]
        if is_running != self.status.get('is_moonlight_running'): self.status['is_moonlight_running'] = is_running
        return is_running

    def moonlight_watcher_loop(self):
        while not self.stop_event.is_set():
            if self.settings.get("auto_start_with_moonlight"):
                is_active = self._is_moonlight_running()
                if is_active and not self.status['is_running']: self.start_monitoring(True)
                elif not is_active and self.status['is_running'] and self.monitoring_started_by_moonlight: self.stop_monitoring()
            time.sleep(10)

    def restart_wifi(self):
        method = self.settings.get("restartMethod", "dbus")
        if self._is_moonlight_running(): method = "dbus"

        success = False
        if method == "dbus":
            logger.info("Using Moonlight-safe D-Bus method. Success will be assumed for counter.")
            cmd_off = "dbus-send --system --dest=org.freedesktop.NetworkManager /org/freedesktop/NetworkManager org.freedesktop.DBus.Properties.Set string:org.freedesktop.NetworkManager string:WirelessEnabled variant:boolean:false"
            cmd_on = "dbus-send --system --dest=org.freedesktop.NetworkManager /org/freedesktop/NetworkManager org.freedesktop.DBus.Properties.Set string:org.freedesktop.NetworkManager string:WirelessEnabled variant:boolean:true"
            self._run_command(cmd_off, shell=True); time.sleep(2); self._run_command(cmd_on, shell=True)
            success = True # Explicitly assume success for D-Bus to ensure counter increments
        elif method == "rfkill":
            if self._run_command(["rfkill", "block", "wifi"])['success']:
                time.sleep(1); success = self._run_command(["rfkill", "unblock", "wifi"])['success']

        if success:
            logger.info("WiFi restart process marked as successful. Incrementing counter.")
            self.status['restart_count'] += 1; self.best_ping_host_cache = None
        else:
            logger.error(f"WiFi restart with method '{method}' failed.")

    def start_monitoring(self, started_by_watcher=False):
        if self.status['is_running']: return
        self.stop_event.clear(); self.status['is_running'] = True; self.monitoring_started_by_moonlight = started_by_watcher
        self.monitor_thread = threading.Thread(target=self.monitor_wifi_loop, daemon=True); self.monitor_thread.start()

    def stop_monitoring(self):
        if not self.status['is_running']: return
        self.stop_event.set()
        if self.monitor_thread and self.monitor_thread.is_alive(): self.monitor_thread.join(timeout=2)
        self.status['is_running'] = False; self.status['current_latency'] = None
        self.status['ping_failed'] = False; self.status['restart_count'] = 0; self.monitoring_started_by_moonlight = False

    def monitor_wifi_loop(self):
        while not self.stop_event.is_set():
            host = self.get_ping_host()
            if not host: self.status['detected_ping_host'] = "Detecting..."; time.sleep(5); continue
            latency, ping_success = self.ping_host(host)
            self.status['current_latency'] = latency; self.status['ping_failed'] = not ping_success
            if self.settings.get("auto_restart") and (not ping_success or (latency is not None and latency > self.settings["ping_threshold"])):
                self.restart_wifi()
            time.sleep(self.settings.get("ping_interval", 5))

    def get_ping_host(self):
        if self.settings.get('ping_host') != 'auto':
            self.status['detected_ping_host'] = self.settings.get('ping_host'); return self.settings.get('ping_host')
        if self.best_ping_host_cache: return self.best_ping_host_cache
        result = self._run_command(["ip", "route", "show", "default"])
        if result['success'] and result.get('stdout'):
            match = re.search(r'default via ([\d\.]+)', result['stdout'])
            if match: ip = match.group(1); self.best_ping_host_cache = ip; self.status['detected_ping_host'] = f"{ip} (Gateway)"; return ip
        return None

    def ping_host(self, host):
        result = self._run_command(["ping", "-c", "1", "-W", "2", host])
        if result["success"] and result.get('stdout'):
            match = re.search(r"time=([\d.]+)", result["stdout"]);
            if match: return float(match.group(1)), True
        return None, False

    def unload(self):
        self.stop_event.set()

class Plugin:
    async def _main(self):
        global plugin_logic_instance
        if plugin_logic_instance is None:
            plugin_logic_instance = WiFiDiagnosticPlugin()
    async def _unload(self):
        if plugin_logic_instance: plugin_logic_instance.unload()
    async def get_status(self): return plugin_logic_instance.status
    async def get_settings(self): return plugin_logic_instance.settings
    async def start_monitoring(self): plugin_logic_instance.start_monitoring()
    async def stop_monitoring(self): plugin_logic_instance.stop_monitoring()
    async def force_wifi_restart(self): threading.Thread(target=plugin_logic_instance.restart_wifi).start()
    async def update_settings(self, **kwargs):
        if plugin_logic_instance:
            plugin_logic_instance.update_and_save_settings(**kwargs)

    async def generate_diagnostic_report(self): return plugin_logic_instance.diagnostic_reporter.generate_diagnostic_report()
    async def get_diagnostic_logs(self): return plugin_logic_instance.diagnostic_reporter.get_log_list()
    async def delete_all_logs(self): return plugin_logic_instance.diagnostic_reporter.delete_all_logs()
