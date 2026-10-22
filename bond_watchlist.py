"""Consulta informativa Data912 para seis bonos. No calcula patrimonio ni escribe Sheets."""
import requests

SYMBOLS=("AN29","AO28","AO29","GD35","GD38","GD41")
URL="https://data912.com/live/arg_bonds"

def read_bond_watchlist(timeout=12):
    response=requests.get(URL,timeout=timeout,headers={"Accept":"application/json"})
    response.raise_for_status()
    data=response.json()
    if not isinstance(data,list):
        raise ValueError("Formato inesperado del proveedor")
    by_symbol={}
    for item in data:
        if not isinstance(item,dict):
            continue
        symbol=str(item.get("symbol","")).upper().strip()
        if symbol not in SYMBOLS:
            continue
        try:
            price=float(item["c"])
        except (ValueError,TypeError,KeyError):
            continue
        if not (0<price<float("inf")):
            continue
        by_symbol[symbol]=price
    return [{"Ticker":symbol,"Precio crudo Data912":by_symbol.get(symbol),
             "Estado":"Dato experimental" if symbol in by_symbol else "No disponible"}
            for symbol in SYMBOLS]
