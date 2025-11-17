# Release Log

## 25.11.3
### credential script:
- New automated credentialing workflow (`credential.exe`) instead of (`credential.cmd`) with config file input instead of CLI prompting
- Enhanced error handling and initial checks (BIOS lock, admin privileges, config validation)
- Password storage in Windows Credential Manager (SMC admin passwords)
- Debug mode support (skips service installation, uses Python modules instead of exe)
- Added credential process logging in ope-credential.log
- Dynamic configuration summary with user confirmation
- Fixed LMS log file access denied
- LMS background sync disabled
### mgmt modules:
- Refactored credential process handling
- Minor updates to folder permissions, registry settings, and system time modules
### Lock Screen Widget
- Removed lock screen widget

## 25.8.25
### credential script:
- Removed change the time and license windows as it's handled by being on the domain.
