import getpass
import json
import os
import sys
import time
import subprocess
import datetime

from mgmt_FolderPermissions import FolderPermissions
from mgmt_RegistrySettings import RegistrySettings
from mgmt_UserAccounts import UserAccounts
from mgmt_RestClient import RestClient
from mgmt_Computer import Computer
from mgmt_GroupPolicy import GroupPolicy
from mgmt_ProcessManagement import ProcessManagement
from mgmt_SystemTime import SystemTime
from mgmt_NetworkDevices import NetworkDevices


from common.color import p
from common.p_state import p_state
from common import util


class CredentialProcess:
    COMPUTER_INFO = {}

    @staticmethod
    def get_mgmt_version(version_file=None):
        ret = "NO VERSION"

        # Try to load the version file
        if version_file is None:
            app_folder = os.path.dirname(os.path.abspath(__file__))
            version_file = os.path.join(app_folder, "mgmt.version")

        if os.path.exists(version_file):
            try:
                f = open(version_file, "r")
                ver = json.load(f)
                f.close()
                ret = ver["version"]
            except Exception as ex:
                p("}}rbError reading mgmt.version!}}xx\n" + str(ex))

        else:
            p(f"}}rnNo mgmt.version file exists at {version_file}!")

        return ret

    @staticmethod
    def is_credentialed_domain_joined():
        """Return True if the credentialed laptop is domain-joined, False otherwise."""
        val = RegistrySettings.get_reg_value(value_name="is_domain_joined", default=0)
        return bool(val)
    
    @staticmethod
    def get_credentialed_student():
        # Return the name of the current credentialed student or None if missing
        return RegistrySettings.get_reg_value(value_name="student_user", default=None)
    
    @staticmethod
    def get_credentialed_admin():
        # Return the name of the current credentialed student or None if missing
        return RegistrySettings.get_reg_value(app="OPEService", value_name="admin_user", default=None)

    @staticmethod
    def config_mgmt_utility_once():
        # Setup local groups for students and admins
        UserAccounts.create_local_students_group()
        UserAccounts.create_local_admins_group()

        # Create registry entries and set permissions
        RegistrySettings.set_default_ope_registry_permissions(force=True)

        # Create programdata\ope folders and set permissions
        FolderPermissions.set_default_ope_folder_permissions(force=True)

        return True
        
    @staticmethod
    def config_mgmt_utility():
        mgmt_version = CredentialProcess.get_mgmt_version()

        UserAccounts.create_local_students_group()
        UserAccounts.create_local_admins_group()

        # Create registry entries and set permissions
        RegistrySettings.set_default_ope_registry_permissions(force=True)

        # Create programdata\ope folders and set permissions
        FolderPermissions.set_default_ope_folder_permissions(force=True)

        # Make sure RDP RPC is allowed
        RegistrySettings.set_reg_value(
            root="HKLM",
            app="System\\CurrentControlSet\\Control\\Terminal Server",
            value_name="AllowRemoteRPC", value="1",
            value_type="REG_DWORD")

        p("\n}}gbOPE Management Utility - Version: " + mgmt_version + "}}xx")

        p("}}gnSyncing time with NTP servers...}}xx")
        SystemTime.sync_time_w_ntp(force=True)

        p("}}gnConfiguring Network Devices...}}xx")
        NetworkDevices.configure_nics()

        # Check if current user is in the OPEadmins group
        active_user = UserAccounts.get_active_user_name()
        if active_user is not None and active_user.lower() != "system" and not UserAccounts.is_user_in_group(active_user, "OPEAdmins"):
            p("}}gnAdding current user (" + active_user + ") to OPEAdmins group...}}xx")
            UserAccounts.add_user_to_group(active_user, "OPEAdmins")

        return True

    @staticmethod
    def _get_student_info_from_registry():
        """Read student info from registry (called from credential.py pipeline)."""
        student_user = RegistrySettings.get_reg_value(value_name="student_user", default="")
        student_name = RegistrySettings.get_reg_value(value_name="student_name", default="")
        is_domain_joined = bool(RegistrySettings.get_reg_value(value_name="is_domain_joined", default=0))

        if not student_user:
            p("}}rbNo student_user found in registry!}}xx")
            return None

        student_password = None
        if not is_domain_joined:
            import secrets
            student_password = secrets.token_urlsafe(6)
            p("}}ynGenerated password for " + student_user + ": }}cb" + student_password + "}}xx")
            util.store_password(student_user, student_password)

        return (student_user, student_name, student_password, is_domain_joined)

    @staticmethod
    def _get_student_info_interactive():
        """Prompt for student info interactively (standalone mgmt invocation)."""
        mgmt_version = CredentialProcess.get_mgmt_version()
        student_user = RegistrySettings.get_reg_value(value_name="student_user", default="")
        is_domain_joined = bool(RegistrySettings.get_reg_value(value_name="is_domain_joined", default=0))
        base_dn = RegistrySettings.get_reg_value(value_name="base_dn", default="")

        loop_running = True
        while loop_running:
            p("\n}}gb Version: " + mgmt_version + "}}xx")
            p("""

}}mn======================================================================
}}mn| }}ybOPE Credential App                                                 }}mn|
}}mn| }}xxThis app will add student credentials to the computer and          }}mn|
}}mn| }}xxsecure the laptop for inmate use.                                  }}mn|
}}mn| }}yn(answer with quit to stop this tool)                               }}mn|
}}mn======================================================================}}xx

            """)

            tmp = ""
            last_student_user_prompt = ""
            while tmp.strip() == "":
                if student_user != "":
                    last_student_user_prompt = " }}cn[enter for previous student " + student_user + "]"
                p("}}ynPlease enter the username for the student" + last_student_user_prompt + ":}}xx ", False)
                tmp = input()
                if tmp.lower() == "quit":
                    p("}}rnGot QUIT - exiting credential!}}xx")
                    return None
                if tmp.strip() == "":
                    tmp = student_user
            student_user = tmp.strip()

            student_name = ""
            student_password = None

            if is_domain_joined:
                if base_dn:
                    success, result_msg = util.verify_student_account_in_ad(student_user, base_dn)
                    if not success:
                        p("}}rbUnable to verify student in AD: " + result_msg + "}}xx")
                        return None
                    student_name = result_msg
                else:
                    p("}}ybNo base_dn set; skipping AD validation.}}xx")
            else:
                p("}}ynPlease enter the student's full name:}}xx ", False)
                student_name = input().strip()
                if not student_name:
                    p("}}rbStudent name cannot be empty.}}xx")
                    continue

                import secrets
                student_password = secrets.token_urlsafe(6)
                util.store_password(student_user, student_password)

            ad_info = "Domain Joined" if is_domain_joined else "Standalone"
            student_text = student_user + " (" + student_name + ")"

            txt = """
}}mn======================================================================
}}mn| }}gbFound Student - Continue?                                          }}mn|
}}mn| }}ynCredential Version:    }}cn<mgmt_version>}}mn|
}}mn| }}ynActive Directory Info: }}cn<ad_info>}}mn|
}}mn| }}ynStudent Username:      }}cn<student_user>}}mn|
}}mn| }}ynSystem Serial Number:  }}cn<bios_serial_number>}}mn|
}}mn| }}ynDisk Serial Number:    }}cn<disk_serial_number>}}mn|
}}mn======================================================================}}xx
            """
            col_size = 44
            txt = txt.replace("<mgmt_version>", mgmt_version.ljust(col_size))
            txt = txt.replace("<ad_info>", ad_info.ljust(col_size))
            txt = txt.replace("<student_user>", student_text.ljust(col_size))
            txt = txt.replace("<bios_serial_number>",
                str(CredentialProcess.COMPUTER_INFO['bios_serial_number']).ljust(col_size))
            txt = txt.replace("<disk_serial_number>",
                str(CredentialProcess.COMPUTER_INFO['disk_boot_drive_serial_number']).ljust(col_size))

            p(txt)
            p("}}ybPress Y to continue: }}xx", False)
            tmp = input()
            if tmp.strip().lower() != "y":
                p("}}cnCanceled - trying again....}}xx")
                continue

            p("""
}}mn======================================================================
}}mn| }}rb====================       WARNING!!!         ==================== }}mn|
}}mn| }}xxEnsure that the boot from USB or boot from SD card options in      }}mn|
}}mn| }}xxthe bios are disabled and that the admin password is set to a      }}mn|
}}mn| }}xxstrong random password.                                            }}mn|
}}mn======================================================================}}xx
            """)
            p("}}ybHave you locked down the BIOS? Press Y to continue: }}xx", False)
            tmp = input()
            if tmp.strip().lower() != "y":
                p("}}cnCanceled - trying again....}}xx")
                continue

            loop_running = False

        return (student_user, student_name, student_password, is_domain_joined)

    @staticmethod
    def credential_input_verify_loop():
        """Gather student info either from registry (credential_config) or interactively."""
        credential_config = RegistrySettings.get_reg_value(value_name="credential_config", default=False)

        if credential_config:
            return CredentialProcess._get_student_info_from_registry()
        else:
            return CredentialProcess._get_student_info_interactive()

    @staticmethod
    def credential_laptop():
        
        # Are we running as admin w UAC??
        if not UserAccounts.is_uac_admin():
            p("}}rbNot Admin in UAC mode! - UAC Is required for credential process.}}xx")
            return False
    
        CredentialProcess.config_mgmt_utility_once()

        # Start time sync
        SystemTime.sync_time_w_ntp(force=True)
        
        # Get computer info
        CredentialProcess.COMPUTER_INFO = Computer.get_machine_info(print_info=False)
        
        # Are we using a proper edition win 10 or 11? (Home not supported, ed, pro, enterprise ok?)
        # OK - win 10 - pro, ed, enterprise
        # NOT OK - non win 10, win 10 home
        is_win10_plus = False
        is_win_home = True
        os_caption = CredentialProcess.COMPUTER_INFO["os_caption"].lower()
        if any(version in os_caption for version in ["microsoft windows 10", "microsoft windows 11", "microsoft windows server"]):
            is_win10_plus = True
        if any(version in os_caption for version in ["enterprise", "pro", "professional", "education", "workstation", "server"]):
            is_win_home = False

        if is_win10_plus is not True:
            p("}}rbNOT RUNNING ON WINDOWS 10 or 11!!!\nThis software is designed to work win windows 10 or 11 ONLY!\n (Enterprise, Professional, or Education OK, Home edition NOT supported)}}xx")
            return False
        if is_win_home is True:
            p("}}rbWIN10 or 11 HOME EDITION DETECTED!\nThis software is designed to work win windows 10 or 11 ONLY!\n (Enterprise, Professional, or Education OK, Home edition NOT supported)}}xx")
            return False

        # Disable guest account
        p("}}gnDisabling guest account}}xx", debug_level=2)
        UserAccounts.disable_guest_account()

        # Make sure folder exist and have proper permissions
        if not FolderPermissions.set_default_ope_folder_permissions():
            p("}}rbERROR - Unable to ensure folders are present and permissions are setup properly!}}xx")
            return False

        # Disable all student accounts
        UserAccounts.disable_student_accounts()

        result = CredentialProcess.credential_input_verify_loop()
        if result is None:
            return False
        (student_user, student_name, student_password, is_domain_joined) = result

        if not is_domain_joined:
            p("}}gnCreating local student windows account...}}xx")
            # student_name is the same as student_user for standalone mode (not domain joined)
            if not UserAccounts.create_local_student_account(student_user, student_user, student_password):
                p("}}rbError setting up OPE Student Account}}xx\n " + str(student_user))
                return False
        else:
            p("}}gnRunning as domain laptop, skipping create local student windows account...}}xx")

        if not RegistrySettings.store_credential_info(student_user, student_name, is_domain_joined):
            p("}}rbError saving registry info!}}xx")
            return False
        
        # Create desktop shortcut
        #p("\n}}gnSetting up LMS App...}}xx")
        Computer.create_win_shortcut(
            lnk_path = "c:\\users\\public\\desktop\\OPE LMS.lnk",
            ico_path = "%programdata%\\ope\\Services\\lms\\logo_icon.ico",
            target_path = "%programdata%\\ope\\Services\\lms\\ope_lms.exe",
            description = "Offline LMS app for Open Prison Education project"
        )
        
        return True

    @staticmethod
    def unlock_machine():
        ret = True

        is_domain_joined = CredentialProcess.is_credentialed_domain_joined()

        RegistrySettings.add_mgmt_utility_to_path()

        RegistrySettings.set_machine_locked(False)

        if not UserAccounts.log_out_all_students():
            p("}}rbUnable to log out students!}}xx")
            return False
        
        if not is_domain_joined:
            GroupPolicy.reset_group_policy_to_default()
        else:
            p("}}ybRunning in Domain Mode, not resetting gpol.}}xx")

        if not is_domain_joined:
            GroupPolicy.reset_firewall_policy()
        else:
            p("}}ybRunning in Domain Mode, not resetting firewall.}}xx")

        return ret

    @staticmethod
    def ensure_opeservice_running():
        
        if RegistrySettings.is_debug():
            p("}}ynDEBUG MODE ON - Skipping ensure OPEService is running}}xx")
            return True
        
        ret = False

        w = Computer.get_wmi_connection()

        services = w.Win32_Service(Name="OPEService")
        found = False
        for service in services:
            found = True
            if service.state == "Running":
                ret = True
            else:
                p("}}rbOPEService not in running state! " + str(service.state) + \
                    "\nTry rebooting and check again}}xx")

        if not found:
            p("}}rbOPEService not installed! - Try running credential again!}}xx")                
        return ret

    @staticmethod
    def lock_machine():
        ret = True

        RegistrySettings.add_mgmt_utility_to_path()

        student_user_name = CredentialProcess.get_credentialed_student()
        if student_user_name is None:
            p("}}rbNot Credentiled! - Unable to find credentialed student - not locking machine!}}xx")
            return False

        is_domain_joined = CredentialProcess.is_credentialed_domain_joined()

        if not UserAccounts.log_out_all_students():
            p("}}rbUnable to log out students!}}xx")
            return False

        if not is_domain_joined:
            if not GroupPolicy.apply_firewall_policy():
                p("}}rbError - Could Not apply firewall policy!\nStudent Account NOT unlocked!}}xx")
                return False
        else:
            p("}}ybRunning in Domain Mode, not applying firewall policy.}}xx")

        if not GroupPolicy.apply_group_policy():
            p("}}rbError - Could Not apply group policy!\nStudent Account NOT unlocked!}}xx")
            return False
        
        if not FolderPermissions.lock_boot_settings():
            p("}}rbError - Could not lock boot settings!\nStudent Account NOT unlocked!}}xx")
            return False
        
        if not FolderPermissions.disable_volume_shadow_copies():
            p("}}rbError - Could not disable VSS settings!\nStudent Account NOT unlocked!}}xx")
            return False

        if not RegistrySettings.set_default_ope_registry_permissions(force=True):
            p("}}rbError - Could not reset registry permissions!\nStudent Account NOT unlocked!}}xx")
            return False

        if not FolderPermissions.set_default_ope_folder_permissions(force=True):
            p("}}rbError - Could not reset ope folder permissions!\nStudent Account NOT unlocked!}}xx")
            return False
        
        if not UserAccounts.set_default_groups_for_student(student_user_name):
            p("}}rbError - Could not reset default groups for student!\nStudent Account NOT unlocked!}}xx")
            return False

        if not CredentialProcess.ensure_opeservice_running():
            p("}}rbError - Verify OPEService is running!\nStudent Account NOT unlocked!}}xx")
            return False
        
        if not is_domain_joined:
            if not UserAccounts.enable_account(student_user_name):
                p("}}rbError - Failed to enable student account: " + str(student_user_name) + "}}xx")
                return False

        RegistrySettings.set_machine_locked(True)

        return ret

    @staticmethod
    def is_time_to_upgrade():
        # How long has it been since we tried to upgrade?
        last_upgrade_time = RegistrySettings.get_reg_value(value_name="last_upgrade_time", default=0)
        curr_time = time.time()

        # Only check for upgrades every 5 minutes
        if curr_time - last_upgrade_time > 300:
            return True
        
        return False

    @staticmethod
    def is_version_newer(current_version, remote_version):
        # Parse the strings and see which version is newer
        ret = False

        # Split out the parts
        cv_parts = current_version.split(".")
        rv_parts = remote_version.split(".")

        cv_major = 0
        cv_minor = 0
        cv_revision = 0

        try:
            cv_major = int(cv_parts[0])
        except:
            pass
        try:
            cv_minor = int(cv_parts[1])
        except:
            pass
        try:
            cv_revision = int(cv_parts[2])
        except:
            pass

        rv_major = 0
        rv_minor = 0
        rv_revision = 0

        try:
            rv_major = int(rv_parts[0])
        except:
            pass
        try:
            rv_minor = int(rv_parts[1])
        except:
            pass
        try:
            rv_revision = int(rv_parts[2])
        except:
            pass

        p(str(cv_major) + "." + str(cv_minor) + "." + str(cv_revision) + " -> " + \
            str(rv_major) + "." + str(rv_minor) + "." + str(rv_revision))
        # Is major version bigger?
        if rv_major > cv_major:
            ret = True
        # Is minor version bigger?
        if rv_major == cv_major and rv_minor > cv_minor:
            ret = True
        # Is revision bigger?
        if rv_major == cv_major and rv_minor == cv_minor and rv_revision > cv_revision:
            ret = True

        return ret

    @staticmethod
    def start_upgrade_process(branch=None, force_upgrade=None):
        ret = None

        # Command that is run to start this function
        only_for = "start_upgrade"
        
        # Force upgrade - even if versions match
        if force_upgrade is None:
            force_upgrade = util.pop_force_flag(only_for=only_for)
        
        if not force_upgrade is True and not CredentialProcess.is_time_to_upgrade():
            p("}}gnNot time to check for upgrades yet, skipping...}}xx", log_level=3)
            return None
        p("}}rbSoftware Upgrades Disabled...}}xx")
        # TODO - Reimplement software upgrade with download and unpack zip - remove GIT stuff
        return None

        curr_branch = branch
        if curr_branch is None:
            # See if a parameter was provided
            curr_branch = util.get_param(2, None, only_for=only_for)
            if curr_branch is not None:
                # Save this branch for next time
                RegistrySettings.set_git_branch(curr_branch)
        
        p("Running Upgrade...")
        p_state("Starting Software Update...", title="Checking For Software Updates")
        RegistrySettings.set_reg_value(value_name="last_upgrade_time", value=time.time())
       
        # If branch is still empty, get it from the registry
        if curr_branch is None:
            curr_branch = RegistrySettings.get_git_branch()

        # Start by grabbing any new stuff from the git server
        ret = ProcessManagement.git_pull_branch(curr_branch)
        if ret is False:
            # Not critical if this fails - apply whatever is present if it is
            # a different version number
            # return False
            p("}}ybWARNING - Unable to pull updates for git server!}}xx")
            pass
        
        # Check the mgmt.version files to see if we have a new version
        ope_laptop_binaries_path = os.path.expandvars("%programdata%\\ope\\tmp\\ope_laptop_binaries")
        # Get the path to the mgmt.version file
        git_version_path = os.path.join(ope_laptop_binaries_path, "Services", "mgmt", "mgmt.version")

        # Do we have a new version?
        curr_version = CredentialProcess.get_mgmt_version()
        git_version = CredentialProcess.get_mgmt_version(git_version_path)

        if git_version == "NO VERSION":
            # No version file found
            p("}}ynNo version file found in git repo, skipping upgrade!}}xx")
            return None
        
        if not force_upgrade is True and not CredentialProcess.is_version_newer(curr_version, git_version):
            # Same version - no upgrade needed
            p("}}gnOPE Software up to date: " + str(git_version) + " not newer than " + str(curr_version) + " - (not upgrading)}}xx")
            return None

        # Version is different, prep for update
        forced = ""
        if force_upgrade:
            forced = "}}yb(upgrade forced)}}gn"
        
        p_state("Software Update Found, Updating...", title="Applying Software Updates")
        p("}}gnFound new version " + forced + " - starting upgrade process: " + \
            curr_version + " --> " + git_version + "}}xx")
        
        # Lock user accounts
        domain_joined = Computer.is_domain_joined()

        if not domain_joined:
            if not UserAccounts.disable_student_accounts():
                p("}}rbERROR - Unable to disable student accounts prior to upgrade!}}xx")
                return False

        # Make sure students are logged out
        if not UserAccounts.log_out_all_students():
            p("}}rbERROR - Unable to log out student accounts prior to upgrade!}}xx")
            return False
        
        p("}}ynLaunching OPE Software Update process...}}xx")
        RegistrySettings.set_reg_value(value_name="upgrade_started", value=time.time())
        
        # run the upgrade_ope.cmd from the TMP rc folder!!!
        bat_path = os.path.join(ope_laptop_binaries_path, "Services\\mgmt\\rc\\upgrade_ope.cmd")
        # Add the redirect so we end up with a log file
        if not ProcessManagement.run_detatched_cmd(bat_path + " >> %programdata%\\ope\\tmp\\log\\upgrade.log 2>&1"):
            p("}}rbERROR - Unable to start upgrade process!}}xx")
            return False
        # Make sure to exit this app??
        #sys.exit(0)

        # Return True to indicate the upgrade process has started
        return True

    @staticmethod
    def store_ope_version():
        # Store new version
        curr_version = CredentialProcess.get_mgmt_version()
        RegistrySettings.set_reg_value(value_name="ope_version", value=curr_version)

    @staticmethod
    def finish_upgrade_process():
        p("}}ynFinish Upgrade Process Called, continuing...}}xx")
        CredentialProcess.store_ope_version()
        # If everything was successful, then
        # - Re-apply security
        # - lock_machine also re-enables credentialed account if succesful
        if not CredentialProcess.lock_machine():
            p("}}rbERROR - Unable to lock machine after upgrade!}}xx")
            return False

        p("}}gbSUCCESS! - Machine locked and user account enabled.}}xx")
        RegistrySettings.set_reg_value(value_name="upgrade_started", value=-1)
        return True

    @staticmethod
    def sync_student_password():
        # Bounce off SMC to sync student password (in case it has changed)

        if not RegistrySettings.is_timer_expired(timer_name="sync_student_password_timer", time_span=2400):
            # Not time to sync yet
            return True
        # TODO 
        # Are we credentialed?
        p_state("Syncing Password", title="Password Sync", kill_logon=False)
        # Send of info

        # Set password

        p("}}ybsync_student_password - Coming Soon...}}xx")
        return True

    @staticmethod
    def sync_lms_app_data(force=False):
        # Command that is run to start this function
        only_for = "sync_lms_app_data"
        cmd_force = util.pop_force_flag(only_for=only_for)
        if cmd_force is True:
            force = True

        # Make the LMS app sync in headless mode (auto sync)
        if force is False and not RegistrySettings.is_timer_expired(timer_name="sync_lms_app_data_timer", time_span=2400):
            p("}}gnNot time to sync lms app data}}xx")
            return True
        
        p_state("LMS App Syncing, may take several minutes...", title="LMS Syncing")

        RegistrySettings.set_reg_value(value_name="last_sync_lms_app_time", value=time.time())

        # FIRST - Make sure the appdata folder is owned by the current student
        # so we don't break their profile later (e.g. owned by system)
        curr_student = CredentialProcess.get_credentialed_student()
        if curr_student is None:
            # No credentialed!
            p("Not currently credentialed, not syncing LMS data.")
            RegistrySettings.set_reg_value(value_name="last_sync_lms_app_message", value="<not synced yet>")
            return True
        
        # Figure out path for this user
        profile_path = "c:\\users\\" + curr_student
        # Make sure profile path exists, or don't sync as syncing will end up creating 
        # files owned by the system user and screw things up
        if not os.path.exists(profile_path):
            p("No profile folder for student, have them login before auto sync will work: " + str(curr_student))
            return False
        
        # See if we have permissions to write to the folder - make sure we do...
        try:
            # Elevate process rights
            UserAccounts.elevate_process_privilege_to_se_security_name()
            # Get permissions (list of things like 'r', 'w', 'a', etc...)
            perms = FolderPermissions.get_acl_rights_for_user(profile_path, curr_student)
            #p(str(perms))
            if "w" not in perms:
                p("Adding permissions for profile folder: " + str(profile_path))
                FolderPermissions.set_home_folder_permissions(profile_path, curr_student, walk_files=False)
        except Exception as ex:
            p("ERROR - Unable to set folder permissions for profile folder: " + str(profile_path) + "\n" + str(ex))
        
        # Redirect stderr to null and write output to the log file
        cmd = "%programdata%\\ope\\Services\\lms\\ope_lms.exe quiet_sync"
        returncode, output = ProcessManagement.run_cmd(cmd,
            require_return_code=0, cmd_timeout=3600)
        
        sync_finished = datetime.datetime.strftime(datetime.datetime.now(), "%m/%d %I:%M%p")
        if returncode == -2:
            # Error running command?
            msg = "}}rbError - Unable to sync lms app data!}}xx\n" + output
            p_state(msg, title="LMS Sync Failed!")
            RegistrySettings.set_reg_value(value_name="last_sync_lms_app_message", value="LMS Sync Failed: " + sync_finished)
            # Make sure we try to run this again soon
            RegistrySettings.reset_timer(timer_name="sync_lms_app_data_timer")
            return False
        else:
            RegistrySettings.set_reg_value(value_name="last_sync_lms_app_message", value="LMS Sync Finished: " + sync_finished)
        p("Ret: " + str(returncode) + " - " + output, log_level=3)
        # Write the output to the state log
        p_state(output, title="LMS Syncing")

        return True
    
    @staticmethod
    def sync_work_folder():
        # Start sync process to sync the home/work folder for the user
        if not RegistrySettings.is_timer_expired(timer_name="sync_work_folder_timer", time_span=1200):
            # Not time to sync yet
            return True
        # TODO
        p_state("Syncing Work Folder...", title="Work Folder", kill_logon=False)
        p("}}ybsync_work_folder - Coming Soon...}}xx")
        return True
    
    @staticmethod
    def sync_logs_to_smc():
        if not RegistrySettings.is_timer_expired(timer_name="sync_logs_to_smc_timer", time_span=2400):
            # Not time to sync yet
            return True
        # TODO
        # 
        p_state("Pushing SMC Logs...", title="Pushing Logs", kill_logon=False)
        p("}}ybsync_logs_to_smc - Coming Soon...}}xx") 
        return True

    @staticmethod
    def ping_smc(smc_url=None):
        # See if we can bounce off the SMC server and get a response
        p_state("Starting ping_smc", state="none", title="Ping SMC", kill_logon=False)
        # Command that is run to start this function
        only_for = "ping_smc"

        force = util.pop_force_flag(only_for=only_for)

        if smc_url is None:
            # Try and get from command line
            smc_url = util.get_param(2, None, only_for=only_for)
        if smc_url is None:
            # Nothing on command line? Get from registry
            smc_url = RegistrySettings.get_reg_value(value_name="smc_url", default="https://smc.corrections.sbctc.edu")

        if not force is True and not RegistrySettings.is_timer_expired(timer_name="ping_smc_timer", time_span=15):
            p("}}gnNot time to ping smc, skipping...}}xx", log_level=5)
            return True
        
        #RegistrySettings.set_reg_value(value_name="last_smc_ping_time", value=time.time())
        
        if not RestClient.ping_smc(smc_url):
            p("}}mnNot able to ping SMC " + smc_url + "}}xx", log_level=4)
            # Ok to return true - we just don't do more maintenance
            p_state("Offline mode.", title="Offline", state="IDLE", kill_logon=False)
            RegistrySettings.set_reg_value(value_name="is_online", value=0)
            return True

        # We are connected, do maintenance
        p_state("SMC Detected, online mode...", state="none", title="SMC Detected", kill_logon=False)
        # Save the state in the registry
        RegistrySettings.set_reg_value(value_name="is_online", value=1)

        # Check if time to auto upgrade
        #p_state("Sync Processing...", title="Syncing")
        # Don't force upgrade process - have to call that seperatly if you want to force it
        if CredentialProcess.start_upgrade_process() is True:
            # Upgrade starting - skip the rest of this for now - it will try again later
            p("}}ynPing_SMC - Exiting early, software upgrade in progress (separate process running for upgrade)...}}xx")
            return True
        # NOTE - If there is an upgrade, this will exit and re-run ping_smc when done

        # Check if time to sync time
        SystemTime.sync_time_w_ntp()

        # Make sure the student password is updated (if changed in SMC)
        CredentialProcess.sync_student_password()

        # Have the OPE_LMS app sync (assignments, course work)
        # CredentialProcess.sync_lms_app_data()

        # Dropbox like sync - copy files back/forth between laptop/desktop home dir
        CredentialProcess.sync_work_folder()

        # Push logs and screenshots up to the SMC server
        CredentialProcess.sync_logs_to_smc()

        # Refresh version number in the registry
        CredentialProcess.store_ope_version()

        p_state("Sync Finished.", title="Sync Complete", state="DONE")
        return True

    @staticmethod
    def run_tests():
        p("}}gnRunning Tests...}}xx")

        p(CredentialProcess.get_mgmt_version())
        p("is_domain_joined: " + str(CredentialProcess.is_credentialed_domain_joined()))
        pass


if __name__ == "__main__":
    CredentialProcess.run_tests()
    
