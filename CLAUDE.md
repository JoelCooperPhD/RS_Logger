# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RS_Logger is a scientific data logging system developed by Red Scientific. It's designed for measuring and recording human response times and potentially other physiological data like eye movements. The system consists of multiple hardware modules with both wired and wireless variants.

## Architecture

The application follows a three-layer architecture:

1. **Firmware Layer**: Contains the code that runs on the various hardware devices.
   - SFT (Stimulus-Feature-Time): Configurable multi-stimuli system
   - sDRT: Simple Detection Response Task module
   - sVOG: Eye tracking module
   - wDRT: Wireless Detection Response Task module
   - wVOG: Wireless eye tracking module

2. **Hardware I/O Layer**: Manages communication with the hardware devices.
   - Handles USB and XBee radio connections
   - Distributes messages between the UI and hardware

3. **User Interface Layer**: Provides the GUI for controlling the system.
   - Contains specific UI components for each hardware module
   - Includes common widgets like experiment controls, timers, and note-taking

The entire application uses threading, with communication handled by SimpleQueue instances.

## Common Commands

### Building the Application

```
pyinstaller --onefile --noconsole --clean --noconfirm --add-data="rs_icon.ico;." --add-data="RSLogger\img\questionmark_15.png;RSLogger\img" --add-data="RSLogger\img\record.png;RSLogger\img" --add-data="RSLogger\img\pause.png;RSLogger\img" --add-data="RSLogger\img\rs_icon.ico;RSLogger\img" --icon=rs_icon.ico --name="RS_Logger" main.py
```

Or simply use the provided batch file:

```
make.bat
```

### Running Tests

Tests are organized for each firmware module with dedicated test directories:

```
# Run all tests for a specific module (e.g., wVOG)
python RSLogger/Firmware/wVOG_FW/tests/run_all_tests.py

# Run a specific test
python RSLogger/Firmware/wVOG_FW/tests/timers_test.py
```

Note that these tests are designed for the embedded systems and may require specific hardware to function correctly.

## Version Management

When updating the version:

1. Update `version.txt` in the root directory
2. Update `__version__` in `main.py` 
3. Update version in `dist/InstallerSetup.iss` for the installer

Current version: 1.3

## Key Components

### Hardware Communication

- `hi_controller.py`: Central hub for hardware communication
- `usb_connect.py`: Manages USB connections
- `remote_connect.py`: Manages XBee radio connections
- Each device has a dedicated controller class (e.g., `wDRT_HIController.py`)

### User Interface

- `ui_controller.py`: Manages the UI components
- Device-specific UI modules (e.g., `wDRT_UIController.py`)
- Common UI widgets in `RSLogger/user_interface/Logger/`

### Inter-Thread Communication

The application uses SimpleQueue instances for communication:
- `q_2_hi`: Messages from UI to hardware
- `q_2_ui`: Messages from hardware to UI

Messages follow the format: `{device}>{port}>{key}>{val}`

## Dependencies

- Python 3.12+
- digi-xbee
- pyserial
- pywin32
- serial
- tkinter (standard library)