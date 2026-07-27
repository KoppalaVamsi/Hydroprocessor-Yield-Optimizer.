#!/usr/bin/env python
# coding: utf-8

import sys
import pandas as pd
import numpy as np
import xlwings as xw
import joblib
import os
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import root_mean_squared_error, mean_absolute_error, r2_score
import warnings
from datetime import datetime
from tqdm import tqdm  

warnings.filterwarnings('ignore')

def run_optimization_pipeline(RUN_MODE="Retrain", status_placeholder=None):
    """
    Main execution engine. 
    status_placeholder allows us to send text updates directly to the Streamlit screen.
    """
    
    def ui_print(msg):
        """Helper to print to CMD terminal AND update the Streamlit UI."""
        print(msg)
        if status_placeholder:
            status_placeholder.markdown(f"⏳ **{msg}**")

    MODEL_STORAGE_FILE = "rf_production_models.pkl"

    # ==========================================
    # RICH CMD OUTPUT: START BANNERS
    # ==========================================
    cmd_timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    print(f"\n\n===============================================================")
    print(f" HYDROPROCESSOR OPTIMIZATION MATRIX CYCLE LAUNCHED AT: {cmd_timestamp}")
    print(f"===============================================================\n")
    
    print(f"====================================================")
    print(f" SYSTEM ARCHITECTURE INITIALIZED IN [{RUN_MODE.upper()}] MODE")
    print(f"====================================================")

    # ==========================================
    # STEP 1: LOAD REVISED CONFIG & DATA FILES
    # ==========================================
    ui_print("Loading data and config files...")
    file_path = "46 Parameters Last 4 hours Data Live Excel version.xlsx"
    
    def get_live_data_fresh(file_path):
        cache_file = "cached_live_parameters.csv"
        try:
            wb = xw.books["46 Parameters Last 4 hours Data Live Excel version.xlsx"]
            wb.app.calculate()
            df_live = wb.sheets['Sheet1'].range('A1').options(pd.DataFrame, expand='table', header=True).value
            ts_vals = [wb.sheets['Sheet1'].range(f'G{i}').value for i in range(1, 5)]
            df_live.loc['TIMESTAMP_ROW'] = ts_vals
            df_live.to_csv(cache_file)
            print("Live snapshot with timestamps cached to disk...")
            return df_live
        except Exception as e:
            if os.path.exists(cache_file):
                print("--> Excel unreachable, loading from cache...")
                return pd.read_csv(cache_file, index_col=0)
            else:
                return pd.read_excel(file_path, index_col=0)

    df_dcs_bulk = pd.read_csv("Bulk_Data_DCS 47 Parameters against Time.csv")
    df_lab_bulk = pd.read_csv("Bulk_Data_Lab 18 Parameters against Time.csv")
    df_live_input = get_live_data_fresh("46 Parameters Last 4 hours Data Live Excel version.xlsx")
    df_live_input.index = df_live_input.index.astype(str).str.strip()
    df_corr = pd.read_csv("55 Total Parameters Correlations with 9 Target Parameters.csv", index_col=0)
    
    df_corr.index = df_corr.index.str.strip()
    df_corr.columns = df_corr.columns.str.strip()

    try:
        df_template = pd.read_csv("11 Target Parameters Next 3 hours Prediction.csv")
        display_order = df_template.iloc[:, 0].str.strip().tolist()
    except Exception:
        print("WARNING: '11 Target Parameters Next 3 hours Prediction.csv' missing. Activating self-healing fallback order.")
        ml_targets_fallback = [str(c).strip() for c in df_corr.columns]
        display_order = ml_targets_fallback + ['Blend_Diesel_D95', 'Blend_Diesel_Flash']

    if 'Blend_Diesel_Yield' not in display_order:
        display_order.append('Blend_Diesel_Yield')

    Blend_group = ['Blend_Diesel_Yield', 'Blend_Diesel_D95', 'Blend_Diesel_Flash']
    product_group = ['Product_Diesel_Yield', 'Product_Diesel_D95', 'Product_Diesel_Flash']

    for item in Blend_group:
        if item in display_order:
            display_order.remove(item)

    insert_idx = len(display_order)
    for p_item in product_group:
        if p_item in display_order:
            insert_idx = min(insert_idx, display_order.index(p_item))
            break

    for item in reversed(Blend_group):
        display_order.insert(insert_idx, item)

    for col in df_dcs_bulk.columns:
        if col != 'Time':
            df_dcs_bulk[col] = pd.to_numeric(df_dcs_bulk[col], errors='coerce')
    df_dcs_bulk = df_dcs_bulk.ffill().bfill()

    df_dcs_bulk['Time'] = pd.to_datetime(df_dcs_bulk['Time'], dayfirst=True)
    df_lab_bulk['Sample_collection_Date_and_Time'] = pd.to_datetime(df_lab_bulk['Sample_collection_Date_and_Time'], dayfirst=True)
    df_lab_bulk = df_lab_bulk.rename(columns={'Sample_collection_Date_and_Time': 'Time', 'Kero Flash': 'Kerosene_Flash'})

    # Removed the 5 engineered parameters from the authorized list
    live_base_set = set(df_live_input.index.astype(str).str.strip().tolist())
    authorized_live_base = live_base_set

    # ==========================================
    # STEP 2: DATA AUDIT & DEVIANT STREAM TRANSFER
    # ==========================================
    ui_print("Executing Experimental Data Audit & Route Patch...")
    if 'Blend_Diesel_D95' not in df_lab_bulk.columns:
        df_lab_bulk['Blend_Diesel_D95'] = np.nan
    if 'Blend_Diesel_Flash' not in df_lab_bulk.columns:
        df_lab_bulk['Blend_Diesel_Flash'] = np.nan

    for col in ['Product_Diesel_D95', 'Product_Diesel_Flash', 'Blend_Diesel_D95', 'Blend_Diesel_Flash']:
        if col in df_lab_bulk.columns:
            df_lab_bulk[col] = pd.to_numeric(df_lab_bulk[col], errors='coerce')

    df_lab_bulk = df_lab_bulk.sort_values('Time')

    mislabeled_mask = df_lab_bulk['Product_Diesel_Flash'] < 90.0
    print(f"Data Audit: Masked {mislabeled_mask.sum()} contaminated rows from Diesel modeling...")

    df_lab_bulk.loc[mislabeled_mask, 'Blend_Diesel_D95'] = df_lab_bulk.loc[mislabeled_mask, 'Product_Diesel_D95']
    df_lab_bulk.loc[mislabeled_mask, 'Blend_Diesel_Flash'] = df_lab_bulk.loc[mislabeled_mask, 'Product_Diesel_Flash']

    df_lab_bulk.loc[mislabeled_mask, 'Product_Diesel_D95'] = np.nan
    df_lab_bulk.loc[mislabeled_mask, 'Product_Diesel_Flash'] = np.nan

    # ==========================================
    # STEP 3: TIME-LAGGED MATRIX & DUAL ALIGNMENT
    # ==========================================
    ui_print("Constructing explicit time lags...")

    df_dcs_bulk = df_dcs_bulk.sort_values('Time')
    dcs_base_cols = [c for c in df_dcs_bulk.columns if c != 'Time']

    columns_to_lag = dcs_base_cols
    lagged_features_list = []

    for lag in [1, 2, 3]:
        for col in columns_to_lag:
            lag_col_name = f"{col}_T-{lag}"
            df_dcs_bulk[lag_col_name] = df_dcs_bulk[col].shift(lag)
            lagged_features_list.append(lag_col_name)

    df_dcs_bulk = df_dcs_bulk.dropna(subset=lagged_features_list)

    lab_targets = [c for c in df_lab_bulk.columns if c != 'Time']
    df_lab_clean_ffill = df_lab_bulk.copy()
    df_lab_clean_ffill[lab_targets] = df_lab_clean_ffill[lab_targets].ffill().fillna(df_lab_clean_ffill[lab_targets].mean())
    df_dcs_centric = pd.merge_asof(df_dcs_bulk.sort_values('Time'), df_lab_clean_ffill.sort_values('Time'), on='Time', direction='backward')
    df_lab_centric = pd.merge_asof(df_lab_bulk.sort_values('Time'), df_dcs_bulk.sort_values('Time'), on='Time', direction='backward')

    ml_targets = [t for t in display_order if "Blend_Diesel" not in t]
    excluded_from_features = display_order + ['Time', 'Catalyst_Age_in_hours']

    # ==========================================
    # STEP 4: TUNED RANDOM FOREST PIPELINE
    # ==========================================
    models_dict = {}
    metrics_summary = []
    drivers_summary = {}

    if RUN_MODE == "Inference" and os.path.exists(MODEL_STORAGE_FILE):
        ui_print("Mode: Inference. Loading optimized weights from disk silently...")
        saved_payload = joblib.load(MODEL_STORAGE_FILE)
        models_dict = saved_payload['models']
        metrics_summary = saved_payload['metrics']
        drivers_summary = saved_payload['drivers']
        print("Pre-trained binary weights deployed successfully...")
    else:
        if RUN_MODE == "Inference":
            ui_print(f"--> ALERT: {MODEL_STORAGE_FILE} not found! Forcing [Retrain] to compile weights.")
        else:
            ui_print("Mode: Retrain. Executing full multi-variable Random Forest compilation...")
        
        for target in ml_targets:
            print(f"Compiling Model [{target}]")

            base_features = []
            if target in df_corr.columns:
                potential_base_features = df_corr.index[df_corr[target] == 'Yes'].tolist()
                base_features = [f for f in potential_base_features if f in df_dcs_bulk.columns]

            raw_features = []
            if base_features:
                for f in base_features:
                    raw_features.append(f)
                    for lag in [1, 2, 3]:
                        lag_f = f"{f}_T-{lag}"
                        if lag_f in df_dcs_bulk.columns:
                            raw_features.append(lag_f)
            else:
                raw_features = [c for c in df_dcs_bulk.columns if c not in excluded_from_features]

            features = []
            for f in raw_features:
                base_f = f
                for lag_suffix in ['_T-1', '_T-2', '_T-3']:
                    if f.endswith(lag_suffix):
                        base_f = f.replace(lag_suffix, '')
                        break
                if base_f in authorized_live_base and base_f not in excluded_from_features:
                    features.append(f)

            features = list(set(features))

            if any(suffix in target for suffix in ['D95', 'Flash', 'FBP']):
                df_target_train = df_lab_centric.dropna(subset=[target] + features)
                max_depth_tune = 6  
            else:
                df_target_train = df_dcs_centric.dropna(subset=[target] + features)
                max_depth_tune = 8  

            if len(df_target_train) < 5:
                df_target_train = df_dcs_centric.dropna(subset=[target] + features)

            X = df_target_train[features]
            y = df_target_train[target]

            rf = RandomForestRegressor(n_estimators=100, max_depth=max_depth_tune, max_features='sqrt', random_state=42, n_jobs=-1)
            rf.fit(X, y)
            models_dict[target] = (rf, features)

            y_pred = rf.predict(X)
            metrics_summary.append({
                'Target': target, 
                'RMSE': round(root_mean_squared_error(y, y_pred), 3), 
                'MAE': round(mean_absolute_error(y, y_pred), 3), 
                'R2': round(r2_score(y, y_pred), 2)
            })

            importances = rf.feature_importances_
            indices = np.argsort(importances)[::-1][:5]
            drivers_summary[target] = ", ".join([f"{features[i]} ({importances[i]*100:.1f}%)" for i in indices])

        for comb_target in ['Blend_Diesel_D95', 'Blend_Diesel_Flash', 'Blend_Diesel_Yield']:
            metrics_summary.append({'Target': comb_target, 'RMSE': 'Physics', 'MAE': 'Physics', 'R2': 'Calculated'})
            drivers_summary[comb_target] = "Thermodynamic Mass & Blend Balance Model"

        payload_to_save = {
            'models': models_dict,
            'metrics': metrics_summary,
            'drivers': drivers_summary
        }
        joblib.dump(payload_to_save, MODEL_STORAGE_FILE)
        
        ui_print(f"--> Success: Model states compiled and preserved to {MODEL_STORAGE_FILE}")

    # ==========================================
    # STEP 5: LIVE CASCADING INFERENCE ENGINE
    # ==========================================
    ui_print("Processing Live Predict Data with Rolling Lags...")
    df_live_input = df_live_input.reset_index()
    df_live_input.rename(columns={df_live_input.columns[0]: 'Parameter'}, inplace=True)

    core_columns = ['Parameter'] + list(df_live_input.columns[1:5])
    df_live_input = df_live_input[core_columns]
    df_live_input.columns = ['Parameter', 'T-3', 'T-2', 'T-1', 'T']
    df_live_input = df_live_input.set_index('Parameter').T

    for col in df_live_input.columns:
        df_live_input[col] = pd.to_numeric(df_live_input[col], errors='coerce')
    df_live_input = df_live_input.ffill().bfill()

    horizons = ['T', 'T+1', 'T+2', 'T+3']
    live_vectors = {}
    base_live_cols = list(df_live_input.columns)

    v_T = df_live_input.iloc[-1].to_dict()
    for col in base_live_cols:
        v_T[f"{col}_T-1"] = df_live_input[col].iloc[-2]
        v_T[f"{col}_T-2"] = df_live_input[col].iloc[-3]
        v_T[f"{col}_T-3"] = df_live_input[col].iloc[-4]
    live_vectors['T'] = v_T

    v_T1 = df_live_input.iloc[-1].to_dict()
    for col in base_live_cols:
        v_T1[f"{col}_T-1"] = df_live_input[col].iloc[-1]
        v_T1[f"{col}_T-2"] = df_live_input[col].iloc[-2]
        v_T1[f"{col}_T-3"] = df_live_input[col].iloc[-3]
    live_vectors['T+1'] = v_T1

    v_T2 = df_live_input.iloc[-1].to_dict()
    for col in base_live_cols:
        v_T2[f"{col}_T-1"] = df_live_input[col].iloc[-1]
        v_T2[f"{col}_T-2"] = df_live_input[col].iloc[-1]
        v_T2[f"{col}_T-3"] = df_live_input[col].iloc[-2]
    live_vectors['T+2'] = v_T2

    v_T3 = df_live_input.iloc[-1].to_dict()
    for col in base_live_cols:
        v_T3[f"{col}_T-1"] = df_live_input[col].iloc[-1]
        v_T3[f"{col}_T-2"] = df_live_input[col].iloc[-1]
        v_T3[f"{col}_T-3"] = df_live_input[col].iloc[-1]
    live_vectors['T+3'] = v_T3

    predictions_table = {t: [] for t in display_order}

    for target in ml_targets:
        rf_model, feat_list = models_dict[target]
        for step_name in horizons:
            df_step_vector = pd.DataFrame([live_vectors[step_name]])
            X_live = df_step_vector[feat_list]
            pred_val = rf_model.predict(X_live)[0]
            predictions_table[target].append(pred_val)

    # ==========================================
    # STEP 6: ADVANCED ASTM SLOPES BLEND ENGINE
    # ==========================================
    ui_print("Running Rigorous ASTM Fractional Curve Blend Matrix...")

    try:
        p_d50_base = pd.to_numeric(df_lab_bulk['Product_Diesel_D50'], errors='coerce').mean()
        p_d90_base = pd.to_numeric(df_lab_bulk['Product_Diesel_D90'], errors='coerce').mean()
        p_d95_base = pd.to_numeric(df_lab_bulk['Product_Diesel_D95'], errors='coerce').mean()

        k_d50_base = pd.to_numeric(df_lab_bulk['Kero_D50'], errors='coerce').mean()
        k_d90_base = pd.to_numeric(df_lab_bulk['Kero_D90'], errors='coerce').mean()
        k_d95_base = pd.to_numeric(df_lab_bulk['Kerosene_D95'], errors='coerce').mean()

        p_delta_50 = p_d95_base - p_d50_base
        p_delta_90 = p_d95_base - p_d90_base
        k_delta_50 = k_d95_base - k_d50_base
        k_delta_90 = k_d95_base - k_d90_base
    except Exception:
        p_delta_50, p_delta_90 = 82.5, 9.8
        k_delta_50, k_delta_90 = 41.5, 6.5

    for i, step_name in enumerate(horizons):
        p_yield = predictions_table['Product_Diesel_Yield'][i]
        k_to_diesel = live_vectors[step_name].get('Kerosene_to_Diesel', predictions_table['Kerosene_Yield'][i])
        k_yield_for_blend = k_to_diesel

        p_d95 = predictions_table['Product_Diesel_D95'][i]
        k_d95 = predictions_table['Kerosene_D95'][i]

        p_flash = predictions_table['Product_Diesel_Flash'][i]
        k_flash = predictions_table['Kerosene_Flash'][i]

        total_flow = p_yield + k_yield_for_blend + 1e-5
        vol_frac_p = p_yield / total_flow
        vol_frac_k = k_yield_for_blend / total_flow

        p_d50_curr = p_d95 - p_delta_50
        p_d90_curr = p_d95 - p_delta_90

        k_d50_curr = k_d95 - k_delta_50
        k_d90_curr = k_d95 - k_delta_90

        vabp_d50 = (vol_frac_p * p_d50_curr) + (vol_frac_k * k_d50_curr)
        vabp_d90 = (vol_frac_p * p_d90_curr) + (vol_frac_k * k_d90_curr)
        vabp_d95 = (vol_frac_p * p_d95) + (vol_frac_k * k_d95)

        blend_slope = (vabp_d90 - vabp_d50) / 40.0
        tailing_factor = blend_slope * (p_d95 - vabp_d95) * 0.65
        
        d95_interaction_alpha = 1.5
        d95_blend_synergy = d95_interaction_alpha * vol_frac_p * vol_frac_k
        
        calculated_comb_d95 = vabp_d95 + tailing_factor + d95_blend_synergy
        calculated_comb_d95 = max(vabp_d95, min(calculated_comb_d95, p_d95 - 4.5))
        
        predictions_table['Blend_Diesel_D95'].append(calculated_comb_d95)
        predictions_table['Blend_Diesel_Yield'].append(total_flow)
        
        # ==========================================
        # FLASH BLENDING WITH INTERACTION TERM
        # ==========================================
        bi_flash_p = np.exp(-4.25 + (1250.0 / (p_flash + 273.15)))
        bi_flash_k = np.exp(-4.25 + (1250.0 / (k_flash + 273.15)))
        
        flash_interaction_alpha = 0.4  
        blend_synergy = flash_interaction_alpha * vol_frac_p * vol_frac_k
        bi_flash_comb = (vol_frac_p * bi_flash_p) + (vol_frac_k * bi_flash_k) + blend_synergy

        bi_flash_comb = max(1e-8, bi_flash_comb)

        calculated_comb_flash = (1250.0 / (np.log(bi_flash_comb) + 4.25)) - 273.15
        predictions_table['Blend_Diesel_Flash'].append(calculated_comb_flash)

    # ==========================================
    # STEP 7: GENERATE RE-ALIGNED TABLES
    # ==========================================
    existing_metrics_targets = [m['Target'] for m in metrics_summary] if isinstance(metrics_summary, list) else []
    for comb_target in ['Blend_Diesel_D95', 'Blend_Diesel_Flash', 'Blend_Diesel_Yield']:
        if comb_target not in existing_metrics_targets:
            metrics_summary.append({'Target': comb_target, 'RMSE': 'Physics', 'MAE': 'Physics', 'R2': 'Calculated'})
        drivers_summary[comb_target] = "Thermodynamic Mass & Blend Balance Model"

    df_metrics_out = pd.DataFrame(metrics_summary).set_index('Target')
    df_drivers_out = pd.DataFrame.from_dict(drivers_summary, orient='index', columns=['Top 5 Drivers']).reindex(display_order)
    df_preds_out = pd.DataFrame.from_dict(predictions_table, orient='index', columns=horizons).reindex(display_order)

    df_Blend_out = df_preds_out.join(df_metrics_out)

    # RESTORED: RICH CMD TABLE PRINT
    print("\n" + "="*80)
    print("TABLE 1: LIVE PREDICTION RESULTS & MODEL PERFORMANCE")
    print("="*80)
    print(df_Blend_out.round(3).to_string())

    # ==========================================
    # STEP 8: AUTOMATED EXPORT ENGINE
    # ==========================================
    df_preds_out.round(3).to_csv("11 Target Parameters Next 3 hours Prediction.csv", index_label="Target")
    df_drivers_out.to_csv("Process_Drivers_Interpretability_Profile.csv")
    df_Blend_out.round(3).to_csv("Consolidated_Predictions_And_Validation_Report.csv")
    
    # RESTORED: Final CMD completion message
    print("\nOutput Loop Complete: Updated hybrid matrices saved to disk...\n")
    
    return True

