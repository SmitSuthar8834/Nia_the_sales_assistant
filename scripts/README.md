# Scripts Directory

This directory contains utility scripts organized by functionality.

## Directory Structure

### debugging/
Contains scripts for debugging and troubleshooting:
- `debug_frontend_issue.py` - Debug frontend blank results issues
- `debug_frontend_500.py` - Debug 500 errors in frontend

### testing/
Contains test scripts and test utilities:
- `run_tests.py` - Main test runner for organized test structure
- `run_frontend_tests.py` - Comprehensive frontend test runner
- `quick_functionality_test.py` - Quick core functionality tests (no AI calls)
- `simple_test.py` - Simple Django setup and import tests
- `test_frontend_manual.html` - Manual frontend testing interface
- `test_voice_frontend.html` - Voice service testing interface

### deployment/
Contains deployment and server management scripts:
- `restart_server.py` - Test server status and provide restart instructions

## Usage

All scripts should be run from the project root directory:

```bash
# Testing scripts
python scripts/testing/run_tests.py list
python scripts/testing/quick_functionality_test.py

# Debugging scripts
python scripts/debugging/debug_frontend_issue.py

# Deployment scripts
python scripts/deployment/restart_server.py
```

## Notes

- All Python scripts have been updated to work correctly from their new locations
- Path imports have been adjusted to work from the scripts subdirectories
- Documentation has been updated to reflect the new script locations