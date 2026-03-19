"""
OPE Credential Process
Configures a laptop for student use by installing services, credentialing, and locking down security.
"""

import os
import sys
import json
import subprocess
import ctypes

# Add parent directory to path so we can import common and mgmt modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from common.color import p
from common import util
from mgmt.mgmt_EventLog import EventLog
from mgmt.mgmt_RegistrySettings import RegistrySettings
from mgmt.mgmt_SystemTime import SystemTime
from mgmt.mgmt_NetworkDevices import NetworkDevices

# Setup logging
lf = os.path.join(util.LOG_FOLDER, 'ope-credential.log')
os.makedirs(os.path.dirname(lf), exist_ok=True)
LOGGER = EventLog(lf, service_name="OPECredential")

# Exit codes
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_CRITICAL = 2


class CredentialConfig:
    """Manages credential configuration from JSON file"""
    
    def __init__(self, config_path=None):
        if config_path is None:
            if getattr(sys, 'frozen', False):
                # Running as a bundled executable
                script_dir = os.path.dirname(sys.executable)
            else:
                # Running as a normal Python script
                script_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(script_dir, "credential_config.json")
        
        self.config_path = config_path
        self.config = {}
        
    def load(self):
        """Load configuration from JSON file"""
        p("}}gnLoading configuration from: " + self.config_path + "}}xx")
        
        if not os.path.exists(self.config_path):
            p("}}rbERROR: Configuration file not found: " + self.config_path + "}}xx", log_level=1)
            p("}}ybPlease create a credential_config.json file with required settings.}}xx")
            return False
        
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
            p("}}gnConfiguration loaded successfully.}}xx")
            return True
        except json.JSONDecodeError as ex:
            p("}}rbERROR: Invalid JSON in configuration file: " + str(ex) + "}}xx", log_level=1)
            return False
        except Exception as ex:
            p("}}rbERROR: Failed to load configuration: " + str(ex) + "}}xx", log_level=1)
            return False
    
    def get(self, key, default=None):
        """Get a configuration value"""
        return self.config.get(key, default)
    
    def validate(self):
        """Validate required configuration settings"""
        required_keys = ['install_vc_runtimes', 'have_you_locked_down_the_bios', 'services_path', 'vc_runtimes_script', 'install_service_script']
        
        for key in required_keys:
            if key not in self.config:
                p("}}rbERROR: Missing required configuration key: " + key + "}}xx", log_level=1)
                p("}}rbThe following keys are required:")
                for key in required_keys:
                    p("}}yn" + key.replace('_', ' ').title() + "}}xx", log_level=1)
                p("}}rbPlease edit the credential_config.json file and try again.}}xx", log_level=1)
                return False
        
        return True
    
    def get_config(self):
        """Get the configuration dictionary"""
        return self.config





