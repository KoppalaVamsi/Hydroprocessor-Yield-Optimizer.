import streamlit as st
import xlwings as xw
import pandas as pd
import numpy as np
import os
import sys
import time
from datetime import datetime, timedelta

st.logo(
    image="HP Logo.png",
    size="Large",  # Options: "small" (20px), "medium" (24px), "large" (32px)
    link="https://www.hindustanpetroleum.com/" # Optional redirection link on click
)

# Import our backend engine directly into memory (NO SUBPROCESS NEEDED!)
from core_engine import run_optimization_pipeline

def get_saved_cycle_rate():
    """Reads the cycle rate from config.csv on disk, defaults to 2 if missing."""
    try:
        if os.path.exists("config.csv"):
            df_cfg = pd.read_csv("config.csv", index_col=0)
            if "Cycle_Rate" in df_cfg.index:
                return int(df_cfg.loc["Cycle_Rate", "Value"])
    except Exception:
        pass
    return 2  

def save_cycle_rate(minutes):
    """Saves the chosen cycle rate directly to config.csv so it survives Chrome updates."""
    try:
        if os.path.exists("config.csv"):
            df_cfg = pd.read_csv("config.csv", index_col=0)
        else:
            df_cfg = pd.DataFrame(columns=["Value"])
        
        df_cfg.loc["Cycle_Rate"] = [str(minutes)]
        df_cfg.to_csv("config.csv", index_label="Parameter")
    except Exception as e:
        st.error(f"Failed to update config.csv matrix: {e}")

# 1. Page Configuration & Styling (Wide Layout)
st.set_page_config(page_title="Hydroprocessor Optimization Engine", layout="wide")

