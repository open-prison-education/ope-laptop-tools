# OPE Credential Script

## Overview

`credential.py` automates the full student laptop credentialing workflow. It
validates operator input, stores configuration values in the registry for the
management tooling, calls out to `mgmt.exe` (or `python -m mgmt.mgmt` when
debugging), and applies security hardening steps. The script logs to
`%PROGRAMDATA%\ope\logs\ope-credential.log` via the `mgmt.mgmt_EventLog` helper.

At a high level the process performs the following:

- Confirms the JSON configuration is complete and operator has locked down the BIOS.
- Verifies the session is elevated (UAC/Admin) before proceeding.
- Caches configuration data in the registry for downstream services.
- Pulls SMC configuration, confirms the target student account, and syncs NIC/time settings.
- Orchestrates `mgmt.exe` commands to unlock the machine, credential the laptop, add Defender exclusions, install services, and relock the device.

Every failure path is logged, and critical steps will stop execution with the correct exit code so the laptop is not handed to students in an unfinished state.

## Running the Script

1.  **Configure `credential_config.json`**:
    -   Open the `credential_config.json` file.
    -   Update the values for each key according to your setup. See the "Configuration" section below for details on each setting.
    -   Pay special attention to `smc_admin_username` and `student_username`.

2.  **Run as Administrator**:
    -   The script requires administrative privileges to perform tasks like installing software, modifying system settings, and accessing the registry.
    -   **For `credential.exe`**, you can right-click the file and select "Run as administrator".
    -   **For `credential.py`**, follow step 3 below.

3. **for running `credential.py` (skip this step when running `credential.exe`):**
    you will need to open your terminal (e.g., PowerShell or Command Prompt) as an administrator before running the script  
   ```powershell
   cd path\to\repo
   python credential\credential.py
   ```

4. **Review the summary.** The script prints a formatted list of the configuration values and prompts for confirmation unless `"debug": "on"`.
5. **Monitor output/logs.** Interactive status messages mirror the registry and `mgmt.exe` operations. Check `ope-credential.log` for detailed traces if needed.

If you are iterating locally, set `"debug": "on"` to:

- Skip service installation.
- Run `python -m mgmt.mgmt` commands from the repository root instead of invoking `mgmt.exe`.
- Bypass confirmation prompts (continues automatically).

## Configuration Reference (`credential_config.json`)

This file contains all the settings for the credentialing process. Below is a description of each key and its acceptable values.

---

### `install_vc_runtimes`

-   **Description**: Determines whether to install the Visual C++ runtimes.
-   **Acceptable Values**: `true`, `false` (boolean)
-   **Required**: Yes

---

### `have_you_locked_down_the_bios`

-   **Description**: A manual check to ensure the laptop's BIOS has been secured. The script will not run if this is set to `false`.
-   **Acceptable Values**: `true`, `false` (boolean)
-   **Required**: Yes (must be `true` to proceed)

---

### `smc_url`

-   **Description**: The URL for the Student Management Console (SMC).
-   **Acceptable Values**: A valid URL string.
-   **Example**: `"https://smc.corrections.sbctc.edu/"`
-   **Required**: Yes

---

### `smc_admin_username`

-   **Description**: The username for an admin account on the SMC. This is used to verify the student's account.
-   **Acceptable Values**: A valid SMC admin username string.
-   **Required**: Yes

---

### `student_username`

-   **Description**: The username of the student whose account will be set up on the laptop.
-   **Acceptable Values**: A valid student username string.
-   **Required**: No (if not set, you will be prompted to enter it at run time).

---

### `approved_nics`

- **Description**: A JSON-encoded string representing a list of approved network adapters and their allowed IP subnets.
- **Acceptable Values**: A valid JSON string that decodes to a list of lists, each containing a network card name and its associated allowed subnet in CIDR notation. Subent can be partial.
- **Example**: `[[ "nic_name #1", "subnet #1" ], [ "nic_name #2", "subnet #2" ]]`
- **Required**: Yes


### `services_path`

-   **Description**: The relative path to the directory from root project containing the OPE services, including `mgmt.exe`.
-   **Acceptable Values**: A string representing a valid path.
-   **Example**: `"Services"`
-   **Required**: Yes

---

### `vc_runtimes_script`

-   **Description**: The relative path to the directory from root project to the script used for installing for installing the Visual C++ runtimes.
-   **Acceptable Values**: A string representing a valid path to a `.cmd` or `.bat` file.
-   **Example**: `"bin/install_vc_runtimes.cmd"`
-   **Required**: Yes

---

### `install_service_script`

-   **Description**: The relative path to the directory from root project to the script used for installing the OPE services.
-   **Acceptable Values**: A string representing a valid path to a `.cmd` or `.bat` file.
-   **Example**: `"bin/install_service.cmd"`
-   **Required**: Yes

---

### `debug`

-   **Description**: Enables or disables debug mode. When `"on"`, the script will:
    -   Skip the confirmation prompt.
    -   Skip service installation.
    -   Execute `mgmt` commands using `python -m mgmt.mgmt` which is useful for development.
-   **Acceptable Values**: `"on"`, `"off"` (string)
-   **Required**: No


### Runtime Behaviour Influenced by Configuration

- `install_vc_runtimes=false` logs the choice and continues without invoking the batch installer.
- `debug="on"` sets the working directory to the project root, runs `mgmt` via Python, skips service installation, and bypasses the confirmation prompt.
- When not in debug mode the script expects `mgmt.exe` to exist under `services_path\mgmt\mgmt.exe`; missing files raise errors and halt the process.
- Registry values written by the script (`smc_url`, `student_user`, `debug`, etc.) feed the downstream `mgmt` credential flow.

### Error Handling

- Any failed “critical” command (unlocking, credentialing, installing services, locking) exits with code `2` to mark the device unusable until retried.
- Non-critical issues (VC runtimes, Defender exclusion) emit warnings but do not abort the run.
- The script always clears the `credential_config` registry flag in a `finally` block to avoid leaving stale state if interrupted.

Refer to the inline logging in `credential.py` for the exact messaging emitted during each step.