class CredentialProcess:
    """Main credential process orchestrator"""
    
    def __init__(self, config_dict):
        self.config = config_dict
        if getattr(sys, 'frozen', False):
            # Running as a bundled executable
            self.script_dir = os.path.dirname(sys.executable)
        else:
            # Running as a normal Python script
            self.script_dir = os.path.dirname(__file__)
    
    def print_summary_and_confirm(self):
        """Print configuration summary and get user confirmation"""
        p("}}gb=== Credential Configuration ===}}xx")
        
        # Dynamically print all config keys and values
        for key, value in self.config.items():
            p("}}yn" + key.replace('_', ' ').title() + ": }}cn" + str(value) + "}}xx")
        
        p("}}gb=================================}}xx\n")

        if self.config.get('debug', 'off').lower() == "on":
            return True

        p("}}ynDo you want to continue? (y/n): }}xx ", False)
        userInput = input()
        userInput = userInput.strip().lower()
        while userInput != "y" and userInput != "n":
            p("}}rbInvalid input " + userInput + " - please enter y or n: }}xx ", end=False, log_level=1)
            userInput = input()    
            userInput = userInput.strip().lower()
        if userInput == "y":
            return True
        else:
            return False
    
    def check_admin_privileges(self):
        """Verify the script is running with admin/UAC privileges"""
        try:
            # Try to access admin-only registry key
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            if not is_admin:
                p("}}rbERROR: This script must be run as Administrator!}}xx", log_level=1)
                p("}}ybPlease right-click and select 'Run as Administrator'}}xx")
                return False
            
            p("}}gnRunning with Administrator privileges.}}xx")
            return True
        except Exception as ex:
            p("}}rbERROR: Failed to check admin privileges: " + str(ex) + "}}xx", log_level=1)
            return False
    
    def run_command(self, cmd, error_msg=None, critical=False):
        """
        Run a command and check return code
        
        Args:
            cmd: Command to run
            error_msg: Error message to display on failure
            critical: If True, exit with EXIT_CRITICAL on failure
            
        Returns:
            True on success, False on failure
        """
        p("}}gnExecuting: " + cmd + "}}xx")
        
        # Set up environment and working directory for testing mode
        cwd = None
        if self.config.get('debug', 'off').lower() == "on":
            cwd = self.get_base_path()
            p("}}gnWorking directory is set to: " + cwd + "}}xx", log_level=4)

        try:
            result = subprocess.run(cmd, shell=True, capture_output=False, cwd=cwd)    
            if result.returncode != 0:
                if error_msg:
                    p("}}rb" + error_msg + "}}xx", log_level=1)
                
                p("}}rbCommand failed with exit code: " + str(result.returncode) + "}}xx", log_level=1)
                
                if critical:
                    p("\n}}rbCritical error - exiting credential process.}}xx", log_level=1)
                    sys.exit(EXIT_CRITICAL)
                
                return False
            
            return True
        except Exception as ex:
            p("}}rbERROR: Failed to execute command: " + str(ex) + "}}xx", log_level=1)
            if critical:
                p("\n}}rbCritical error - exiting credential process.}}xx", log_level=1)
                sys.exit(EXIT_CRITICAL)
            return False
    
    def install_vc_runtimes(self):
        """Optionally install VC runtime packages"""
        if not self.config.get('install_vc_runtimes', False):
            p("}}ynSkipping VC Runtimes installation (disabled in config).}}xx")
            return True
        
        p("}}gb-- Installing VC Runtimes...}}xx")

        vc_script_path = self.get_full_path(self.config.get('vc_runtimes_script', ''))
        
        if not os.path.exists(vc_script_path):
            p("}}rbError: VC Runtimes script not found: " + vc_script_path + "}}xx", log_level=1)
            return False
        
        return self.run_command(
            f'call "{vc_script_path}"',
            error_msg="Error: VC Runtimes installation failed",
            critical=False
        )
    
    def add_defender_exclusion(self):
        """Add Windows Defender exclusion for OPE folder"""
        p("}}gb-- Adding Windows Defender exclusion...}}xx")
        
        cmd = 'PowerShell -NoProfile -ExecutionPolicy Bypass -Command "& {Add-MpPreference -ExclusionPath \'%PROGRAMDATA%\\ope\'}"'
        
        return self.run_command(
            cmd,
            error_msg="Error: Failed to add Defender exclusion",
            critical=True
        )
    
    def unlock_machine(self):
        """Unlock machine to disable security settings for credential process"""
        p("}}gb-- Unlocking Machine - please wait...}}xx")
        p("")
        
        mgmt_exe = self.get_mgmt_exe_path()
        if not mgmt_exe:
            return False
        
        return self.run_command(
            f'{mgmt_exe} unlock_machine',
            error_msg="*** ERROR - Failed to unlock machine - Quitting. ***",
            critical=True
        )
    
    def install_services(self):
        """Install OPE Services"""
        p("}}gb-- Installing OPE Services...}}xx")

        if self.config.get('debug', 'off').lower() == "on":
            p("}}gnSkipping service installation in testing mode.}}xx")
            return True
        
        install_script_path = self.get_full_path(self.config.get('install_service_script', ''))
        
        if not os.path.exists(install_script_path):
            p("}}rbERROR: Install service script not found: " + install_script_path + "}}xx", log_level=1)
            return False
        
        return self.run_command(
            f'call {install_script_path}',
            error_msg="****** ERROR - Failed to install OPE services. Credential process did not complete properly - this Laptop is NOT ready to hand out to students. *******",
            critical=True
        )
    
    def credential_laptop(self):
        """Run the main credential process"""
        p("}}gb-- Starting credential process...}}xx")
        
        mgmt_exe = self.get_mgmt_exe_path()
        if not mgmt_exe:
            return False
        
        return self.run_command(
            f'{mgmt_exe} credential_laptop',
            error_msg="****** Credential process did not complete properly - this Laptop is NOT ready to hand out to students. *******",
            critical=True
        )
    
    def lock_machine(self):
        """Lock machine down and enable student account"""
        p("}}gb-- Locking Machine...}}xx")
        
        mgmt_exe = self.get_mgmt_exe_path()
        if not mgmt_exe:
            return False
        
        return self.run_command(
            f'{mgmt_exe} lock_machine',
            error_msg="****** ERROR - Unable to lock machine. Credential process did not complete properly - this Laptop is NOT ready to hand out to students. Try mgmt lock_machine again to see if you can lock it manually. *******",
            critical=True
        )
    
    def display_completion(self):
        """Display completion message"""
        p("")
        p("}}gb *** Credential Done *** }}xx")
        p("")

    def get_mgmt_exe_path(self):
        """Get the path to the mgmt.exe file"""
        if self.config.get('debug', 'off').lower() == "on":
            return "python -m mgmt.mgmt"
        else:
            # When frozen (bundled as an executable), script_dir is the exe's directory. The Services directory is one level above.
            services_path = self.get_full_path(self.config.get('services_path', 'Services'))
            mgmt_exe_path = os.path.join(services_path, "mgmt", "mgmt.exe")
            if not os.path.exists(mgmt_exe_path):
                p("}}rbERROR: mgmt.exe not found at: " + mgmt_exe_path + "}}xx", log_level=1)
                p("}}ybMake sure services were installed correctly.}}xx")
                return None
            return mgmt_exe_path

    def store_config_in_registry(self):
        """Store the configuration in the registry to be used by the credential_laptop function in mgmt module"""
        p("}}gb-- Storing configuration in the registry...}}xx")

        student_user = self.config.get('student_username', '')
        debug = self.config.get('debug', 'off')
        base_dn = self.config.get('base_dn', '')

        RegistrySettings.set_reg_value(value_name="student_user", value=student_user, value_type="REG_SZ")
        RegistrySettings.set_reg_value(value_name="debug", value=debug, value_type="REG_SZ")
        RegistrySettings.set_reg_value(value_name="base_dn", value=base_dn, value_type="REG_SZ")

        p("}}gb-- Configuration stored in the registry...}}xx")

        return True

    def configure_network_devices(self):
        """Configure the network devices"""
        p("}}gb-- Configuring network devices...}}xx")

        approved_nics_config = self.config.get("approved_nics", "")

        # If approved_nics_config is not None, it is a valid JSON string that decodes to a list of lists each with [nic_name, subnet].
        if approved_nics_config != "" and approved_nics_config != "[]":
            p("}}gnStoring approved NICs provided in config: " + approved_nics_config + "}}xx")
            RegistrySettings.set_reg_value(app="OPEService", value_name="approved_nics", value=approved_nics_config, value_type="REG_SZ")
            return True

        approved_nics_str = RegistrySettings.get_reg_value(app="OPEService", value_name="approved_nics", default=None)

        approved_nics = json.loads(approved_nics_str)
        
        if not self.is_valid_approved_nics(approved_nics):
            p("}}gnNo approved NICs found or invalid format, configuring NICs...}}xx")
            RegistrySettings.remove_reg_value(app="OPEService", value_name="approved_nics")
            NetworkDevices.configure_nics()
        else:
            p("}}gnApproved NICs: " + approved_nics_str + "}}xx")
        
        return True

    def sync_time_with_ntp(self):
        """Sync time with NTP servers"""
        p("}}gb-- Syncing time with NTP servers...}}xx")
        
        SystemTime.sync_time_w_ntp()
        
        return True

    def validate_and_store_student_account(self):
        """Validate student account exists in SMC and get account details"""
        p("}}gb-- Validating and storing student account...}}xx")
        student_username = self.config.get('student_username', '')

        if not student_username:
            p("}}cnStudent username not set, please enter it now:}}xx")
            student_username = input()
            if not student_username:
                p("}}rbERROR: Student username is not set.}}xx", log_level=1)
                return False
            self.config['student_username'] = student_username
            # update the registry with the new student username
            RegistrySettings.set_reg_value(value_name="student_user", value=student_username, value_type="REG_SZ")

        base_dn = self.config.get('base_dn', '')
        result, error = util.verify_student_account_in_ad(student_username, base_dn)
        if not result:
            p("}}rbERROR: Unable to verify student account in Active Directory: " + error + "}}xx", log_level=1)
            return False

        # TODO - what to do if it's not a domain member? do we stop credentialing? or add a flag to continue? ask about standalone mode?
        # do we need to distinguish between domain member and standalone mode anymore?

        laptop_network_type = "Domain Member"
        RegistrySettings.set_reg_value(value_name="laptop_network_type", value=laptop_network_type, value_type="REG_SZ")


        p("}}gnStudent account validated and stored successfully}}xx")
        return True

    def store_laptop_network_type(self):
        """Store the laptop network type in the registry"""
        p("}}gb-- Storing laptop network type in the registry...}}xx")
        laptop_network_type = self.config.get('laptop_network_type', '')
        RegistrySettings.set_reg_value(value_name="laptop_network_type", value=laptop_network_type, value_type="REG_SZ")
        return True

    def validate_config_settings(self):
        """Validate the configuration settings"""
        p("}}gb-- Validating configuration settings...}}xx")

        install_vc_runtimes = self.config.get('install_vc_runtimes', False)
        have_you_locked_down_the_bios = self.config.get('have_you_locked_down_the_bios', False)

        if not isinstance(install_vc_runtimes, bool) or not isinstance(have_you_locked_down_the_bios, bool):
            p("}}rbERROR: install_vc_runtimes and have_you_locked_down_the_bios must be a boolean value (true or false).}}xx", log_level=1)
            return False

        if not have_you_locked_down_the_bios:
            p("}}rbERROR: Have you locked down the BIOS? if yes, set have_you_locked_down_the_bios to true in the credential_config.json file and try again.    }}xx", log_level=1)
            return False

        string_keys = [
            'base_dn', 'services_path', 'vc_runtimes_script', 'install_service_script'
        ]
        for key in string_keys:
            value = self.config.get(key)
            if not isinstance(value, str):
                p("}}rbERROR: " + key + " must be a string value (check credential_config.json).}}xx", log_level=1)
                return False

        # student_username is optional, but if it exists, it must be a string. None is also acceptable.
        student_username = self.config.get('student_username')
        if student_username is not None and not isinstance(student_username, str):
            p("}}rbERROR: student_username must be a string value (check credential_config.json).}}xx", log_level=1)
            return False

        approved_nics_str = self.config.get('approved_nics', '')
        if approved_nics_str != "" and approved_nics_str != "[]":
            try:
                approved_nics = json.loads(approved_nics_str)
                if not self.is_valid_approved_nics(approved_nics):
                    p("}}rbERROR: 'approved_nics' must be a JSON-encoded list of [[\"nic_name #1\", \"subnet #1\"], [\"nic_name #2\", \"subnet #2\"]]. Check credential_config.json.}}xx", log_level=1)
                    return False
            except Exception as ex:
                p("}}rbERROR: 'approved_nics' must be a valid JSON string like [[\"nic_name #1\", \"subnet #1\"], [\"nic_name #2\", \"subnet #2\"]]. Exception: " + str(ex) + "}}xx", log_level=1)
                return False

        p("}}gnConfiguration settings validated successfully}}xx")
        return True

    def is_valid_approved_nics(self, approved_nics):
        """Validate the approved NICs - approved_nics is optional, but if it exists, it must be a valid JSON string that decodes to a list of lists each with [nic_name, subnet]."""
        if (
            not isinstance(approved_nics, list) or
            len(approved_nics) == 0 or
            not all(isinstance(item, list) and len(item) == 2 and
            all(isinstance(x, str) for x in item)
            for item in approved_nics)
            ):
                return False
        return True

    def run(self):
        """Execute the complete credential process"""
        # Check admin privileges
        if not self.check_admin_privileges() or not self.validate_config_settings() or not self.print_summary_and_confirm():
            return EXIT_ERROR

        self.store_config_in_registry()
        
        initial_checks = (self.validate_and_store_student_account, self.configure_network_devices, self.sync_time_with_ntp)
        for check in initial_checks:
            if not check():
                p("}}rbInitial check failed: " + check.__name__ + "}}xx", log_level=1)
                return EXIT_ERROR
        
        # Execute workflow steps
        steps = (
            ("Unlocking machine", self.unlock_machine),
            ("Credentialing laptop", self.credential_laptop),
            ("Installing VC Runtimes", self.install_vc_runtimes),
            ("Adding Defender exclusion", self.add_defender_exclusion),
            ("Installing services", self.install_services),
            ("Locking machine", self.lock_machine),
        )
        
        for step_name, step_func in steps:
            p("}}gnStep: " + step_name + "}}xx")
            if not step_func():
                p("}}rbStep failed: " + step_name + "}}xx", log_level=1)
                return EXIT_ERROR
        
        # Display completion
        self.display_completion()
        
        return EXIT_SUCCESS

    def get_base_path(self):
        """Get the base path of the project root directory
        which is a level above the script directory"""
        return os.path.normpath(os.path.join(self.script_dir, ".."))

    def get_full_path(self, path_str):
        """Get full and split path string based on forward slash or backslash and join to use correct OS separator"""
        if "/" in path_str or "\\" in path_str:
            parts = path_str.replace("\\", "/").split("/")
            return os.path.join(self.get_base_path(), *parts)
        else:
            return os.path.join(self.get_base_path(), path_str)


