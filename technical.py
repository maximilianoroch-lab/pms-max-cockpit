"""Análisis técnico independiente: cálculos determinísticos sobre precios de cierre."""
import pandas as pd

def indicators(close):
    s=pd.to_numeric(pd.Series(close),errors="coerce").dropna()
    s=s[s>0]
    out=pd.DataFrame({"Close":s})
    if len(out)<200:
        raise ValueError("Se necesitan al menos 200 cierres válidos para EMA 200.")
    for n in (21,50,200):
        out[f"EMA {n}"]=out["Close"].ewm(span=n,adjust=False).mean()
    delta=out["Close"].diff()
    gain=delta.clip(lower=0).ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    loss=(-delta.clip(upper=0)).ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    rs=gain/loss.replace(0,float("nan"))
    out["RSI 14"]=100-(100/(1+rs))
    out.loc[(loss==0)&(gain>0),"RSI 14"]=100
    out.loc[(loss==0)&(gain==0),"RSI 14"]=50
    return out

def fetch_history(symbol,period="5y"):
    """Yahoo Finance via yfinance. Do not silently infer Argentine CEDEAR mapping."""
    import yfinance as yf
    sym=str(symbol).strip().upper()
    if not sym or any(ch not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-^=" for ch in sym):
        raise ValueError("Ticker inválido")
    frame=yf.Ticker(sym).history(period=period,interval="1d",auto_adjust=True)
    if frame is None or frame.empty or "Close" not in frame:
        raise ValueError("No se encontró una serie histórica verificable para este símbolo.")
    result=indicators(frame["Close"])
    result.index=pd.to_datetime(result.index).tz_localize(None)
    return result
