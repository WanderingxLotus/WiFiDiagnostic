import React, { VFC, useState, useEffect, useRef } from "react";
import {
  definePlugin,
  ServerAPI,
  PanelSection,
  PanelSectionRow,
  ButtonItem,
  SliderField,
  ToggleField,
  Field,
  Focusable,
  Dropdown,
  TextField,
} from "decky-frontend-lib";
import { FaWifi, FaInfoCircle, FaStream, FaSyncAlt, FaBug, FaTrash } from "react-icons/fa";

// CSS for Keyboard Fix
const keyboardFixCSS = `[class*="virtualkeyboard_VirtualKeyboard_"] { z-index: 99999 !important; }`;

interface PluginStatus {
  is_running: boolean;
  restart_count: number;
  current_latency: number | null;
  ping_failed: boolean;
  is_moonlight_running: boolean;
  detected_ping_host: string;
}

type RestartMethod = 'rfkill' | 'dbus';
interface PluginSettings {
  ping_host: string;
  ping_threshold: number;
  ping_interval: number;
  auto_restart: boolean;
  restartMethod: RestartMethod;
  auto_start_with_moonlight: boolean;
}

interface DiagnosticLog {
  filename: string;
  timestamp: string;
  size: number;
}

const hostOptions = [
  { label: "Auto-Detect Router", data: "auto" },
{ label: "Google DNS (8.8.8.8)", data: "8.8.8.8" },
{ label: "Cloudflare DNS (1.1.1.1)", data: "1.1.1.1" },
];