# 🌟 UNIFORM COMPACT LAYOUT ENGINE (CSS OVERRIDES)
st.markdown("""
    <style>
    .block-container {
        padding-top: 2.3rem !important;
        padding-bottom: 1rem !important;
        padding-left: 3rem !important;
        padding-right: 3rem !important;
    }
    div[data-testid="stVerticalBlock"] {
        gap: 0.75rem !important;
    }
    hr {
        margin-top: 0.5rem !important;
        margin-bottom: 0.5rem !important;
        border-bottom: 1px solid rgba(49, 51, 63, 0.2);
    }
    h1 { margin-top: 0.25rem !important; margin-bottom: 0.25rem !important; padding-top: 0rem !important; padding-bottom: 0rem !important; }
    h2, h3, h4 { font-size: 1.25rem !important; font-weight: 600 !important; margin-top: 0.25rem !important; margin-bottom: 0.25rem !important; padding-top: 0rem !important; padding-bottom: 0rem !important; }
    h5, h6 { margin-top: 0.25rem !important; margin-bottom: 0.25rem !important; padding-top: 0rem !important; padding-bottom: 0rem !important; }
    .metric-box {
        background-color: var(--secondary-background-color); 
        color: var(--text-color); 
        padding: 16px 14px; 
        border-radius: 10px;
        border-left: 5px solid #0EA5E9; 
        text-align: center;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        min-height: 155px;
        box-sizing: border-box;
    }
    div[data-testid="stSelectbox"] > div { height: 42px !important; }
    div[data-testid="stButton"] > button { height: 42px !important; display: flex !important; align-items: center !important; justify-content: center !important; }
    div[data-testid="stCheckbox"], div[data-testid="stToggle"] { height: 42px !important; display: flex !important; align-items: center !important; }
    .stProgress > div > div > div > div { background-color: #0EA5E9 !important; }
    
    /* Blinking Operator Alerts (D95 Only) */
    @keyframes blink-red {
        0% { background-color: #450a0a; border: 1.5px solid #ef4444; box-shadow: 0 0 8px #ef4444; }
        50% { background-color: #200000; border: 1.5px solid #991b1b; box-shadow: 0 0 2px #991b1b; }
        100% { background-color: #450a0a; border: 1.5px solid #ef4444; box-shadow: 0 0 8px #ef4444; }
    }
    @keyframes blink-yellow {
        0% { background-color: #451a03; border: 1.5px solid #f59e0b; box-shadow: 0 0 8px #f59e0b; }
        50% { background-color: #200d00; border: 1.5px solid #b45309; box-shadow: 0 0 2px #b45309; }
        100% { background-color: #451a03; border: 1.5px solid #f59e0b; box-shadow: 0 0 8px #f59e0b; }
    }
    .alert-red { animation: blink-red 1.5s infinite; color: #fca5a5; padding: 6px 10px; border-radius: 6px; text-align: center; font-weight: bold; font-size: 13px; margin-top: 8px; width: 100%; box-sizing: border-box; }
    .alert-yellow { animation: blink-yellow 1.5s infinite; color: #fde68a; padding: 6px 10px; border-radius: 6px; text-align: center; font-weight: bold; font-size: 13px; margin-top: 8px; width: 100%; box-sizing: border-box; }
    .alert-green { background-color: #064E3B; color: #A7F3D0; border: 1.5px solid #10B981; padding: 6px 10px; border-radius: 6px; text-align: center; font-weight: bold; font-size: 13px; margin-top: 8px; width: 100%; box-sizing: border-box; }

    /* 🔴 Red Primary Action Button for 'Run Engine Matrices' */
    div[data-testid="stButton"] > button[aria-label*="Run Engine"] {
        background-color: #EF4444 !important;
        border-color: #DC2626 !important;
        color: #FFFFFF !important;
        font-weight: bold !important;
        font-size: 15px !important;
        box-shadow: 0 0 10px rgba(239, 68, 68, 0.4) !important;
    }
    div[data-testid="stButton"] > button[aria-label*="Run Engine"]:hover {
        background-color: #DC2626 !important;
        border-color: #B91C1C !important;
        color: #FFFFFF !important;
        box-shadow: 0 0 15px rgba(239, 68, 68, 0.6) !important;
    }

    /* 🟢 Green Primary Action Button for Prescriptive Engine ('ESTIMATE OPTIMAL MOVES') */
    div[data-testid="stButton"] > button[aria-label*="ESTIMATE"] {
        background-color: #10B981 !important;
        border-color: #059669 !important;
        color: #FFFFFF !important;
        font-weight: bold !important;
        font-size: 15px !important;
        box-shadow: 0 0 10px rgba(16, 185, 129, 0.3) !important;
    }
    div[data-testid="stButton"] > button[aria-label*="ESTIMATE"]:hover {
        background-color: #059669 !important;
        border-color: #047857 !important;
        color: #FFFFFF !important;
        box-shadow: 0 0 15px rgba(16, 185, 129, 0.5) !important;
    }

    div[data-testid="stCheckbox"] label p, 
    div[data-testid="stCheckbox"] label span {
        font-size: 14px !important;
        font-weight: 500 !important;
        color: #F1F5F9 !important;
    }
    div[data-testid="stNumberInput"] input {
        font-size: 14px !important;
        font-weight: 500 !important;
    }
""", unsafe_allow_html=True)

if "last_run" not in st.session_state:
    st.session_state.last_run = datetime.now() - timedelta(hours=1)

def find_historian_file():
    for f in os.listdir("."):
        if "46 Parameters" in f and f.endswith(".xlsx"):
            return f
    return None

# 2. Main Title Header
st.title("Hydroprocessor Live Optimization Engine⚡")
st.subheader("Hybrid Gray-Box Machine Learning & Thermodynamic Distillation Curve Model")
st.write("   ")

