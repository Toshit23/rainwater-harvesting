# Rainwater Harvesting Potential Estimation for Construction Sites

A modular Python system for estimating rainwater harvesting potential and comparing it against construction site water demand.

## Project Structure

`	ext
rainwater-harvesting/
│
├── api/                  # Member 2: Geocoding (Nominatim) & Weather (Open-Meteo)
│   ├── __init__.py
│   ├── location.py
│   ├── weather.py
│   └── api_utils.py
│
├── calculations/         # Member 3: Engineering Calculations Engine
│   ├── __init__.py       # Master function: calculate_project_result()
│   ├── rooftop_area.py   # Physical area = Total Image Area * (Rooftop % / 100)
│   ├── rainwater_yield.py# Yield (L) = Area (m²) * Rainfall (mm) * Runoff Coeff
│   ├── water_demand.py   # Concrete + Plaster + Curing water demand
│   ├── comparison.py     # Supply vs Demand -> SURPLUS / SHORTFALL / BALANCED
│   └── validation.py     # Input range & type safety
│
├── backend/              # Alias for calculations (for backwards compatibility)
│   └── __init__.py
│
├── tests/                # Automated unit & integration tests
│   ├── test_engineering_calculations.py
│   ├── test_location.py
│   ├── test_weather.py
│   └── test_integration.py
│
├── main.py               # Main CLI application (Interactive & Demo)
├── demo.py               # One-click demo script
└── requirements.txt      # Project dependencies
`

## Quick Start

### 1. Install Dependencies
`powershell
pip install -r requirements.txt
`

### 2. Run the Demo
`powershell
python demo.py
`

### 3. Run Interactively
`powershell
python main.py
`

### 4. Run All Automated Tests
`powershell
python -m pytest tests/ -v
`

## Core Engineering Formulas

1. **Rooftop Area**:
   \text{Area (m}^2\text{)} = \text{Image Physical Area} \times \frac{\text{Rooftop Coverage \%}}{100}

2. **Rainwater Yield**:
   \text{Yield (L)} = \text{Rooftop Area (m}^2\text{)} \times \text{Rainfall (mm)} \times \text{Runoff Coefficient}
   *(Based on \text{ mm of rain} \times 1\text{ m}^2 = 1\text{ Litre}$)*

3. **Construction Water Demand**:
   \text{Demand (L)} = (\text{Concrete Vol} \times 180) + (\text{Plaster Vol} \times 160) + ((\text{Concrete} + \text{Plaster}) \times 20 \times \text{Curing Days})

4. **Supply vs Demand**:
   \text{Difference} = \text{Harvested Rainwater} - \text{Construction Demand}
   \text{Status} \in \{\text{SURPLUS}, \text{SHORTFALL}, \text{BALANCED}\}
