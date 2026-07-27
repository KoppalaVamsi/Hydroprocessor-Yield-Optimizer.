import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

print("⚡ Running Complete Data Generator...")

if os.path.exists("rf_production_models.pkl"):
    os.remove("rf_production_models.pkl")

np.random.seed(42)

dcs_cols = [
    'Catalyst_Age_in_hours', 'Feed_Rate', 'WABT_R1_HT', 'WABT_R1_HC', 'System_Pressure',
    'Hydrogen_Consumption', 'RCO_Yield', 'Plant_Conversion', 'Diesel_Draw-Off_Temperature',
    'Diesel_Flash_Zone_Temperature', 'Diesel_Circulation_Return_Temp', 'Diesel_Pump_Down_Flow',
    'Diesel_Pump_Around_Flow', 'HF_Top_Pressure', 'HF_Top_Temperature', 'HF_Bottom_Temperature',
    'RCO_Steam', 'UCO_Steam', 'Product_Diesel_Yield', 'Kerosene_Draw-Off_Temperature',
    'Kero_Reboiler_Outlet_Temperature', 'HF_Receiver_to_LF_flow', 'LF_Inlet_Temperature',
    'LF_Reflux', 'LF_Receiver_Inlet_Temperature', 'LF_Top_Pressure', 'LF_Top_Temperature',
    'LF_Steam', 'LF_bottom_to_HF_Flow', 'Kerosene_Yield', 'DE_Feed_from_V101', 'DB_Feed_from_V102',
    'DHT_Offgases', 'Lean_Oil_Flow', 'DE_Pressure', 'DB_Pressure', 'DE_Top_Temp', 'DB_Top_Temp',
    'DE_Reboiler_Outlet_Temperature', 'DB_Reboiler_Outlet_Temperature', 'DB_Tray_Temperature',
    'DB_Receiver_Inlet_Temperature', 'LPG_Yield', 'Total_Naphtha_Yield', 'MP_Sponge_Oil_Flow',
    'LP_Sponge_Oil_Flow', 'Sponge_Oil_Temperature'
]

lab_cols = [
    'Feed_Density', 'Feed_Nitrogen', 'Feed_Sulphur', 'Product_Diesel_D95',
    'Product_Diesel_Flash', 'Kerosene_FBP', 'Kero Flash', 'Kerosene_D95',
    'Product_Diesel_D5', 'Product_Diesel_D10', 'Product_Diesel_D50', 'Product_Diesel_D85',
    'Product_Diesel_D90', 'Product_Diesel_D100', 'Kero_D05', 'Kero_D50', 'Kero_D90'
]

live_cols = [
    'Catalyst_Age_in_hours', 'Feed_Density', 'Feed_Nitrogen', 'Feed_Sulphur', 'Feed_Rate',
    'WABT_R1_HT', 'WABT_R1_HC', 'System_Pressure', 'Hydrogen_Consumption', 'RCO_Yield',
    'Plant_Conversion', 'Diesel_Draw-Off_Temperature', 'Diesel_Flash_Zone_Temperature',
    'Diesel_Circulation_Return_Temp', 'Diesel_Pump_Down_Flow', 'Diesel_Pump_Around_Flow',
    'HF_Top_Pressure', 'HF_Top_Temperature', 'HF_Bottom_Temperature', 'RCO_Steam',
    'UCO_Steam', 'Kerosene_to_Diesel', 'Kerosene_to_ATF', 'Kerosene_Draw-Off_Temperature',
    'Kero_Reboiler_Outlet_Temperature', 'HF_Receiver_to_LF_flow', 'LF_Inlet_Temperature',
    'LF_Reflux', 'LF_Receiver_Inlet_Temperature', 'LF_Top_Pressure', 'LF_Top_Temperature',
    'LF_Steam', 'LF_bottom_to_HF_Flow', 'DE_Feed_from_V101', 'DB_Feed_from_V102',
    'DHT_Offgases', 'Lean_Oil_Flow', 'DE_Pressure', 'DB_Pressure', 'DE_Top_Temp',
    'DB_Top_Temp', 'DE_Reboiler_Outlet_Temperature', 'DB_Reboiler_Outlet_Temperature',
    'DB_Tray_Temperature', 'DB_Receiver_Inlet_Temperature', 'MP_Sponge_Oil_Flow',
    'LP_Sponge_Oil_Flow', 'Sponge_Oil_Temperature'
]