const Content: VFC<{ serverAPI: ServerAPI }> = ({ serverAPI }) => {
  const [status, setStatus] = useState<PluginStatus>({is_running: false, restart_count: 0, current_latency: null, ping_failed: false, is_moonlight_running: false, detected_ping_host: "N/A"});
  const [settings, setSettings] = useState<PluginSettings>({ping_host: "auto", ping_threshold: 50, ping_interval: 5, auto_restart: true, restartMethod: 'dbus', auto_start_with_moonlight: true});
  const [diagnosticLogs, setDiagnosticLogs] = useState<DiagnosticLog[]>([]);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const userSelectedMethod = useRef<RestartMethod>('dbus');
  const restartCountRef = useRef(0);

  useEffect(() => {
    const style = document.createElement('style');
    style.id = 'wifidiagnostic-keyboard-fix';
    style.textContent = keyboardFixCSS;
    document.head.appendChild(style);
    return () => { document.head.removeChild(style); };
  }, []);

  useEffect(() => {
    const initializePlugin = async () => {
      const settingsResult = await serverAPI.callPluginMethod("get_settings", {});
      if (settingsResult.success) {
        const loadedSettings = settingsResult.result as PluginSettings;
        setSettings(loadedSettings);
        userSelectedMethod.current = loadedSettings.restartMethod;
      }
      const statusResult = await serverAPI.callPluginMethod("get_status", {});
      if (statusResult.success) {
        const newStatus = statusResult.result as PluginStatus;
        setStatus(newStatus);
        restartCountRef.current = newStatus.restart_count;
      }
      await refreshLogs();
      setIsLoading(false);
    };
    initializePlugin();
    const interval = setInterval(async () => {
      const statusResult = await serverAPI.callPluginMethod("get_status", {});
      if (statusResult.success) setStatus(statusResult.result as PluginStatus);
    }, 2000);
      return () => clearInterval(interval);
  }, [serverAPI]);

  useEffect(() => {
    if (status.is_moonlight_running) {
      if (settings.restartMethod !== 'dbus') {
        userSelectedMethod.current = settings.restartMethod;
        setSettings(s => ({...s, restartMethod: 'dbus'}));
      }
    } else {
      if (settings.restartMethod === 'dbus' && userSelectedMethod.current !== 'dbus') {
        setSettings(s => ({...s, restartMethod: userSelectedMethod.current}));
      }
    }
  }, [status.is_moonlight_running, settings.restartMethod]);

  useEffect(() => {
    if (restartCountRef.current < status.restart_count) {
      serverAPI.toaster.toast({ title: "WiFiDiagnostic", body: "WiFi was successfully restarted." });
    }
    restartCountRef.current = status.restart_count;
  }, [status.restart_count]);

  const updateSetting = async (key: keyof PluginSettings, value: any) => {
    if (key === 'restartMethod' && !status.is_moonlight_running) userSelectedMethod.current = value;
    setSettings(s => ({...s, [key]: value}));
    await serverAPI.callPluginMethod("update_settings", { [key]: value });
  };

  const forceRestart = () => {
    serverAPI.callPluginMethod("force_wifi_restart", {});
    serverAPI.toaster.toast({ title: "WiFiDiagnostic", body: "Manual restart command sent." });
  };
  const toggleMonitoring = () => serverAPI.callPluginMethod(status.is_running ? "stop_monitoring" : "start_monitoring", {});

  const refreshLogs = async () => {
    const logsResult = await serverAPI.callPluginMethod("get_diagnostic_logs", {});
    if (logsResult.success) {
      setDiagnosticLogs(logsResult.result as DiagnosticLog[]);
    }
  };

  const generateReport = async () => {
    setIsGeneratingReport(true);
    const result = await serverAPI.callPluginMethod("generate_diagnostic_report", {});
    if (result.success) {
      serverAPI.toaster.toast({ title: "WiFiDiagnostic", body: "Diagnostic report generated."});
      await refreshLogs();
    } else {
      serverAPI.toaster.toast({ title: "WiFiDiagnostic Error", body: "Failed to generate report."});
    }
    setIsGeneratingReport(false);
  };

  const clearAllLogs = async () => {
    if ((await serverAPI.callPluginMethod("delete_all_logs", {})).success) {
      serverAPI.toaster.toast({ title: "WiFiDiagnostic", body: "All reports cleared."});
      setDiagnosticLogs([]);
    }
  };

  const getLatencyColor = (l: number | null) => l === null || status.ping_failed ? "#ff4444" : l <= settings.ping_threshold ? "#44ff44" : "#ffaa44";
  const getPingStatusText = () => status.ping_failed ? "FAIL" : status.current_latency === null ? "N/A" : `${status.current_latency.toFixed(1)}ms`;
  const formatFileSize = (b: number) => b < 1024 ? `${b} B` : b < 1048576 ? `${(b/1024).toFixed(1)} KB` : `${(b/1048576).toFixed(1)} MB`;

  if (isLoading) return <div>Loading...</div>;

  return (
    <Focusable>
    <PanelSection title="Monitor">
    <PanelSectionRow>
    <Field label="Status"><div style={{ color: status.is_running ? "#44ff44" : "#ffaa44", fontWeight: "bold" }}>{status.is_running ? "RUNNING" : "STOPPED"}</div></Field>
    <Field label="Latency"><div style={{ color: getLatencyColor(status.current_latency), fontWeight: "bold" }}>{getPingStatusText()}</div></Field>
    </PanelSectionRow>
    {status.is_running && <PanelSectionRow><Field label="Ping Target"><div style={{fontWeight: 'bold'}}>{status.detected_ping_host}</div></Field></PanelSectionRow>}
    {status.is_moonlight_running && <PanelSectionRow><Field label="Streaming"><div style={{ color: "#00ffff", fontWeight: "bold" }}>Moonlight Active</div></Field></PanelSectionRow>}
    <PanelSectionRow><Field label="WiFi Restarts"><div style={{fontWeight: 'bold'}}>{status.restart_count}</div></Field></PanelSectionRow>
    <PanelSectionRow><ButtonItem layout="below" onClick={toggleMonitoring}>{status.is_running ? "Stop Monitoring" : "Start Monitoring"}</ButtonItem></PanelSectionRow>
    <PanelSectionRow><ButtonItem layout="below" onClick={forceRestart}><FaSyncAlt /> Force WiFi Restart</ButtonItem></PanelSectionRow>
    </PanelSection>
    <PanelSection title="Settings">
    <PanelSectionRow>
    <Field label="Ping Target">
    <Dropdown
    menuLabel="Select Ping Target"
    rgOptions={hostOptions}
    selectedOption={settings.ping_host}
    onChange={(option: { data: string; }) => { updateSetting('ping_host', option.data); }}
    />
    </Field>
    </PanelSectionRow>
    <ToggleField label="Auto-Start with Moonlight" checked={settings.auto_start_with_moonlight} onChange={(v) => updateSetting('auto_start_with_moonlight', v)} />
    <ToggleField label="Auto Restart on High Ping" checked={settings.auto_restart} onChange={(v) => updateSetting('auto_restart', v)} />
    <SliderField label={`Ping Threshold: ${settings.ping_threshold}ms`} value={settings.ping_threshold} min={0} max={100} step={1} showValue={false} onChange={(v) => updateSetting('ping_threshold', v)} />
    <SliderField label={`Ping Interval: ${settings.ping_interval}s`} value={settings.ping_interval} min={1} max={15} step={1} showValue={false} onChange={(v) => updateSetting('ping_interval', v)} />
    </PanelSection>
    <PanelSection title="Restart Method">
    <PanelSectionRow><Field label="" icon={<FaInfoCircle/>}><div style={{fontSize: "11px", color: "#8b8d8f", lineHeight: '1.2'}}>Gentle method is auto-selected when Moonlight is active.</div></Field></PanelSectionRow>
    <ToggleField label="Gentle (D-Bus)" checked={settings.restartMethod === 'dbus'} onChange={() => updateSetting('restartMethod', 'dbus')} />
    <ToggleField label="Forceful (rfkill)" disabled={status.is_moonlight_running} checked={settings.restartMethod === 'rfkill'} onChange={() => updateSetting('restartMethod', 'rfkill')} />
    </PanelSection>
    <PanelSection title="WiFi Diagnostics">
    <PanelSectionRow><ButtonItem layout="below" onClick={generateReport} disabled={isGeneratingReport}><FaBug /> {isGeneratingReport ? "Generating..." : "Generate Report"}</ButtonItem></PanelSectionRow>
    {diagnosticLogs.length > 0 && <PanelSectionRow><ButtonItem layout="below" onClick={clearAllLogs}><FaTrash /> Clear All Reports</ButtonItem></PanelSectionRow>}
    </PanelSection>
    {diagnosticLogs.length > 0 && (
      <PanelSection title="Recent Reports">
      {diagnosticLogs.map((log) => <PanelSectionRow key={log.filename}><Field label={log.timestamp}><div style={{ fontSize: '12px', color: '#8b8d8f' }}>{formatFileSize(log.size)}</div></Field></PanelSectionRow>)}
      </PanelSection>
    )}
    </Focusable>
  );
};

export default definePlugin((serverAPI: ServerAPI) => ({
  title: <div style={{display: 'flex', alignItems: 'center'}}><FaWifi style={{marginRight: '5px'}}/> WiFiDiagnostic</div>,
  content: <Content serverAPI={serverAPI} />,
  icon: <FaWifi />,
}));
