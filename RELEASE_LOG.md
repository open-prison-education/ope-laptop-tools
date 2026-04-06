# Release Log

## 26.4.1
### credential script:
- Replaced SMC server dependency with local Active Directory (ADSI) verification for student accounts
- Removed need for SMC URL, SMC admin username, and SMC admin password configuration
- Added `is_domain_joined` and `base_dn` as new required configuration keys in `credential_config.json`
- Student accounts on domain-joined laptops are now validated directly against Active Directory
- Auto-generates secure passwords for students on non-domain-joined (standalone) laptops
- Fixed crash when `approved_nics` registry value is empty or contains invalid JSON
- Improved debug mode: skips OPEService startup check when debug is enabled
### mgmt modules:
- Replaced `laptop_network_type` / `laptop_domain_name` with a single `is_domain_joined` flag throughout
- Removed `store_smc_config`, `trust_ope_certs`, and SMC-related registry operations
- Simplified interactive configuration by removing all SMC-related prompts
- Domain name is now read from the machine's computer system info instead of stored registry values

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