# ==========================================
# 3. CONTROL DOCK (OPTIMIZED HORIZONTAL COLUMNS)
# ==========================================
with st.container(border=True):
    col_ctrl1, col_ctrl2, col_ctrl3, col_ctrl4, col_ctrl5, col_timer1, col_timer2 = st.columns([2.3, 1.7, 1.6, 1.5, 1.3, 1.7, 2.3])
    
    with col_ctrl1:
        st.markdown("<p style='margin-bottom:4px; font-weight:bold; color:#94A3B8; font-size:12px; white-space:nowrap;'>⚙️ CONFIGURATION FRAMEWORK</p>", unsafe_allow_html=True)
        try:
            df_config = pd.read_csv("config.csv", index_col=0)
            current_mode = df_config.iloc[0, 0].strip()
            default_index = 0 if "Inference" in current_mode else 1
        except Exception:
            default_index = 0

        ui_mode = st.selectbox(
            "Select Pipeline Execution Mode:",
            options=["Inference (Live Deployment)", "Retrain (Model Optimization)"],
            index=default_index,
            label_visibility="collapsed"
        )
        backend_mode = "Inference" if "Inference" in ui_mode else "Retrain"
        
    with col_ctrl2:
        st.markdown("<p style='margin-bottom:4px; font-weight:bold; color:#94A3B8; font-size:12px; white-space:nowrap;'>🔔 ACTIVE SYSTEM STATUS</p>", unsafe_allow_html=True)
        if backend_mode == "Inference":
            status_html = '<div style="background-color: #064E3B; color: #A7F3D0; border: 1px solid #10B981; padding: 0px 14px; border-radius: 8px; height: 42px; display: flex; align-items: center; font-size: 13px; font-weight: 500; white-space:nowrap;">⚡ Cache Mode Active</div>'
        else:
            status_html = '<div style="background-color: #1E3A8A; color: #BFDBFE; border: 1px solid #3B82F6; padding: 0px 14px; border-radius: 8px; height: 42px; display: flex; align-items: center; font-size: 13px; font-weight: 500; white-space:nowrap;">🔄 Compilation Loop Active</div>'
        st.markdown(status_html, unsafe_allow_html=True)

    with col_ctrl3:
        st.markdown("<p style='margin-bottom:4px; font-weight:bold; color:#94A3B8; font-size:12px; white-space:nowrap;'>🚀 ENGINE EXECUTION</p>", unsafe_allow_html=True)
        trigger_manual = st.button("Run Engine Matrices", use_container_width=True, type="primary")

    with col_ctrl4:
        st.markdown("<p style='margin-bottom:4px; font-weight:bold; color:#94A3B8; font-size:12px; white-space:nowrap;'>⏱️ AUTOMATION</p>", unsafe_allow_html=True)
        auto_cycle = st.toggle("Auto-Cycle Loop", value=True)
        
    with col_ctrl5:
        st.markdown("<p style='margin-bottom:4px; font-weight:bold; color:#94A3B8; font-size:12px; white-space:nowrap;'>⏳ CYCLE RATE</p>", unsafe_allow_html=True)
        saved_mins = get_saved_cycle_rate()
        if 1 <= saved_mins <= 10:
            default_dropdown_index = saved_mins - 1
        else:
            default_dropdown_index = 1  
            
        cycle_minutes = st.selectbox(
            "Select Cycle Interval Range:", 
            options=list(range(1, 11)),
            index=default_dropdown_index, 
            format_func=lambda x: f"{x} Min" if x == 1 else f"{x} Mins",
            label_visibility="collapsed"
        )
        
        if cycle_minutes != saved_mins:
            save_cycle_rate(cycle_minutes)
            st.rerun()
            
        cycle_seconds = cycle_minutes * 60

    with col_timer1:
        st.markdown("<p style='margin-bottom:4px; font-weight:bold; color:#94A3B8; font-size:12px; white-space:nowrap;'>📅 LAST PREDICTION SYNC</p>", unsafe_allow_html=True)
        timer1_placeholder = st.empty()
        
    with col_timer2:
        st.markdown("<p style='margin-bottom:4px; font-weight:bold; color:#94A3B8; font-size:12px; white-space:nowrap;'>⏳ NEXT AUTOMATIC CYCLE</p>", unsafe_allow_html=True)
        timer2_placeholder = st.empty()

    @st.fragment(run_every=1)
    def run_dock_timer_subloop(t1_space, t2_space, is_automated, total_seconds_target):
        last_time_str = st.session_state.last_run.strftime("%d:%m:%Y %H:%M:%S")
        t1_space.markdown(f"<div style='height: 42px; display: flex; align-items: center; font-size: 13.5px; font-weight: 600; color: #F1F5F9; font-family: monospace;'>{last_time_str}</div>", unsafe_allow_html=True)
        
        if is_automated:
            elapsed = (datetime.now() - st.session_state.last_run).total_seconds()
            remaining = max(0, total_seconds_target - int(elapsed))
            if remaining <= 0:
                t2_space.markdown("<div style='height: 42px; display: flex; align-items: center; font-size: 12.5px; font-weight: bold; color: #38BDF8;'>🔄 Syncing matrices...</div>", unsafe_allow_html=True)
            else:
                progress_pct = min(1.0, float(total_seconds_target - remaining) / total_seconds_target)
                with t2_space.container():
                    st.progress(progress_pct)
                    st.markdown(f"<p style='margin-top: -11px; font-size: 11.5px; color: #38BDF8; font-weight: 500;'>Initialization in {remaining}s</p>", unsafe_allow_html=True)
        else:
            t2_space.markdown("<div style='height: 42px; display: flex; align-items: center; font-size: 12.5px; color: #64748B; font-style: italic;'>⏸️ Loop Deactivated</div>", unsafe_allow_html=True)

    run_dock_timer_subloop(timer1_placeholder, timer2_placeholder, is_automated=auto_cycle, total_seconds_target=cycle_seconds)