baselines = {
    'Catalyst_Age_in_hours': 34500.0, 'Feed_Rate': 220.0, 'WABT_R1_HT': 372.5, 'WABT_R1_HC': 368.0,
    'System_Pressure': 155.2, 'Hydrogen_Consumption': 7000, 'RCO_Yield': 2.0, 'Plant_Conversion': 97.5,
    'Diesel_Draw-Off_Temperature': 285.0, 'Diesel_Flash_Zone_Temperature': 345.0,
    'Diesel_Circulation_Return_Temp': 180.0, 'Diesel_Pump_Down_Flow': 180.0, 'Diesel_Pump_Around_Flow': 320.0,
    'HF_Top_Pressure': 300, 'HF_Top_Temperature': 77.0, 'HF_Bottom_Temperature': 310.0, 'RCO_Steam': 5,
    'UCO_Steam': 1.8, 'Product_Diesel_Yield': 135.0, 'Kerosene_Draw-Off_Temperature': 195.0,
    'Kero_Reboiler_Outlet_Temperature': 215.0, 'HF_Receiver_to_LF_flow': 20.0, 'LF_Inlet_Temperature': 245.0,
    'LF_Reflux': 35.0, 'LF_Receiver_Inlet_Temperature': 70.0, 'LF_Top_Pressure': 0.8,
    'LF_Top_Temperature': 130.0, 'LF_Steam': 0.8, 'LF_bottom_to_HF_Flow': 60.0, 'Kerosene_Yield': 38.0,
    'DE_Feed_from_V101': 25.0, 'DB_Feed_from_V102': 20.0, 'DHT_Offgases': 5.5, 'Lean_Oil_Flow': 15.0,
    'DE_Pressure': 14.5, 'DB_Pressure': 11.2, 'DE_Top_Temp': 65.0, 'DB_Top_Temp': 75.0,
    'DE_Reboiler_Outlet_Temperature': 190.0, 'DB_Reboiler_Outlet_Temperature': 210.0,
    'DB_Tray_Temperature': 105.0, 'DB_Receiver_Inlet_Temperature': 58.0, 'LPG_Yield': 12.0,
    'Total_Naphtha_Yield': 52.0, 'MP_Sponge_Oil_Flow': 12.0, 'LP_Sponge_Oil_Flow': 18.0,
    'Sponge_Oil_Temperature': 42.0, 'Feed_Density': 0.865, 'Feed_Nitrogen': 1025.0, 'Feed_Sulphur': 2120.0,
    'Product_Diesel_D95': 362.0, 'Product_Diesel_Flash': 94.0, 'Kerosene_FBP': 255.0, 'Kero Flash': 48.0,
    'Kerosene_D95': 240.0, 'Product_Diesel_D5': 240.0, 'Product_Diesel_D10': 252.0, 'Product_Diesel_D50': 282.0,
    'Product_Diesel_D85': 342.0, 'Product_Diesel_D90': 352.0, 'Product_Diesel_D100': 370.0, 'Kero_D05': 155.0,
    'Kero_D50': 198.0, 'Kero_D90': 233.5, 'Kerosene_to_Diesel': 45.0, 'Kerosene_to_ATF': 15.0
}

start_time = datetime(2025, 5, 1, 0, 0)
time_stamps = [(start_time + timedelta(hours=i)).strftime("%d-%m-%Y %H:%M") for i in range(1000)]

# 1. Bulk DCS
dcs_data = {"Time": time_stamps}
for col in dcs_cols:
    base = baselines.get(col, 100.0)
    if col == "Catalyst_Age_in_hours":
        dcs_data[col] = np.round(base + np.arange(1000) * 1.0, 1)
    else:
        noise = np.cumsum(np.random.normal(0, 0.05, 1000))
        dcs_data[col] = np.round(base + noise, 2)
pd.DataFrame(dcs_data).to_csv("Bulk_Data_DCS 47 Parameters against Time.csv", index=False)

# 2. Bulk Lab
lab_data = {"Sample_collection_Date_and_Time": time_stamps}
for col in lab_cols:
    base = baselines.get(col, 100.0)
    noise = np.cumsum(np.random.normal(0, 0.03, 1000))
    lab_data[col] = np.round(base + noise, 2)
pd.DataFrame(lab_data).to_csv("Bulk_Data_Lab 18 Parameters against Time.csv", index=False)

