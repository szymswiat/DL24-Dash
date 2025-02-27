# DL24-Dash

A Python-based CLI tool for monitoring and visualizing data from DL24 electronic load devices. This tool provides real-time monitoring capabilities and data visualization through an interactive dashboard.

## Features

- Real-time discharge monitoring
- Automatic data logging to CSV files
- Interactive data visualization dashboard
- Support for comparing multiple discharge sessions
- Bluetooth serial communication with DL24 devices

## Prerequisites

- Python 3.x
- Bluetooth connectivity
- DL24 electronic load device

## Installation

1. Install using pip:
```bash
pip install dl24-dash
```

Or using UV (faster alternative):
```bash
# Install UV if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install DL24-Dash
uv tool install dl24-dash
```

2. Set up the environment:
```bash
uv sync
```

## Development Setup

For development or if you want to run from source:

1. Install Astral UV (Python package manager):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Set up the development environment:
```bash
uv sync
```

## Usage

### Connecting the Device

1. Connect your DL24 device via Bluetooth in serial port mode
2. The device should be available at `/dev/rfcomm0` (path may vary depending on your system)

### Monitoring Tool

Start a new monitoring session:
```bash
uv run dl24-dash monitor --start-new-session --current 4 test_discharge
```

Parameters:
- `--start-new-session`: Initiates a new monitoring session
- `--current 4`: Sets the discharge current to 4A
- `test_discharge`: Session name for data storage

The monitoring dashboard will be available at [http://127.0.0.1:8050/](http://127.0.0.1:8050/)

### Plotting Tool

Compare multiple discharge sessions:
```bash
uv run dl24_dash/main.py plot data1 data2 data3
```

The tool will:
- Scan specified directories for CSV files
- Generate an interactive comparison chart
- Display results at [http://127.0.0.1:8050/](http://127.0.0.1:8050/)

## Help

For additional information and command options:
```bash
uv run dl24_dash/main.py --help
```
