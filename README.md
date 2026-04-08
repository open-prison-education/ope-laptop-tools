# OPE Laptop Tools

A collection of Windows applications and utilities designed to prepare and manage laptops for incarcerated students. These tools automate the credentialing process, enforce security policies, manage user accounts, and maintain system compliance.

## Overview

This repository contains several applications that work together to:
- Automate laptop setup and credentialing for student use
- Enforce security policies and firewall rules
- Manage Windows user accounts and permissions
- Monitor system activity and capture screenshots
- Sync data with the Student Management Console (SMC)
- Generate Canvas tokens for LMS integration

## Applications

### 1. Credential (`credential.exe`)

The main credentialing application that automates the full student laptop setup workflow.

**Key Features:**
- Validates operator input and configuration
- Sets firewall rules and security policies
- Creates student Windows user accounts
- Generates Canvas tokens for OPE-LMS integration
- Installs required services and dependencies
- Applies security hardening steps
- Stores configuration in Windows Registry for downstream services

**What it does:**
1. Verifies BIOS lockdown status
2. Confirms administrative privileges
3. Caches configuration data in registry
4. Validates student account (optionally fetches Canvas tokens from SMC when configured)
5. Syncs network interface and time settings
6. Orchestrates `mgmt.exe` commands to:
   - Unlock the machine
   - Credential the laptop
   - Add Windows Defender exclusions
   - Install services
   - Relock the device

**Usage:**
- Configure `credential_config.json` before running
- Run as Administrator (right-click → "Run as administrator")
- See [credential/README.md](credential/README.md) for detailed configuration options

**Logs:** `%PROGRAMDATA%\ope\logs\ope-credential.log`

---

### 2. Management Tool (`mgmt.exe`)

A comprehensive command-line management utility that handles system configuration, security enforcement, and maintenance tasks.

**Key Features:**
- System configuration and setup
- Network interface management (approve/disapprove NICs)
- User account management (create, enable, disable, remove)
- Group Policy and firewall policy management
- Registry and folder permission management
- Process management and monitoring
- System time synchronization
- Credentialing workflow orchestration
- Data synchronization with SMC

**Common Commands:**
- `mgmt.exe config` - Initial configuration setup
- `mgmt.exe credential` - Run credentialing process
- `mgmt.exe sync` - Sync with SMC (passwords, logs, work folders)
- `mgmt.exe screen_shot` - Capture screenshot
- `mgmt.exe scan_nics` - Scan and disable unauthorized network interfaces
- `mgmt.exe apply_group_policy` - Apply security lockdown policies
- `mgmt.exe apply_firewall_policy` - Apply firewall rules
- `mgmt.exe help <command>` - Get help for specific commands

**Logs:** `%PROGRAMDATA%\ope\logs\ope-mgmt.log`

---

### 3. OPEService (`OPEService.exe`)

A Windows service that runs in the background to maintain system security and compliance.

**Key Features:**
- Monitors USB device connections
- Automatically scans and manages network interfaces
- Enforces security policies on a schedule
- Captures periodic screenshots
- Monitors login events
- Executes scheduled maintenance tasks
- Responds to device events (NIC plug/unplug)

**What it does:**
- Runs continuously in the background
- Executes `mgmt.exe` commands on schedule:
  - Network interface scanning
  - Screenshot capture
  - Permission resets
  - Registry maintenance
- Responds to USB device events
- Monitors for unauthorized network adapters

**Installation:**
- Installed automatically by `credential.exe`
- Can be installed manually using `bin\install_service.cmd`
- Service name: `OPEService`

**Logs:** `%PROGRAMDATA%\ope\logs\ope-service.log`

---

### 4. Screenshot Tool (`sshot.exe`)

A utility for capturing screenshots of the student's desktop for monitoring purposes.

**Key Features:**
- Captures full desktop screenshots (supports multi-monitor)
- Adds timestamp and user information overlay
- Saves screenshots to `%PROGRAMDATA%\ope\screenshots\`
- Can be run manually or scheduled via OPEService

**Usage:**
- Run directly: `sshot.exe`
- Called automatically by `mgmt.exe screen_shot`
- Scheduled by OPEService at configurable intervals

**Logs:** `%PROGRAMDATA%\ope\logs\ope-sshot.log`

---

## Quick Start

### Prerequisites

- Windows 10/11
- Python 3.12 (3.13 not supported yet by Nuitka)
- Administrative privileges
- Network access to SMC server

### Initial Setup

1. **Clone the repository:**
   ```powershell
   git clone https://github.com/open-prison-education/ope-laptop-tools
   cd ope-laptop-tools
   ```

2. **Create virtual environment and install dependencies:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r modules.txt
   ```