# 3. Live Snapshot with explicit Timestamps
time_cols = ["T-3", "T-2", "T-1", "T"]
now = datetime.now()
ts_strings = [(now - timedelta(hours=3-i)).strftime("%d-%m-%Y %H:%M:%S") for i in range(4)]

live_data = {}
for param in live_cols:
    base = baselines.get(param, 100.0)
    vals = base + np.random.normal(0, 0.2, 4)
    live_data[param] = np.round(vals, 2)

df_live = pd.DataFrame(live_data, index=time_cols).T
df_live.index.name = "Parameter"
df_live_cache = df_live.copy()
df_live_cache.loc["TIMESTAMP_ROW"] = ts_strings

df_live_cache.to_csv("cached_live_parameters.csv")

try:
    with pd.ExcelWriter("46 Parameters Last 4 hours Data Live Excel version.xlsx") as writer:
        df_live_cache.to_excel(writer, sheet_name="Sheet1")
except Exception:
    pass

# 4. Correlation Matrix Generator (Retains exact original dataset mapping)
correlation_dict = {
    'Unnamed: 0': ['Catalyst_Age_in_hours', 'Feed_Density', 'Feed_Nitrogen', 'Feed_Sulphur', 'Feed_Rate', 'WABT_R1_HT', 'WABT_R1_HC', 'System_Pressure', 'Hydrogen_Consumption', 'RCO_Yield', 'Plant_Conversion', 'Diesel_Draw-Off_Temperature', 'Diesel_Flash_Zone_Temperature', 'Diesel_Circulation_Return_Temp', 'Diesel_Pump_Down_Flow', 'Diesel_Pump_Around_Flow', 'HF_Top_Pressure', 'HF_Top_Temperature', 'HF_Bottom_Temperature', 'RCO_Steam', 'UCO_Steam', 'Product_Diesel_Yield', 'Product_Diesel_D95', 'Product_Diesel_Flash', 'Kerosene_Draw-Off_Temperature', 'Kero_Reboiler_Outlet_Temperature', 'HF_Receiver_to_LF_flow', 'LF_Inlet_Temperature', 'LF_Receiver_Inlet_Temperature', 'LF_Reflux', 'LF_Top_Pressure', 'LF_Top_Temperature', 'LF_Steam', 'LF_bottom_to_HF_Flow', 'Kerosene_Yield', 'Kerosene_D95', 'Kerosene_FBP', 'Kerosene_Flash', 'DE_Feed_from_V101', 'DB_Feed_from_V102', 'DHT_Offgases', 'Lean_Oil_Flow', 'DE_Pressure', 'DB_Pressure', 'DE_Top_Temp', 'DB_Top_Temp', 'DE_Reboiler_Outlet_Temperature', 'DB_Reboiler_Outlet_Temperature.1', 'DB_Tray_Temperature', 'DB_Receiver_Inlet_Temperature', 'LPG_Yield', 'Total_Naphtha_Yield', 'MP_Sponge_Oil_Flow', 'LP_Sponge_Oil_Flow', 'Sponge_Oil_Temperature'], 
    'Product_Diesel_Yield': ['Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'No', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'No', 'No', 'No', 'No', 'No', 'Yes', 'Yes', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No'], 
    'Product_Diesel_D95': ['No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'No', 'No', 'No', 'No', 'No', 'Yes', 'Yes', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No'], 
    'Product_Diesel_Flash': ['No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'No', 'No', 'No', 'No', 'No', 'Yes', 'Yes', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No'], 
    'Kerosene_Yield': ['Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'No', 'Yes', 'Yes', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'No', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No'], 
    'Kerosene_D95': ['No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No'], 
    'Kerosene_FBP': ['No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No'], 
    'Kerosene_Flash': ['No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No'], 
    'LPG_Yield': ['Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'Yes', 'No', 'Yes', 'Yes', 'Yes', 'No', 'No', 'No', 'No', 'No', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'No', 'No', 'No'], 
    'Total_Naphtha_Yield': ['Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'No', 'Yes', 'No', 'Yes', 'Yes', 'Yes', 'No', 'No', 'No', 'No', 'No', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes']
}
pd.DataFrame(correlation_dict).to_csv("55 Total Parameters Correlations with 9 Target Parameters.csv", index=False)

print("\n🎉 DATASETS AND TIMESTAMPS SYNCED PERFECTLY!")