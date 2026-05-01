# Needed for running as alternate user
import win32ts
import win32security
import win32con
import win32process
import win32api
import win32profile

import subprocess
import sys
import os


from common.color import p
from common import util
from mgmt_UserAccounts import UserAccounts
from mgmt_ProcessManagement import ProcessManagement

class ScreenShot:
    # Class to deal with grabbing screen shots
    
    # Disable sshot if this is set
    DISABLE_SSHOT = False

    @staticmethod
    def init_globals():
        if os.path.isfile(os.path.join(util.ROOT_FOLDER, ".disable_sshot")):
            p("}}rb**** WARNING **** screen shots disabled!}}xx", log_level=2)
            ScreenShot.DISABLE_SSHOT = True
    pass

    @staticmethod
    def take_screenshot():
        ret = False
        ScreenShot.init_globals()

        if ScreenShot.DISABLE_SSHOT:
            p("}}ybSkipping screenshot - disabled by .disable_sshot file}}xx", log_level=2)
            return
        
        # Find the logged in user and run the sshot.exe app
        cmd = os.path.join(util.BINARIES_FOLDER, "sshot", "sshot.exe")
        
        p("}}gnTrying to run " + cmd + "}}xx")

        user_token = UserAccounts.get_active_user_token()
        if user_token is None:
            p("}}ybSkipping screenshot - user not logged in?}}xx")
            return ret

        sidObj, intVal = win32security.GetTokenInformation(user_token, win32security.TokenUser)
        #source = win32security.GetTokenInformation(tokenh, TokenSource)
        if sidObj:
            accountName, domainName, accountTypeInt = \
                win32security.LookupAccountSid(".", sidObj)
        else:
            p("}}rnSkipping screenshot - unable to get user token}}xx")
            return None
        user_name = domainName + "\\" + accountName

        # If user is in the administrators group, skip taking the sshot
        admin_group_list = UserAccounts.get_admin_groups()
        # See if the process token has membership in one of the following groups
        if UserAccounts.is_process_in_group(user_token, admin_group_list, find_first=True):
            p("}}mbUser (" + user_name + ") is in admin group, skipping screen shot...}}xx")
            return True

        p("}}gnRunning As: " + user_name + "}}xx", log_level=2)

        # Use win create process function
        si = win32process.STARTUPINFO()
        si.dwFlags = win32process.STARTF_USESHOWWINDOW
        si.wShowWindow = win32con.SW_NORMAL
        # si.lpDesktop = "WinSta0\Default"   ## For secure desktop, "WinSta0\\Winlogon"
        si.lpDesktop = "WinSta0\\Default"

        # Setup envinroment for the user
        environment = win32profile.CreateEnvironmentBlock(user_token, False)

        try:
            (hProcess, hThread, dwProcessId, dwThreadId) = win32process.CreateProcessAsUser(user_token,
                                            None,   # AppName (really command line, blank if cmd line supplied)
                                            "\"" + cmd + "\"",  # Command Line (blank if app supplied)
                                            None,  # Process Attributes
                                            None,  # Thread Attributes
                                            0,  # Inherits Handles
                                            win32con.NORMAL_PRIORITY_CLASS,  # or win32con.CREATE_NEW_CONSOLE,
                                            environment,  # Environment
                                            os.path.dirname(cmd),  # Curr directory
                                            si)  # Startup info

            p("Process Started: " + str(dwProcessId), log_level=5)
            p(hProcess, log_level=5)
            ret = True
        except Exception as e:
            p("}}rnError launching process:}}xx\n" + str(e), log_level=1)
            
        # Cleanup
        user_token.close()

            
        if ret is True:
            p("}}gnScreenshot taken.}}xx", log_level=3)
        
        return ret