def pause_before_exit():
    """Pause before exiting if running as a frozen executable (packaged as exe)"""
    if getattr(sys, 'frozen', False):
        # Running as a bundled executable
        p("\n}}ynPress Enter to exit...}}xx", False)
        try:
            input()
        except (EOFError, KeyboardInterrupt):
            pass

def main():
    """Main entry point"""
    try:
        RegistrySettings.set_reg_value(value_name="credential_config", value=True, value_type="REG_DWORD")

        config_loader = CredentialConfig()
        if not config_loader.load() or not config_loader.validate():
            sys.exit(EXIT_ERROR)

        config_dict = config_loader.get_config()

        process = CredentialProcess(config_dict)
        exit_code = process.run()
        
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        p("\n}}ynCredential process interrupted by user.}}xx")
        sys.exit(EXIT_ERROR)
    except Exception as ex:
        p("}}rbFATAL ERROR: " + str(ex) + "}}xx", log_level=1)
        import traceback
        traceback.print_exc()
        sys.exit(EXIT_ERROR)
    finally:
        # unset the credential_config registry value
        RegistrySettings.set_reg_value(value_name="credential_config", value=False, value_type="REG_DWORD")
        # Pause before exiting if running as a frozen executable (packaged as exe)
        pause_before_exit()


if __name__ == "__main__":
    main()