3. **Configure credential application:**
   - Edit `credential/credential_config.json`
   - Set required settings (optionally set `smc_url` and `smc_admin_username` for Canvas token integration)
   - See [credential/README.md](credential/README.md) for configuration details

4. **Run credentialing process:**
   - Right-click `dist\credential\credential.exe` → "Run as administrator"
   - Or run from source: `python credential\credential.py` (as admin)

---

## Build Instructions

Use Python 3.12 for all builds (3.13 not supported yet by Nuitka).

### Setup Build Environment

Before building, create a Python virtual environment and install all required packages:

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r modules.txt
```

### Building Applications

**Build mgmt:**
```powershell
.\nuitka_mgmt_build.cmd
```

**Build screenshot:**
```powershell
.\nuitka_sshot_build.cmd
```

**Build OPEService:**
```powershell
python .\build_svc.py
```

**Build credential:**
```powershell
cd credential
.\build_credential.cmd
```

**Output:** All built applications are located in the `dist` directory.

---

## PyInstaller - Custom Build

Due to antivirus false positives, a custom PyInstaller build is required. See the [original article](https://python.plainenglish.io/pyinstaller-exe-false-positive-trojan-virus-resolved-b33842bd3184) for details.

### Custom Build Process

1. **Clone PyInstaller:**
   ```powershell
   git clone https://github.com/pyinstaller/pyinstaller
   ```
   Clone to `c:\pyinstaller`

2. **Modify bootloader:**
   - Add variables to functions in `bootloader/src/pyi_main.c`
   - Adding something like `int ope_custom=1;` in each function changes binary signatures
   - This prevents antivirus false positives

3. **Build bootloader:**
   ```powershell
   cd c:\pyinstaller\bootloader
   pip uninstall pyinstaller
   # Install dependencies via Chocolatey (see PyInstaller docs)
   # Switch to Python 3.11 if needed
   setx VSCMD_SKIP_SENDTELEMETRY 1
   python .\waf distclean all --target-arch=64bit
   ```

4. **Install custom PyInstaller:**
   ```powershell
   cd c:\pyinstaller
   pip install .
   ```

---

## Directory Structure

```
ope-laptop-tools/
├── common/                 # Shared modules and utilities
├── credential/             # Credential application
│   ├── credential.py       # Main credential script
│   └── credential_config.json
├── mgmt/                   # Management tool modules
│   ├── mgmt.py             # Main mgmt entry point
│   ├── mgmt_*.py           # Individual management modules
│   └── mgmt.version        # Version information
├── opeService/             # OPEService Windows service
│   └── OPEService.py
├── screenshot/             # Screenshot utility
│   └── sshot.py
└── modules.txt             # Python dependencies
```

---

## Configuration

### Credential Configuration

The credential application uses `credential_config.json` for all settings. Key configuration options:

See [credential/README.md](credential/README.md) for complete configuration reference.

### Registry Settings

Many settings are stored in Windows Registry under `HKEY_LOCAL_MACHINE\SOFTWARE\OPE\`:
- Log levels
- Timer intervals (screenshot, NIC scan, etc.)
- SMC configuration
- Student account information
- Network type and domain information

---

## Logging

All applications log to `%PROGRAMDATA%\ope\logs\`:
- `ope-credential.log` - Credential application logs
- `ope-mgmt.log` - Management tool logs
- `ope-service.log` - OPEService logs
- `ope-sshot.log` - Screenshot tool logs

Log levels can be adjusted using:
```powershell
mgmt.exe set_log_level <level>
```
Where level is typically 1-5 (higher = more verbose).

---

## Security Features

- **Network Interface Control:** Only approved network adapters are allowed
- **Firewall Management:** Automated firewall rule application
- **Group Policy:** Security lockdown policies applied automatically
- **User Account Management:** Automated student account creation and management
- **Permission Enforcement:** Registry and folder permissions reset on schedule
- **Device Monitoring:** USB and network device event monitoring
- **Screenshot Monitoring:** Periodic desktop screenshots for compliance

---

## Troubleshooting

### Credentialing Fails
- Verify BIOS is locked down (set `have_you_locked_down_the_bios: true`)
- Ensure running as Administrator
- If SMC is configured, check SMC connectivity and credentials
- Review `ope-credential.log` for detailed error messages

### Network Issues
- List approved NICs: `mgmt.exe list_approved_nics`
- List system NICs: `mgmt.exe list_system_nics`
- Approve a NIC: `mgmt.exe approve_nic "NIC Name" "subnet"`

### View Service Output
- Run trace collector: `mgmt.exe show_trace`
- This shows real-time console output from OPEService

---

## Additional Resources

- [Credential Application README](credential/README.md) - Detailed credential configuration
- [Release Log](RELEASE_LOG.md) - Version history and changes

---

## Support

For issues, questions, or contributions, please refer to the project repository or contact the development team.
