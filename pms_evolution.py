"""Simple observed-history periods. Never fabricate missing observations or investment returns."""
import pandas as pd

WINDOWS={"Todo":None,"1M":31,"3M":92,"6M":183,"1A":366,"3A":1096,"5A":1827}

def observed_window(frame,date_column,window="Todo"):
    if window not in WINDOWS:
        raise ValueError("Período inválido")
    if frame is None or frame.empty:
        return frame.copy()
    out=frame.copy()
    out[date_column]=pd.to_datetime(out[date_column],errors="coerce")
    out=out.dropna(subset=[date_column]).sort_values(date_column)
    out=out.drop_duplicates(date_column,keep="last")
    days=WINDOWS[window]
    if days is not None and not out.empty:
        out=out.loc[out[date_column]>=out[date_column].max()-pd.Timedelta(days=days)]
    return out
