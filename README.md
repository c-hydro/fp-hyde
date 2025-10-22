# FloodPROOFS – Hydrological Data Engines (HyDE)

[![License: EUPL 1.2](https://img.shields.io/badge/License-EUPL%201.2-blue.svg)](https://joinup.ec.europa.eu/collection/eupl/eupl-text-11-12)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![CIMA Research Foundation](https://img.shields.io/badge/Made%20by-CIMA%20Research%20Foundation-green)](https://www.cimafoundation.org)

---

## 🌊 Overview

**fp-hyde** (Hydrological Data Engines) is part of the **FloodPROOFS** modelling and forecasting chain developed by [CIMA Research Foundation](https://www.cimafoundation.org) and the [c-hydro](https://github.com/c-hydro) initiative.  
It provides the **data-processing core** of the FloodPROOFS system, organizing and transforming hydrological, meteorological, and geospatial datasets for use in forecasting, risk assessment, and decision-support applications.

HyDE manages the entire data workflow — from raw inputs (e.g., rainfall, temperature, soil moisture) to structured datasets used by the **Hydrological Model Continuum (HMC)** and analysis tools (**HAT**).

---

## ⚙️ Key Features

- 🛰️ **Input Management** — handles multi-source meteorological and hydrological datasets (gridded, station-based, remote sensing).
- 🧩 **Data Preprocessing** — temporal and spatial interpolation, resampling, and harmonization.
- 🗺️ **Geospatial Support** — full GIS integration (raster/vector) with NetCDF, GeoTIFF, and shapefile support.
- 📦 **Flexible Configuration** — YAML/JSON configuration for reproducible workflows.
- 🔄 **Integration with FloodPROOFS Chain** — serves as input engine for HMC (model) and HAT (analysis).
- 🧠 **Modular Architecture** — easy to extend with new drivers and plugins.
- 📊 **Event-based and Continuous Mode** — process both historical archives and real-time feeds.

---

## 🧱 Repository Structure

```
fp-hyde/
│
├── app/                # Main application scripts (processing routines)
├── bin/                # Command-line tools and launcher scripts
├── docs/               # Documentation and manuals
├── tools/              # Utility modules and support functions
├── examples/           # Example configurations and demo data
└── README.md           # This file
```

---

## 🚀 Installation

### Prerequisites

- **Operating System**: Linux (Debian/Ubuntu recommended)
- **Python**: 3.8 or newer  
- **Additional tools**:  
  - Fortran 2003+ (optional, for linked model components)  
  - QGIS ≥ 2.18  
  - R ≥ 3.4.4 (for downstream analysis modules)
  - Libraries: `netCDF4`, `h5py`, `numpy`, `pandas`, `gdal`, `matplotlib`, `scipy`, etc.

### Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/c-hydro/fp-hyde.git
   cd fp-hyde
   ```

2. (Optional but recommended) Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables (paths, data directories, etc.) as described in the `docs/` folder.

---## ▶️ How to run applications

Execution examples are provided as shell wrappers inside the repository (under `app/app_map/...`).  
Use these scripts as the **source of truth** for invocation, arguments, and environment handling.

For instance:
- **ECMWF 0.1° NWP**: [app_nwp_ecmwf_0100.sh](https://github.com/c-hydro/fp-hyde/blob/main/app/app_map/nwp/ecmwf/app_nwp_ecmwf_0100.sh)

Explore adjacent folders for other models and data types (e.g., ICON, LAMI-2i, observations). The scripts document the expected configuration files and runtime options for each application.

## 🧠 Integration within FloodPROOFS
HyDE is the **data layer** of the FloodPROOFS ecosystem:
1. **HyDE** – data acquisition, harmonization, and preprocessing  
2. **HMC** – distributed hydrological model  
3. **HAT** – analysis and visualization toolkit  

Together, these components enable operational flood forecasting, impact assessment, and risk-management services.

---

## 🧪 Example Applications

- Real-time flood forecasting for regional protection agencies  
- Seasonal hydrological analysis and drought assessment  
- Validation and quality control of meteorological datasets  
- Event reanalysis and hydrological benchmarking  

---

## 🤝 Contributing

Contributions are welcome!  
Please:
1. Fork the repository  
2. Create a feature branch (`git checkout -b feature/my-feature`)  
3. Commit your changes  
4. Open a pull request  

Check the `CONTRIBUTING.md` (if available) or contact the maintainers for more details.

---

## 🧾 License

Distributed under the **European Union Public Licence (EUPL 1.2)**.  
See the [LICENSE](LICENSE) file for details.

---

## 📚 References

- [FloodPROOFS Framework](https://github.com/c-hydro)
- [Hydrological Model Continuum (HMC)](https://github.com/c-hydro/hmc-model)
- [Hydrological Analysis Tools (HAT)](https://github.com/c-hydro/fp-hat)

---

## 🧩 Maintainers

**CIMA Research Foundation**  
📍 Savona, Italy  
🌐 [https://www.cimafoundation.org](https://www.cimafoundation.org)  
✉️ info@cimafoundation.org  

---

_Developed and maintained under the c-hydro initiative to support open and reproducible hydrological forecasting._
