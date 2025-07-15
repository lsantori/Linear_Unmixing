# Mineral Spectra Analyzer

A Python desktop application for spectral unmixing analysis of mineral samples using linear spectral unmixing algorithms.

## Features

- **Spectral Unmixing Algorithms**: Weighted Least Squares (WLS) and Sum-to-One (STO)
- **Modern GUI**: Built with ttkbootstrap for a modern themed interface
- **Data Management**: Import and preprocess CSV/Excel spectral data
- **Interactive Visualization**: Real-time spectral plotting and comparison
- **Results Analysis**: Comprehensive analysis with fit quality metrics
- **Export Functionality**: Save results and individual plots in multiple formats

## Screenshots

The application provides:
- Data import and management interface
- Interactive spectral analysis tools
- Detailed results visualization with individual plot saving
- Modern themed user interface

## Requirements

- Python 3.7+
- pandas
- numpy
- scipy
- ttkbootstrap
- matplotlib

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/mineral-spectra-analyzer.git
cd mineral-spectra-analyzer
```

2. Install required packages:
```bash
pip install pandas numpy scipy ttkbootstrap matplotlib
```

3. Run the application:
```bash
python main.py
```

## Usage

1. **Import Data**: Use the Data tab to import your spectral files (CSV or Excel)
2. **Select Spectra**: Choose end-member and mixed spectra for analysis
3. **Run Analysis**: Select algorithm (WLS or STO) and run spectral unmixing
4. **View Results**: Examine fitted spectra, residuals, and mineral abundances
5. **Export**: Save individual plots and comprehensive results

## Data Format

The application expects spectral data with columns:
- Wavenumber (cm⁻¹)
- Emissivity
- Uncertainty (optional)

## Project Structure

```
├── main.py                 # Application entry point
├── core/
│   └── data_manager2.py    # Data processing and management
│   └── spectral_algorithms.py  # WLS and STO algorithms
├── ui/
│   ├── main_window.py      # Main application window
│   ├── data_tab.py         # Data management interface
│   ├── analysis_tab.py     # Analysis configuration
│   ├── results_tab.py      # Results visualization
│   └── settings_tab.py     # Application settings
└── spectral/               # Data directories
    ├── spectral_library/   # Preprocessed end-member spectra
    └── mixed_pre_processed/ # Preprocessed mixed spectra
```

## Algorithms

### Weighted Least Squares (WLS)
Solves: `Abundances = (E^T W E)^-1 E^T W M`
- Automatically removes negative abundances iteratively
- Suitable for most spectral unmixing applications

### Sum-to-One (STO)
- Constrained unmixing ensuring abundances sum to 1
- Also removes negative abundances iteratively
- Ideal for closed-system mineral compositions

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

Developed for mineral spectroscopy research and analysis.