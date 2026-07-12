"""
parse_fit.py
Parses a FIT file into a pandas DataFrame representing a time-series stream.
"""

import os
import pandas as pd
from fitparse import FitFile
from typing import Optional

def parse_fit_to_df(filepath: str) -> Optional[pd.DataFrame]:
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"FIT file not found: {filepath}")
        
    try:
        fitfile = FitFile(filepath)
    except Exception as e:
        print(f"Error parsing FIT file {filepath}: {e}")
        return None

    records = []
    
    for record in fitfile.get_messages('record'):
        record_data = {}
        for data in record:
            if data.name:
                record_data[data.name] = data.value
        if record_data:
            records.append(record_data)
            
    if not records:
        return pd.DataFrame()
        
    df = pd.DataFrame(records)
    
    rename_map = {
        'timestamp': 'time',
        'heart_rate': 'heartrate',
        'position_lat': 'latitude',
        'position_long': 'longitude'
    }
    
    df.rename(columns=rename_map, inplace=True, errors='ignore')
    
    for col in ['latitude', 'longitude']:
        if col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]) and df[col].max() > 200:
                df[col] = df[col] * (180.0 / (2**31))
                
    return df

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        df = parse_fit_to_df(sys.argv[1])
        if df is not None:
            print(df.head())