try:
    if os.path.exists("config.csv"):
        df_current_config = pd.read_csv("config.csv", index_col=0)
    else:
        df_current_config = pd.DataFrame(columns=["Value"])
    
    df_current_config.loc["Mode"] = [backend_mode]
    df_current_config.to_csv("config.csv", index_label="Parameter")
except Exception as e:
    st.error(f"Failed to synchronize framework mode matrix: {e}")

st.write("   ")

# ==========================================
# 4. DATA & VISUAL DISPLAY ENGINE
# ==========================================
def get_live_excel_data(file_path):
    cached_file = "cached_live_parameters.csv"
    try:
        if os.path.exists(cached_file):
            df = pd.read_csv(cached_file, index_col=0)
            if 'TIMESTAMP_ROW' in df.index:
                ts_row = df.loc['TIMESTAMP_ROW']
                excel_times = {
                    "T-3": ts_row.iloc[0], 
                    "T-2": ts_row.iloc[1], 
                    "T-1": ts_row.iloc[2], 
                    "T": ts_row.iloc[3]
                }
                df = df.drop('TIMESTAMP_ROW')
            else:
                excel_times = {"T": "N/A", "T-1": "N/A", "T-2": "N/A", "T-3": "N/A"}
            return df, excel_times
    except Exception as e:
        print(f"DEBUG: Cache read failed ({e}).")
    return pd.read_excel(file_path, index_col=0), {"T": "T", "T-1": "T-1", "T-2": "T-2", "T-3": "T-3"}

