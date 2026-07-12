"""
parse_gpx.py
Parses a GPX file into a pandas DataFrame representing a time-series stream.
"""

import os
import pandas as pd
import gpxpy
from typing import Optional

def parse_gpx_to_df(filepath: str) -> Optional[pd.DataFrame]:
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"GPX file not found: {filepath}")
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            gpx = gpxpy.parse(f)
    except Exception as e:
        print(f"Error parsing GPX file {filepath}: {e}")
        return None

    records = []
    
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                record = {
                    'time': point.time,
                    'latitude': point.latitude,
                    'longitude': point.longitude,
                    'altitude': point.elevation,
                }
                
                if point.extensions:
                    # Depending on how the XML is parsed, it might be an element tree
                    try:
                        for ext_elem in point.extensions:
                            for child in ext_elem.iter():
                                if child.tag.endswith('hr'):
                                    record['heartrate'] = int(child.text)
                                elif child.tag.endswith('cad'):
                                    record['cadence'] = int(child.text)
                    except Exception:
                        pass
                
                records.append(record)
                
    if not records:
        return pd.DataFrame()
        
    return pd.DataFrame(records)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        df = parse_gpx_to_df(sys.argv[1])
        if df is not None:
            print(df.head())
