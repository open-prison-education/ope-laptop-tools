"""
OPE Credential Process
Configures a laptop for student use by installing services, credentialing, and locking down security.
"""

import os
import sys
import json
import subprocess
import time
import ctypes

# Add parent directory to path so we can import common modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from common.color import p
from common import util
from mgmt.mgmt_EventLog import EventLog

# Setup logging
LOGGER = EventLog(os.path.join(util.LOG_FOLDER, 'ope-credential.log'), service_name="OPECredential")

# Exit codes
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_CRITICAL = 2


class CredentialConfig:
    """Manages credential configuration from JSON file"""
    
    def __init__(self, config_path=None):
        if config_path is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(script_dir, "credential_config.json")
        
        self.config_path = config_path
        self.config = {}
        
    def load(self):
        """Load configuration from JSON file"""
        p("}}gnLoading configuration from: " + self.config_path + "}}xx", log_level=3)
        
        if not os.path.exists(self.config_path):
            p("}}rbERROR: Configuration file not found: " + self.config_path + "}}xx", log_level=1)
            p("}}ybPlease create a credential_config.json file with required settings.}}xx")
            return False
        
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
            p("}}gnConfiguration loaded successfully.}}xx", log_level=3)
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
        required_keys = ['install_vc_runtimes', 'services_path', 'vc_runtimes_script', 'install_service_script']
        
        for key in required_keys:
            if key not in self.config:
                p("}}rbERROR: Missing required configuration key: " + key + "}}xx", log_level=1)
                return False
        
        return True
    
    def print_summary_and_confirm(self):
        """Print configuration summary"""
        p("\n}}gb=== Credential Configuration ===}}xx")
        p("}}ynInstall VC Runtimes: }}cn" + str(self.config.get('install_vc_runtimes', False)) + "}}xx")
        p("}}ynServices Path: }}cn" + str(self.config.get('services_path', '')) + "}}xx")
        p("}}ynVC Runtimes Script: }}cn" + str(self.config.get('vc_runtimes_script', '')) + "}}xx")
        p("}}ynInstall Service Script: }}cn" + str(self.config.get('install_service_script', '')) + "}}xx")
        p("}}gb=================================}}xx\n")

        p("}}ynDo you want to continue? (y/n): }}xx ", False)
        userInput = input()
        userInput = userInput.lower().strip()
        while userInput != "y" and userInput != "n":
            p("}}rbInvalid input " + userInput + " - please enter y or n: }}xx ", False)
            userInput = input()    
            userInput = userInput.lower().strip()
        if userInput == "y":
            return True
        else:
            return False