# ==============================================================================
# NEW PRESCRIPTIVE OPTIMIZATION ENGINE (WHAT-IF SCENARIOS)
# ==============================================================================
def run_what_if_optimization(target_mode, desired_d95, desired_flash):
    """
    3D Grid Search Simulator. Predicts the best moves for FZT, DOT, and Kero Routing.
    Enforces strict physical boundaries: Temperatures only affect base Product Diesel via ML. 
    Routing only affects final Blend Blend math.
    """
    MODEL_STORAGE_FILE = "rf_production_models.pkl"
    try:
        saved_payload = joblib.load(MODEL_STORAGE_FILE)
        models_dict = saved_payload['models']
    except Exception as e:
        return {"error": "Models not found. Let the main cycle run once to compile models."}

    cache_file = "cached_live_parameters.csv"
    if not os.path.exists(cache_file):
        return {"error": "Live data cache missing. Awaiting data streams..."}
    
    df_live = pd.read_csv(cache_file, index_col=0)
    df_live.index = df_live.index.astype(str).str.strip()
    
    try:
        # Get Current States
        curr_fzt = float(df_live.loc['Diesel_Flash_Zone_Temperature', 'T'])
        curr_dot = float(df_live.loc['Diesel_Draw-Off_Temperature', 'T'])
        curr_k2d = float(df_live.loc['Kerosene_to_Diesel', 'T'])
        
        # Fallback for Kerosene_to_ATF
        if 'Kerosene_to_ATF' in df_live.index:
            curr_k2atf = float(df_live.loc['Kerosene_to_ATF', 'T'])
        else:
            curr_k2atf = 10.0 # Arbitrary fallback if missing
            
        total_kero = curr_k2d + curr_k2atf
    except Exception as e:
        return {"error": f"Missing critical sensors in live feed: {e}"}

    # 1. Build Valid Temperature Grid
    valid_temps = []
    if "D95" in target_mode:
        # You can expand this ± range if you need more flexibility (e.g. -5.0 to 5.5)
        for f in np.arange(-20.0, 20.5, 0.5):
            for d in np.arange(-20.0, 20.5, 0.5):
                if (f * d >= 0): # Must move in same direction
                    valid_temps.append((f, d))
    else:
        valid_temps.append((0.0, 0.0))

    # 2. Build Valid Routing Grid
    if "Flash" in target_mode:
        k2d_options = np.linspace(0.1, total_kero, 100) # 21 steps of routing
    else:
        k2d_options = [curr_k2d]

    # 3. Create the 3D Master Grid
    scenarios = []
    for (dfzt, ddot) in valid_temps:
        for new_k2d in k2d_options:
            new_k2atf = total_kero - new_k2d
            scenarios.append({
                'delta_fzt': dfzt, 'new_fzt': curr_fzt + dfzt,
                'delta_dot': ddot, 'new_dot': curr_dot + ddot,
                'delta_k2d': new_k2d - curr_k2d, 'new_k2d': new_k2d,
                'delta_k2atf': new_k2atf - curr_k2atf, 'new_k2atf': new_k2atf
            })
            
    df_scenarios = pd.DataFrame(scenarios)
    num_scenarios = len(df_scenarios)

    # 4. Build Vectorized Live Feature Matrix
    base_vector = {}
    for col in df_live.index:
        if col != 'TIMESTAMP_ROW':
            # FIX: We now pull the EXACT historical values for the lags, preserving plant dynamics
            base_vector[col] = float(df_live.loc[col, 'T'])
            base_vector[f"{col}_T-1"] = float(df_live.loc[col, 'T-1'])
            base_vector[f"{col}_T-2"] = float(df_live.loc[col, 'T-2'])
            base_vector[f"{col}_T-3"] = float(df_live.loc[col, 'T-3'])

    df_X = pd.DataFrame([base_vector] * num_scenarios)

    # STRICT PHYSICS ENFORCEMENT: Apply the DELTA to the historical baseline 
    # to simulate a set-point shift, rather than overwriting history.
    for t_step in ['', '_T-1', '_T-2', '_T-3']:
        df_X[f'Diesel_Flash_Zone_Temperature{t_step}'] += df_scenarios['delta_fzt'].values
        df_X[f'Diesel_Draw-Off_Temperature{t_step}'] += df_scenarios['delta_dot'].values

    # 5. Run ML Predictions with Separation of Logic
    preds = {}
    
    # 5A. Predict Product Diesel (affected by Temperatures)
    for t in ['Product_Diesel_D95', 'Product_Diesel_Flash', 'Product_Diesel_Yield']:
        if t in models_dict:
            rf_model, feat_list = models_dict[t]
            missing_cols = [c for c in feat_list if c not in df_X.columns]
            for mc in missing_cols: df_X[mc] = 0
            preds[t] = rf_model.predict(df_X[feat_list])
        else:
            preds[t] = np.full(num_scenarios, 0.0)

    # 5B. Lock Kerosene Predictions (Independent from Vac Column FZT/DOT)
    df_baseline_single = pd.DataFrame([base_vector])
    for t in ['Kerosene_D95', 'Kerosene_Flash', 'Kerosene_Yield']:
        if t in models_dict:
            rf_model, feat_list = models_dict[t]
            missing_cols = [c for c in feat_list if c not in df_baseline_single.columns]
            for mc in missing_cols: df_baseline_single[mc] = 0
            # Predict once and copy it N times
            base_val = rf_model.predict(df_baseline_single[feat_list])[0]
            preds[t] = np.full(num_scenarios, base_val)
        else:
            preds[t] = np.full(num_scenarios, 0.0)

    # 6. Run Vectorized Thermodynamic ASTM Blending
    p_yield = preds['Product_Diesel_Yield']
    k_to_diesel = df_scenarios['new_k2d'].values
    p_d95 = preds['Product_Diesel_D95']
    k_d95 = preds['Kerosene_D95']
    p_flash = preds['Product_Diesel_Flash']
    k_flash = preds['Kerosene_Flash']

    total_flow = p_yield + k_to_diesel + 1e-5
    vol_frac_p = p_yield / total_flow
    vol_frac_k = k_to_diesel / total_flow

    # FIX: Load the EXACT live laboratory constants, rather than hardcoding fallbacks
    try:
        df_lab_bulk = pd.read_csv("Bulk_Data_Lab 18 Parameters against Time.csv")
        p_d50_base = pd.to_numeric(df_lab_bulk['Product_Diesel_D50'], errors='coerce').mean()
        p_d90_base = pd.to_numeric(df_lab_bulk['Product_Diesel_D90'], errors='coerce').mean()
        p_d95_base = pd.to_numeric(df_lab_bulk['Product_Diesel_D95'], errors='coerce').mean()

        k_d50_base = pd.to_numeric(df_lab_bulk['Kero_D50'], errors='coerce').mean()
        k_d90_base = pd.to_numeric(df_lab_bulk['Kero_D90'], errors='coerce').mean()
        k_d95_base = pd.to_numeric(df_lab_bulk['Kerosene_D95'], errors='coerce').mean()

        p_delta_50 = p_d95_base - p_d50_base
        p_delta_90 = p_d95_base - p_d90_base
        k_delta_50 = k_d95_base - k_d50_base
        k_delta_90 = k_d95_base - k_d90_base
    except Exception:
        # Only use these if the lab file is completely missing
        p_delta_50, p_delta_90 = 82.5, 9.8
        k_delta_50, k_delta_90 = 41.5, 6.5

    vabp_d50 = (vol_frac_p * (p_d95 - p_delta_50)) + (vol_frac_k * (k_d95 - k_delta_50))
    vabp_d90 = (vol_frac_p * (p_d95 - p_delta_90)) + (vol_frac_k * (k_d95 - k_delta_90))
    vabp_d95 = (vol_frac_p * p_d95) + (vol_frac_k * k_d95)

    blend_slope = (vabp_d90 - vabp_d50) / 40.0
    tailing_factor = blend_slope * (p_d95 - vabp_d95) * 0.65
    d95_blend_synergy = 1.5 * vol_frac_p * vol_frac_k
    
    # Vectorized D95
    calc_d95 = np.maximum(vabp_d95, np.minimum(vabp_d95 + tailing_factor + d95_blend_synergy, p_d95 - 4.5))
    
    # Vectorized Flash
    bi_flash_p = np.exp(-4.25 + (1250.0 / (p_flash + 273.15)))
    bi_flash_k = np.exp(-4.25 + (1250.0 / (k_flash + 273.15)))
    bi_flash_comb = np.maximum(1e-8, (vol_frac_p * bi_flash_p) + (vol_frac_k * bi_flash_k) + (0.4 * vol_frac_p * vol_frac_k))
    calc_flash = (1250.0 / (np.log(bi_flash_comb) + 4.25)) - 273.15

    # 7. Calculate Errors and Find Best Scenario
    if target_mode == "Blend_Diesel_D95":
        errors = np.abs(calc_d95 - desired_d95)
    elif target_mode == "Blend_Diesel_Flash":
        errors = np.abs(calc_flash - desired_flash)
    else: 
        err_d95 = ((calc_d95 - desired_d95) / 360.0) ** 2
        err_flash = ((calc_flash - desired_flash) / 65.0) ** 2
        errors = err_d95 + err_flash

    best_idx = np.argmin(errors)
    best_scenario = df_scenarios.iloc[best_idx].to_dict()
    
    limit_reached = False
    if target_mode == "Blend_Diesel_D95" and errors[best_idx] > 0.5: limit_reached = True
    if target_mode == "Blend_Diesel_Flash" and errors[best_idx] > 0.5: limit_reached = True
    if target_mode == "Blend_Diesel_D95 & Blend_Diesel_Flash" and (np.abs(calc_d95[best_idx]-desired_d95) > 0.5 or np.abs(calc_flash[best_idx]-desired_flash) > 0.5):
        limit_reached = True

    return {
        "success": True,
        "mode": target_mode,
        "limit_reached": limit_reached,
        "actions": best_scenario,
        "results": {
            "d95": calc_d95[best_idx],
            "flash": calc_flash[best_idx],
            "yield": total_flow[best_idx]
        }
    }