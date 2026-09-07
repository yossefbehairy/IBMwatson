# Enterprise IT Support Knowledge Base - Runbooks

This knowledge base contains verified, safe, step-by-step resolution procedures for tier-1 employee IT issues.

---

## Article KB001001: GlobalProtect VPN DNS Error
- **Category**: Network & Connectivity
- **Affected Platforms**: Windows 10/11, macOS Sonoma/Ventura
- **Risk Level**: Safe (Self-service, no elevated privileges required)
- **Symptoms**:
  - GlobalProtect VPN client shows "Connected", but employee cannot open or resolve internal intranet tools, internal wiki, or private staging environments.
  - Browser reports DNS_PROBE_FINISHED_NXDOMAIN or timeout when loading internal hostnames.
- **Root Cause**:
  - Local operating system DNS resolver cache retains stale public DNS answers instead of routing through the enterprise split-tunnel DNS servers.
- **Resolution Procedure**:
  1. Open Terminal (macOS) or PowerShell / Command Prompt (Windows).
  2. Flush the local DNS resolver cache:
     - On Windows: Execute `ipconfig /flushdns`
     - On macOS: Execute `sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder`
  3. In the GlobalProtect client interface, click the hamburger menu and select Disconnect.
  4. Wait 5 seconds, then click Connect to re-negotiate the VPN gateway and routing tables.
  5. Open a browser and verify access to internal portals.

---

## Article KB001002: Outlook / Exchange Modern Authentication Loop
- **Category**: Identity, Email & Collaboration
- **Affected Platforms**: Windows 10/11, Microsoft Office 365
- **Risk Level**: Safe
- **Symptoms**:
  - Microsoft Outlook continuously prompts for login credentials or flashes a blank login dialog window every few minutes.
  - "Need Password" status appears in the bottom status bar despite entering valid credentials.
- **Root Cause**:
  - Corrupted OAuth/ADAL tokens stored in Windows Credential Manager or conflicting cached identity tokens.
- **Resolution Procedure**:
  1. Close Outlook, Teams, and all Microsoft 365 applications.
  2. Press Win + R, type `control keymgr.dll`, and press Enter to open Windows Credential Manager.
  3. Under Windows Credentials, scroll to Generic Credentials.
  4. Locate any entries starting with `MicrosoftOffice16_Data` or `msteams_adaldso`.
  5. Click the drop-down arrow next to each entry and select Remove.
  6. Launch Outlook again. A fresh modern authentication window will appear.
  7. Enter your corporate email and complete the MFA (Duo / Okta Verify) prompt.

---

## Article KB001003: Slack Desktop Cache Corruption
- **Category**: Collaboration & Messaging
- **Affected Platforms**: Windows, macOS, Linux
- **Risk Level**: Safe
- **Symptoms**:
  - Slack desktop client displays a blank white or grey screen.
  - New messages fail to synchronize, or channels show continuous loading spinners.
- **Root Cause**:
  - Corrupted IndexedDB or cache storage in the local Electron app profile.
- **Resolution Procedure**:
  1. In the Slack top menu bar, click Help -> Troubleshooting -> Clear Cache and Restart.
  2. If Slack is completely frozen or unresponsive:
     - On Windows: Open Task Manager, terminate all Slack processes, then navigate to `%APPDATA%\Slack` and delete the Cache and Service Worker folders.
     - On macOS: Quit Slack (Cmd + Q), open Terminal and run `rm -rf ~/Library/Application\ Support/Slack/Cache`.
  3. Relaunch Slack and allow 30 seconds for initial workspace re-synchronization.

---

## Article KB001004: Zoom Camera Not Detected
- **Category**: Video Conferencing
- **Affected Platforms**: macOS, Windows 11
- **Risk Level**: Safe
- **Symptoms**:
  - Zoom reports "Cannot detect camera" or video feed remains black during meetings.
- **Resolution Procedure**:
  1. Check Operating System Privacy Settings:
     - On Windows: Settings -> Privacy & Security -> Camera -> Ensure "Let apps access your camera" and "Zoom Meetings" are ON.
     - On macOS: System Settings -> Privacy & Security -> Camera -> Ensure Zoom is checked.
  2. Close competing apps (Teams, Google Meet browser tabs).
  3. In Zoom settings -> Video, verify the correct camera is selected.
  4. Restart Zoom.

---

## Article KB001005: Chrome Managed Browser Policy Sync
- **Category**: Browser & Web Apps
- **Resolution Procedure**:
  1. In Chrome address bar, navigate to `chrome://policy`.
  2. Click the "Reload Policies" button.
  3. Verify policy timestamp updates to current time.

---

## Article KB001006: Local Printer Spooler Reset
- **Category**: Hardware & Peripherals
- **Resolution Procedure**:
  1. Press Win + R, type `services.msc`.
  2. Find "Print Spooler", right-click and select Restart.
  3. Clear any stuck documents in queue.