@st.fragment(run_every=(cycle_seconds if auto_cycle else None))
def render_dynamic_dashboard(mode_to_execute, force_run, total_seconds_target):
    pred_file = "Consolidated_Predictions_And_Validation_Report.csv"
    drivers_file = "Process_Drivers_Interpretability_Profile.csv"
    param_file = find_historian_file()
    
    time_since_last_run = (datetime.now() - st.session_state.last_run).total_seconds()
    outputs_missing = not os.path.exists(pred_file) or not os.path.exists(drivers_file)
    should_execute = force_run or outputs_missing or (auto_cycle and time_since_last_run >= (total_seconds_target - 2))
    
    pipeline_just_ran = False
    
    if should_execute:
        status_placeholder = st.empty()
        status_placeholder.markdown("⏳ **Hydroprocessor OPTIMIZATION MATRIX CYCLE LAUNCHED...**")
        
        try:
            # DIRECTLY CALL THE PIPELINE FUNCTION (Much faster, no subprocess!)
            success = run_optimization_pipeline(RUN_MODE=mode_to_execute, status_placeholder=status_placeholder)
            
            if success:
                pipeline_just_ran = True  
                time.sleep(1.5)
                status_placeholder.empty()
                st.toast("✅ Hydroprocessor Optimization Matrix Refreshed")
                
        except Exception as e:
            import traceback
            traceback.print_exc()  # <--- This prints the exact line number to your CMD terminal
            status_placeholder.error(f"🚨 Background Pipeline Execution Failure: {e}")
            st.session_state.last_run = datetime.now()

    # --------------------------------------
    # 📈 HISTORIAN PROFILE TABLE
    # --------------------------------------
    st.markdown("### 📈 Current Feed Rate & WABTs")
    if param_file and os.path.exists(param_file):
        try:
            df_raw_params, excel_time_map = get_live_excel_data(param_file) 
            df_raw_params = df_raw_params.reset_index()
            df_search = df_raw_params.astype(str).replace(r'^\s+|\s+$|[\r\n]+', '', regex=True)
            param_col = None
            
            for col in df_search.columns:
                if "Feed_Rate" in df_search[col].values:
                    param_col = col
                    break
            
            if param_col is not None:
                df_raw_params[param_col] = df_search[param_col]
                df_raw_params = df_raw_params.set_index(param_col)
                existing_targets = ["Feed_Rate", "WABT_R1_HT", "WABT_R1_HC"]
                
                if existing_targets:
                    df_filtered = df_raw_params.loc[existing_targets]
                    time_cols = [c for c in df_filtered.columns if any(t in str(c) for t in ["T", "T-1", "T-2", "T-3"])]
                    
                    if time_cols:
                        df_filtered_view = df_filtered[time_cols].copy()
                        formatted_labels = []
                        for col in time_cols:
                            col_clean = str(col).strip()
                            raw_time = excel_time_map.get(col_clean, None)
                            
                            # Fallback if timestamp is missing or NaN
                            if pd.isna(raw_time) or str(raw_time).strip().lower() in ['nan', 'n/a', 'none', '']:
                                formatted_time = col_clean
                            else:
                                try:
                                    formatted_time = pd.to_datetime(raw_time).strftime("%d:%m:%Y %H:%M:%S")
                                except Exception:
                                    formatted_time = str(raw_time).strip()
                            
                            formatted_labels.append(formatted_time)
                        
                        # Guarantee 100% unique column headers to prevent pandas duplicate errors
                        unique_labels = []
                        seen_headers = {}
                        for label in formatted_labels:
                            if label in seen_headers:
                                seen_headers[label] += 1
                                unique_labels.append(f"{label} ({seen_headers[label]})")
                            else:
                                seen_headers[label] = 0
                                unique_labels.append(label)

                        time_translation = dict(zip(time_cols, unique_labels))
                        df_ui_view = df_filtered_view.rename(columns=time_translation)
                        
                        st.dataframe(
                            df_ui_view.style.format(lambda x: f"{float(x):.2f}" if pd.notnull(x) and str(x).replace('.','',1).isdigit() else str(x)), 
                            width='stretch', 
                            column_config={col: st.column_config.Column(alignment="center") for col in df_ui_view.columns}
                        )
                    else:
                        st.dataframe(df_filtered, width='stretch')
                else:
                    st.warning("Target parameters found, but extraction failed.")
            else:
                st.warning("Could not locate 'Feed_Rate' anywhere in the Excel data. Check file structure.")
        except Exception as e:
            st.error(f"Error parsing parameters historian matrix: {e}")
    else:
        st.info("Searching for historian file pipeline path logs in root context...")

    st.write("   ")

    # --------------------------------------
    # CRITICAL METRIC HIGHLIGHTS
    # --------------------------------------
    st.subheader("🎯 Critical Rundown Properties' Prediction")
    if os.path.exists(pred_file):
        df_t1 = pd.read_csv(pred_file, index_col=0)
        try:
            d95_t = float(df_t1.loc['Blend_Diesel_D95', 'T'])
            flash_t = float(df_t1.loc['Blend_Diesel_Flash', 'T'])
            yield_t = float(df_t1.loc['Blend_Diesel_Yield', 'T'])
        except Exception:
            d95_t = float(df_t1.loc['Blend_Diesel_D95', 'T']) if 'Blend_Diesel_D95' in df_t1.index else 361.81
            flash_t = float(df_t1.loc['Blend_Diesel_Flash', 'T']) if 'Blend_Diesel_Flash' in df_t1.index else 85.00
            p_yield = float(df_t1.loc['Product_Diesel_Yield', 'T']) if 'Product_Diesel_Yield' in df_t1.index else 219.62
            k_yield = float(df_t1.loc['Kero_to_Diesel', 'T']) if 'Kero_to_Diesel' in df_t1.index else (float(df_t1.loc['Kerosene_Yield', 'T']) if 'Kerosene_Yield' in df_t1.index else 0.0)
            yield_t = p_yield + k_yield

        # 🚨 D95 OPERATOR ALERT LOGIC 🚨
        if d95_t > 370:
            alert_msg = "<div class='alert-red'>🚨 Offspec: Increase Diesel Pump Down Flow</div>"
        elif d95_t < 365:
            alert_msg = "<div class='alert-yellow'>⚠️ Quality Giveaway: Reduce Diesel Pump Down Flow</div>"
        else:
            alert_msg = "<div class='alert-green'>✅ Blend Diesel D95 is On Spec</div>"

        # Render Integrated Cards
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(
                f"""<div class='metric-box'>
                    <div style='margin:0;color:inherit;font-size:22px;font-weight:bold;'>Blend Diesel D95</div>
                    <div style='margin:2px 0;color:#38BDF8;font-size:40px;font-weight:bold;'>{d95_t:.2f} °C</div>
                    {alert_msg}
                </div>""", 
                unsafe_allow_html=True
            )
        with m2:
            st.markdown(
                f"""<div class='metric-box'>
                    <div style='margin:0;color:inherit;font-size:22px;font-weight:bold;'>Blend Diesel Flash Point</div>
                    <div style='margin:2px 0;color:#38BDF8;font-size:40px;font-weight:bold;'>{flash_t:.2f} °C</div>
                </div>""", 
                unsafe_allow_html=True
            )
        with m3:
            st.markdown(
                f"""<div class='metric-box'>
                    <div style='margin:0;color:inherit;font-size:22px;font-weight:bold;'>Blend Diesel Yield</div>
                    <div style='margin:2px 0;color:#38BDF8;font-size:40px;font-weight:bold;'>{yield_t:.2f} T/h</div>
                </div>""", 
                unsafe_allow_html=True
            )
        
        st.write("   ")
        st.write("   ")

    # --------------------------------------
    # MAIN TABLES LAYOUT
    # --------------------------------------
    col_left, col_right = st.columns([1.1, 0.9])
    with col_left:
        st.markdown("### 📋 Predictive Horizon Output for the next 3 hours")
        if os.path.exists(pred_file):
            df_t1_fresh = pd.read_csv(pred_file, index_col=0)
            header_padding_map = {col: str(col).center(14) for col in df_t1_fresh.columns}
            df_padded_horizon = df_t1_fresh.rename(columns=header_padding_map)
            
            styled_df = df_padded_horizon.style.map(
                lambda v: 'color: #38BDF8; font-weight: bold;' if v in ['Physics', 'Calculated'] else '',
            ).format(lambda x: f"{x:.3f}" if isinstance(x, (int, float)) else str(x))
            
            st.dataframe(
                styled_df, 
                width='stretch', 
                height=460, 
                column_config={col: st.column_config.Column(alignment="center") for col in df_padded_horizon.columns}
            )
            st.download_button(
                label="📥 Export Prediction Report (.CSV)",
                data=df_t1_fresh.to_csv().encode('utf-8'),
                file_name="Hydroprocessor_Horizon_Predictions.csv",
                mime="text/csv",
                key="btn_dl_pred"
            )
        else:
            st.info("Awaiting predictive data streams...")

    with col_right:
        st.markdown("### 🎯 Top 5 Impact Process Drivers")
        if os.path.exists(drivers_file):
            df_t2 = pd.read_csv(drivers_file, index_col=0)
            st.dataframe(df_t2, width='stretch', height=460)
            st.download_button(
                label="📥 Export Drivers Profile (.CSV)",
                data=df_t2.to_csv().encode('utf-8'),
                file_name="Hydroprocessor_Process_Drivers.csv",
                mime="text/csv",
                key="btn_dl_drivers"
            )
        else:
            st.info("Awaiting interpretability feature matrices...")

    # ==========================================
    # 5. PRESCRIPTIVE OPTIMIZATION ENGINE
    # ==========================================
    st.markdown("---")
    st.header("🎛️ Advanced Hybrid Process Control Engine")
    st.markdown("<p style='color:#94A3B8; font-size:14px; margin-bottom: 16px;'>Calculate required set-point moves to achieve target rundown properties.</p>", unsafe_allow_html=True)
    
    with st.container(border=True):
        # Outer split: Left side for 3-column control grid, Right side for Action Button
        left_grid, right_btn_col = st.columns([3.6, 1.2], vertical_alignment="center")
        
        with left_grid:
            # --- HEADER ROW (14px Bold) ---
            h1, h2, h3 = st.columns([1.2, 1.1, 1.3], vertical_alignment="center")
            with h1:
                st.markdown("<p style='font-weight:bold; color:#F1F5F9; font-size:14px; margin:0;'>Optimization Target:</p>", unsafe_allow_html=True)
            with h2:
                st.markdown("<p style='font-weight:bold; color:#F1F5F9; font-size:14px; margin:0;'>Current Properties:</p>", unsafe_allow_html=True)
            with h3:
                st.markdown("<p style='font-weight:bold; color:#F1F5F9; font-size:14px; margin:0;'>Target Properties (°C):</p>", unsafe_allow_html=True)

            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

            # --- ROW 1: BLEND DIESEL D95 (14px) ---
            r1_1, r1_2, r1_3 = st.columns([1.2, 1.1, 1.3], vertical_alignment="center")
            with r1_1:
                chk_d95 = st.checkbox("Blend Diesel D95", value=True, key="chk_opt_d95")
            with r1_2:
                st.markdown(f"<div style='font-size:14px; color:#94A3B8;'>D95: <span style='color:#38BDF8; font-weight:bold; font-size:14px;'>{d95_t:.2f} °C</span></div>", unsafe_allow_html=True)
            with r1_3:
                desired_d95 = st.number_input(
                    "Target D95",
                    value=float(d95_t),
                    step=0.5,
                    format="%.1f",
                    disabled=not chk_d95,
                    key="num_target_d95",
                    label_visibility="collapsed"
                )

            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

            # --- ROW 2: BLEND DIESEL FLASH (14px) ---
            r2_1, r2_2, r2_3 = st.columns([1.2, 1.1, 1.3], vertical_alignment="center")
            with r2_1:
                chk_flash = st.checkbox("Blend Diesel Flash", value=False, key="chk_opt_flash")
            with r2_2:
                st.markdown(f"<div style='font-size:14px; color:#94A3B8;'>Flash: <span style='color:#38BDF8; font-weight:bold; font-size:14px;'>{flash_t:.2f} °C</span></div>", unsafe_allow_html=True)
            with r2_3:
                desired_flash = st.number_input(
                    "Target Flash",
                    value=float(flash_t),
                    step=0.5,
                    format="%.1f",
                    disabled=not chk_flash,
                    key="num_target_flash",
                    label_visibility="collapsed"
                )

        # --- RIGHT COLUMN: GREEN ESTIMATE BUTTON ---
        with right_btn_col:
            btn_clicked = st.button("ESTIMATE OPTIMAL MOVES", type="primary", use_container_width=True)

        # Map checkboxes to backend target_mode string
        if chk_d95 and chk_flash:
            target_mode = "Blend_Diesel_D95 & Blend_Diesel_Flash"
        elif chk_d95:
            target_mode = "Blend_Diesel_D95"
        elif chk_flash:
            target_mode = "Blend_Diesel_Flash"
        else:
            target_mode = None

        # Process optimization on button click
        if btn_clicked:
            if target_mode is None:
                st.warning("⚠️ Please select at least one Optimization Target checkbox.")
            else:
                with st.spinner("Simulating 3D-Grid Operating Scenarios..."):
                    from core_engine import run_what_if_optimization
                    res = run_what_if_optimization(target_mode, desired_d95, desired_flash)
                    
                    if "error" in res:
                        st.error(res["error"])
                    else:
                        act = res["actions"]
                        pred = res["results"]
                        
                        if res["limit_reached"]:
                            st.warning("**⚠️ LIMIT REACHED: TARGET OUTSIDE SAFE OPERATING WINDOW**\nThe desired target cannot be perfectly matched within safe step limits. Showing closest achievable physical match.")
                        else:
                            if "Both" in target_mode or "&" in target_mode:
                                st.success("**✅ OPTIMIZATION COMPLETE: BEST COMPROMISE ACHIEVED**")
                            else:
                                st.success("**✅ OPTIMIZATION SUCCESSFUL: TARGET ACHIEVED**")

                        actions_md = "#### 🎛️ Primary Set-Point Actions:\n"
                        if "D95" in target_mode or "&" in target_mode:
                            fzt_word = "Increase" if act['delta_fzt'] >= 0 else "Decrease"
                            dot_word = "Increase" if act['delta_dot'] >= 0 else "Decrease"
                            actions_md += f"* **Diesel Flash Zone Temp:** {fzt_word} by **{abs(act['delta_fzt']):.1f} °C** ➔ *(New Target: {act['new_fzt']:.1f} °C)*\n"
                            actions_md += f"* **Diesel Draw-Off Temp:** {dot_word} by **{abs(act['delta_dot']):.1f} °C** ➔ *(New Target: {act['new_dot']:.1f} °C)*\n"
                        
                        if "Flash" in target_mode or "&" in target_mode:
                            k2d_word = "Increase" if act['delta_k2d'] >= 0 else "Decrease"
                            k2a_word = "Increase" if act['delta_k2atf'] >= 0 else "Decrease"
                            actions_md += f"* **Kerosene to Diesel Routing:** {k2d_word} by **{abs(act['delta_k2d']):.1f} T/h** ➔ *(New Target: {act['new_k2d']:.1f} T/h)*\n"
                            actions_md += f"* **Kerosene to ATF Diversion:** {k2a_word} by **{abs(act['delta_k2atf']):.1f} T/h** ➔ *(New Target: {act['new_k2atf']:.1f} T/h)*\n"

                        props_md = "#### 📉 Final Predicted Steady-State Properties:\n"
                        props_md += f"* **Blend Diesel D95:** {pred['d95']:.1f} °C *(Off target by {pred['d95'] - desired_d95:+.1f} °C)*\n"
                        props_md += f"* **Blend Diesel Flash:** {pred['flash']:.1f} °C *(Off target by {pred['flash'] - desired_flash:+.1f} °C)*\n"
                        props_md += f"* **Blend Diesel Yield:** {pred['yield']:.1f} T/h\n"

                        with st.container(border=True):
                            st.markdown(actions_md)
                            st.divider()
                            st.markdown(props_md)
                        
                    time.sleep(0.5)
                
    if pipeline_just_ran:
        st.session_state.last_run = datetime.now()
        st.rerun() 
        
render_dynamic_dashboard(mode_to_execute=backend_mode, force_run=trigger_manual, total_seconds_target=cycle_seconds)