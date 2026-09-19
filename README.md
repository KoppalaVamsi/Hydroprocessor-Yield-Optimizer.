# Hydroprocessor Yield Optimizer & Prescriptive Optimization Platform

An Advanced Process Control (APC) digital twin and prescriptive optimization engine for a **Hydroprocessor**. 

This platform bridges data-driven machine learning models with first-principles thermodynamic physics to deliver real-time predictions for the product yields & specifications while providing the set-point recommendations for blended diesel quality targets ($D95$ Distillation Cut Points and Flash Points).

---

## 🌟 Key Features

* **Hybrid Prediction Engine**: Combines multi-output Random Forest machine learning models with explicit rolling time lags ($T, T-1, T-2, T-3$) to capture unit dynamics for the last 3 hours & predicts the yield & product specifications for the next 3 hours.
* **First-Principles ASTM Blending Thermodynamics**:
  * **D95 Distillation Physics**: Volumetric Average Boiling Point ($VABP$) baseline calculations with non-linear tailing slope corrections and inter-component co-vaporization synergy.
  * **Flash Point Non-Ideality**: Vapor pressure Blending Index ($BI$) transformations derived from Clausius-Clapeyron / Antoine dynamics with binary activity interaction parameters.
* **3D Prescriptive What-If Optimizer**: Simulates set-point variations across the fractionator columns, and Kerosene-to-Diesel/ATF routing to identify optimal conditions & product diversions for achieving the desired blended diesel targets.
* **Interactive Streamlit Dashboard**: Real-time KPI summary, multi-timeframe forecasts ($T$ to $T+3$), performance auditing metrics ($RMSE$, $MAE$, $R^2$), and target set-point controls.

---

## 📁 Repository Structure

```text
├── app.py                                        # Streamlit web UI & interactive control dashboard
├── core_engine.py                                # ML model architecture, thermodynamic math & what-if optimizer
├── generate_dummy_data.py                        # Script to generate synthetic plant sensor datasets for testing
├── HP logo.png                                   # UI branding asset (Currently replaced with a place holder)
└── requirements.txt                              # Required Python library dependencies
```

### File Breakdown
* **`app.py`**: Controls the user interface, renders real-time prediction matrices, and executes interactive what-if scenarios.
* **`core_engine.py`**: The computational core. Trains and deploys Random Forest models, executes thermodynamic blend matrices, and runs the 3D grid search optimization algorithm.
* **`generate_dummy_data.py`**: Generates synthetic CSV data simulating live DCS stream inputs and lab measurements for demonstration purposes.
---

## 🔬 Physics & Thermodynamic Foundations

Unlike pure black-box AI models, the **Hybrid APC Matrix** enforces thermodynamic boundaries during stream blending:

### 1. ASTM D86 Distillation $D95$ Blending
Non-linear heavy-end tailing near $D95$ is calculated using the Volumetric Average Boiling Point ($VABP$) modified by a localized distillation curve slope $S$ and synergy factor.

### 2. Flash Point Non-Linearity
Liquid-phase flash points are transformed into linear thermodynamic Blending Indices ($BI$) to reflect non-additive equilibrium vapor pressures before temperature recovery.

---

## 🚀 Quickstart Guide

### 1. Prerequisites
Ensure you have Python 3.13+ installed on your system.

### 2. Clone the Repository
```bash
git clone https://github.com/KoppalaVamsi/Hydroprocessor-Digital-Twin.git 
cd Hydroprocessor-Digital-Twin
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Generate Synthetic Operating Data
Run the synthetic data generator to populate the required cached operational parameters and historical lab datasets:
```bash
python generate_dummy_data.py
```

### 5. Launch the Dashboard
Start the Streamlit application:
```bash
streamlit run app.py
```
---

## 🛠️ Usage Workflow

1. **Inference Mode**: Launching `app.py` automatically reads the live parameter cache, constructs rolling lag vectors, and generates yield/quality predictions for timeframes $T$, $T+1$, $T+2$, and $T+3$.
2. **Retrain Mode**: When the base / bulk data is renewed, this mode can be used to delete the old model & develop new models based on the renewed data.
3. **Auto Cycle**: The streamlit interface is designed to fetch & process the live data every 2 minutes & generate results. 
4. **Current Feed Rate & WABTs**: The interface also displays the live data from the DCS so that the viewer can match the results against the live data.
5. **Prescriptive Control**:
   * Navigate to the **What-If Optimization** panel in the UI.
   * Select a control target (`Blend_Diesel_D95`, `Blend_Diesel_Flash`, or `Dual Target`).
   * Enter desired target values (e.g., $D95 = 365.8\text{ }^\circ\text{C}$).
   * Execute the optimizer to view calculated set-point adjustments.

---

## Disclaimer

This repository is intended for educational, research, and software demonstration purposes. Any proprietary datasets, process values, operational limits, or production-specific information have been removed prior to publication.

The results may vary slightly because of the synthetic data.

---

## Author

Chemical Engineer specializing in refinery operations, process optimization, machine learning applications, and digital decision-support systems.

---

## License

This project is distributed under the MIT License.

Feel free to use, modify, and distribute the code in accordance with the license terms.
