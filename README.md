# InstSpec - Instrument Data Sheet Generator & Sizer

> Professional engineering tool for instrument sizing and datasheet generation

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.36+-red.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

InstSpec adalah aplikasi web berbasis Streamlit untuk **sizing instrument** (orifice plate, control valve, flow element, DP transmitter, thermowell) dan **generate data sheet profesional** sesuai standar ISA-20. Ditujukan untuk instrument engineer di industri oil & gas, petrochemical, power generation, dan process plant.

## Features

### 🔵 Orifice Plate Sizer
- ISO 5167-2 compliant calculations (Reader-Harris/Gallagher equation)
- Corner tap, flange tap, and D/D/2 tap support
- Beta ratio optimization
- Reynolds number iteration
- Expansibility factor for gases
- Permanent pressure loss calculation
- Straight run requirements (ISO 5167-2 Table 3)
- Uncertainty analysis

### 🔧 Control Valve Sizer
- ISA-75.01 / IEC 60534-2-1 compliant
- Liquid, gas, vapor, and two-phase flow sizing
- Choked flow detection
- Cavitation and flashing analysis
- Noise prediction (ISA-75.01.01-2012)
- Valve selection with Cv tables
- Characteristic curves (equal %, linear, quick-open)
- % opening calculation at min/normal/max flow

### 📏 Flow Element Sizer
- Venturi tube (ISO 5167-3)
- Flow nozzle (ISO 5167-3)
- V-Cone meter
- Wedge meter

### 📡 DP Transmitter Range Checker
- Rangeability verification
- Turndown analysis
- Accuracy at min/max flow
- 4-20mA signal span check

### 🌡️ Thermowell Wake Frequency Calculator
- ASME PTC 19.3 TW-2016 compliant
- Natural frequency calculation
- Strouhal wake frequency
- Frequency ratio verification (safe/caution/unsafe)
- Stress analysis (bending, pressure, fatigue)
- Material properties at temperature

### 📄 Data Sheet Generator
- ISA-20 format compliant
- PDF generation with ReportLab
- Excel export with openpyxl
- Multi-vendor templates (Emerson, Yokogawa, Endress+Hauser, ABB, Siemens)
- Custom template support
- Revision tracking and management

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Framework | Python 3.11+ / Streamlit | Web UI |
| Calculation | NumPy + SciPy | Numerical computation |
| Fluid Props | CoolProp | Real thermodynamic properties |
| PDF | ReportLab | Precision datasheet layout |
| Excel | openpyxl | Editable datasheet export |
| Database | SQLite via SQLAlchemy | Local project storage |
| Testing | pytest + hypothesis | Unit + property-based tests |

## Installation

### Prerequisites

- Python 3.11 or higher
- pip package manager

### Install from Source

```bash
git clone https://github.com/arienug20/instspec.git
cd instspec
pip install -r requirements.txt
```

### Running the Application

```bash
streamlit run src/app.py
```

The application will open in your browser at `http://localhost:8501`

### Docker Deployment

```bash
docker-compose up -d
```

## Quick Start

1. **Create a Project**
   - Click "📋 Project List" → "➕ Create Project"
   - Enter project details (name, client, location)

2. **Add an Instrument**
   - Click "➕ New Instrument"
   - Select instrument type (e.g., Orifice Plate)
   - Enter basic information (tag number, service, line number)

3. **Perform Sizing Calculations**
   - Navigate to the appropriate sizer page (e.g., "🔵 Orifice Sizer")
   - Enter process conditions, fluid properties, pipe data
   - Click "Calculate" to get results

4. **Generate Data Sheet**
   - Review sizing results
   - Click "📄 Data Sheet Preview"
   - Download as PDF or Excel

## Project Status

**Current Version:** v0.1.0 (Sprint 1 - Foundation)

### Completed (Sprint 1)
- ✅ Project structure and configuration
- ✅ SQLite database with project/instrument/revision management
- ✅ Unit converter module (pressure, temperature, flow, length, viscosity, density)
- ✅ Data models for all instrument types
- ✅ Fluid presets JSON (15 common fluids)
- ✅ Pipe schedule database (ASME B36.10/B36.19)
- ✅ Input validation framework
- ✅ Streamlit app shell with navigation

### In Progress (Sprint 2)
- 🔄 Orifice plate sizer implementation
- 🔄 Reader-Harris/Gallagher discharge coefficient
- 🔄 Beta ratio optimization
- 🔄 Reynolds number iteration
- 🔄 Expansibility factor calculation

### Planned
- ⏳ Control valve sizer (Sprint 3)
- ⏳ Flow element sizer (Sprint 4)
- ⏳ DP transmitter checker (Sprint 4)
- ⏳ Thermowell wake frequency (Sprint 4)
- ⏳ Data sheet PDF generator (Sprint 5)
- ⏳ Multi-vendor templates (Sprint 6)
- ⏳ CoolProp deep integration (Sprint 7)
- ⏳ Full documentation (Sprint 8)

## Documentation

- [Getting Started Guide](docs/getting_started.md)
- [Orifice Sizing Tutorial](docs/orifice_tutorial.md)
- [Control Valve Tutorial](docs/control_valve_tutorial.md)
- [Data Sheet Guide](docs/datasheet_guide.md)
- [Thermowell Guide](docs/thermowell_guide.md)

## Development

### Running Tests

```bash
pytest tests/ -v --cov=src
```

### Code Style

```bash
ruff check src/ tests/
mypy src/ --ignore-missing-imports
```

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

**Arie Nugraha** - [GitHub](https://github.com/arienug20)

## Acknowledgments

- ISO standards for calculation methods
- CoolProp for fluid property database
- Streamlit for the web framework
- ReportLab for PDF generation

---

**Note:** This is a work in progress. Features are being implemented according to the [implementation plan](plans/06-instspec.md).