# LotteryApp

LotteryApp is a Python PyQt5 application that provides an interactive and animated lottery drawing experience. The app smoothly scrolls numbers while playing sound effects and highlights the winning number. It supports both numeric ranges and individual numbers, and offers an option to defer removal of the winning number.

## Table of Contents

- [Features](#features)
- [Usage](#usage)
  - [Pre-built Windows Executable](#pre-built-windows-executable)
- [Development](#development)
  - [Setting Up a Virtual Environment](#setting-up-a-virtual-environment)
  - [Upgrading pip](#upgrading-pip)
  - [Installing Dependencies](#installing-dependencies)
- [Packaging with PyInstaller](#packaging-with-pyinstaller)
- [License](#license)

## Features

- Smooth animated scrolling of numbers.
- Integrated sound effects during the draw.
- Supports both number ranges and single numbers.
- Option to defer removal of the winning number.
- Can be packaged as a standalone executable using PyInstaller.

## Usage

### Pre-built Windows Executable

A pre-built Windows executable (`lottery.exe`) is provided in this repository. Simply download and run the executable on your Windows machine to start the application.

## Development

To set up your development environment for LotteryApp, follow these steps:

### Setting Up a Virtual Environment

1. Open your terminal or command prompt.
2. Navigate to the project directory.
3. Create a virtual environment by running:
   ```bash
   python -m venv venv
   ```
4. Activate the virtual environment:
   - **Windows:**
     ```bash
     venv\Scripts\Activate.ps1
     ```
   - **macOS/Linux:**
     ```bash
     source venv/bin/activate
     ```

### Upgrading pip

Ensure you have the latest version of pip (version 25 or higher) by running:
```bash
pip install --upgrade pip
```

### Installing Dependencies

With your virtual environment activated, install the required Python packages:
```bash
pip install -r requirements.txt
```

## Packaging with PyInstaller

To create a standalone executable using PyInstaller, run the following command in your terminal:
```bash
pyinstaller --onefile --windowed --add-data "sounds\wheel;sounds\wheel" --add-data "sounds\winner;sounds\winner" lottery.py
```
Adjust the `--add-data` parameter to include the correct paths for any additional assets required by the application.

## License

LotteryApp is licensed under the [GNU General Public License v3](https://www.gnu.org/licenses/gpl-3.0.en.html).  