class CredentialProcess:
    """Main credential process orchestrator"""
    
    def __init__(self, config):
        self.config = config
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
    
    def check_admin_privileges(self):
        """Verify the script is running with admin/UAC privileges"""
        try:
            # Try to access admin-only registry key
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            if not is_admin:
                p("}}rbERROR: This script must be run as Administrator!}}xx", log_level=1)
                p("}}ybPlease right-click and select 'Run as Administrator'}}xx")
                return False
            
            p("}}gnRunning with Administrator privileges.}}xx", log_level=3)
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
        p("}}gnExecuting: " + cmd + "}}xx", log_level=4)
        
        try:
            result = subprocess.run(cmd, shell=True, capture_output=False)
            
            if result.returncode != 0:
                if error_msg:
                    p("}}rb" + error_msg + "}}xx", log_level=1)
                
                p("}}rbCommand failed with exit code: " + str(result.returncode) + "}}xx", log_level=1)
                
                if critical:
                    p("\n}}rbCritical error - exiting credential process.}}xx", log_level=1)
                    os._exit(EXIT_CRITICAL)
                
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
            p("}}ynSkipping VC Runtimes installation (disabled in config).}}xx", log_level=3)
            return True
        
        p("}}gb-- Installing VC Runtimes...}}xx")
        
        vc_script = self.config.get('vc_runtimes_script', '')
        vc_script_path = os.path.join(self.script_dir, vc_script)
        
        if not os.path.exists(vc_script_path):
            p("}}rbWARNING: VC Runtimes script not found: " + vc_script_path + "}}xx", log_level=2)
            p("}}ynContinuing without VC Runtimes installation...}}xx")
            return True
        
        return self.run_command(
            f'call "{vc_script_path}"',
            error_msg="WARNING: VC Runtimes installation failed, but continuing...",
            critical=False
        )
    
    def run_config_once(self):
        """Run mgmt.exe config_once to setup initial configuration"""
        p("}}gb-- Running initial configuration...}}xx")
        
        services_path = self.config.get('services_path', 'Services')
        mgmt_exe = os.path.join(self.script_dir, services_path, "mgmt", "mgmt.exe")
        
        if not os.path.exists(mgmt_exe):
            p("}}rbERROR: mgmt.exe not found at: " + mgmt_exe + "}}xx", log_level=1)
            return False
        
        return self.run_command(
            f'"{mgmt_exe}" config_once',
            error_msg="ERROR: Failed to run config_once",
            critical=False
        )
    
    def add_defender_exclusion(self):
        """Add Windows Defender exclusion for OPE folder"""
        p("}}gb-- Adding Windows Defender exclusion...}}xx")
        
        cmd = 'PowerShell -NoProfile -ExecutionPolicy Bypass -Command "& {Add-MpPreference -ExclusionPath \'%PROGRAMDATA%\\ope\'}"'
        
        return self.run_command(
            cmd,
            error_msg="WARNING: Failed to add Defender exclusion",
            critical=False
        )
    
    def unlock_machine(self):
        """Unlock machine to disable security settings for credential process"""
        p("}}gb-- Unlocking Machine - please wait...}}xx")
        p("")
        
        services_path = self.config.get('services_path', 'Services')
        mgmt_exe = os.path.join(self.script_dir, services_path, "mgmt", "mgmt.exe")
        
        return self.run_command(
            f'"{mgmt_exe}" unlock_machine',
            error_msg="*** ERROR - Failed to unlock machine - Quitting. ***",
            critical=True
        )
    
    def install_services(self):
        """Install OPE Services"""
        p("}}gb-- Installing OPE Services...}}xx")
        
        install_script = self.config.get('install_service_script', '')
        install_script_path = os.path.join(self.script_dir, install_script)
        
        if not os.path.exists(install_script_path):
            p("}}rbERROR: Install service script not found: " + install_script_path + "}}xx", log_level=1)
            return False
        
        return self.run_command(
            f'call "{install_script_path}"',
            error_msg="****** ERROR - Failed to install OPE services. Credential process did not complete properly - this Laptop is NOT ready to hand out to students. *******",
            critical=True
        )
    
    def credential_laptop(self):
        """Run the main credential process"""
        p("}}gb-- Starting credential process...}}xx")
        
        # Use the installed version in programdata
        mgmt_exe = os.path.expandvars("%programdata%\\ope\\Services\\mgmt\\mgmt.exe")
        
        if not os.path.exists(mgmt_exe):
            p("}}rbERROR: mgmt.exe not found at: " + mgmt_exe + "}}xx", log_level=1)
            p("}}ybMake sure services were installed correctly.}}xx")
            return False
        
        return self.run_command(
            f'"{mgmt_exe}" credential_laptop',
            error_msg="****** Credential process did not complete properly - this Laptop is NOT ready to hand out to students. *******",
            critical=True
        )
    
    def lock_machine(self):
        """Lock machine down and enable student account"""
        p("}}gb-- Locking Machine...}}xx")
        
        # Use the installed version in programdata
        mgmt_exe = os.path.expandvars("%programdata%\\ope\\Services\\mgmt\\mgmt.exe")
        
        return self.run_command(
            f'"{mgmt_exe}" lock_machine',
            error_msg="****** ERROR - Unable to lock machine. Credential process did not complete properly - this Laptop is NOT ready to hand out to students. Try mgmt lock_machine again to see if you can lock it manually. *******",
            critical=True
        )
    
    def display_completion(self):
        """Display completion message"""
        p("")
        p("}}gb *** Credential Done *** }}xx")
        p("")
        
        # Slight pause like the batch script
        p("}}gnWaiting 10 seconds before closing...}}xx", log_level=3)
        time.sleep(10)
        
        input("Press Enter to exit...")
    
    def run(self):
        """Execute the complete credential process"""
        # Check admin privileges
        if not self.check_admin_privileges():
            return EXIT_ERROR
        
        # Print configuration summary
        if not self.config.print_summary_and_confirm():
            p("}}ynCredential process interrupted by user.}}xx")
            return EXIT_SUCCESS
        
        # Execute workflow steps
        steps = (
            ("Installing VC Runtimes", self.install_vc_runtimes),
            ("Running initial configuration", self.run_config_once),
            ("Adding Defender exclusion", self.add_defender_exclusion),
            ("Unlocking machine", self.unlock_machine),
            ("Installing services", self.install_services),
            ("Credentialing laptop", self.credential_laptop),
            ("Locking machine", self.lock_machine),
        )
        
        for step_name, step_func in steps:
            p("}}gnStep: " + step_name + "}}xx", log_level=3)
            if not step_func():
                p("}}rbStep failed: " + step_name + "}}xx", log_level=1)
                return EXIT_ERROR
        
        # Display completion
        self.display_completion()
        
        return EXIT_SUCCESS


def main():
    """Main entry point"""
    try:
        p("}}gb[ ---- Starting Credential Process ---- ]}}xx\n")
        # Load configuration
        config = CredentialConfig()
        if not config.load():
            sys.exit(EXIT_ERROR)
        
        if not config.validate():
            sys.exit(EXIT_ERROR)
        
        # Run credential process
        process = CredentialProcess(config)
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


if __name__ == "__main__":
    main()

