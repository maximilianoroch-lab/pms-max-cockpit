"""Simulaciones puras sobre tenencias DEMO V5; nunca modifica inventario."""
def simulate_demo_trade(positions,ticker,operation,amount,funding="CASH",source=None,cash_amount=0):
    import math
    try:
        h={str(k):float(v) for k,v in positions.items()}
        ticker=str(ticker)
        amount=float(amount)
        cash_amount=float(cash_amount)
    except (TypeError,ValueError,OverflowError):
        return {"error":"Los importes deben ser numéricos."}
    if not all(math.isfinite(x) for x in h.values()) or not math.isfinite(amount) or not math.isfinite(cash_amount):
        return {"error":"Los importes deben ser números finitos."}
    if any(v<0 for v in h.values()):
        return {"error":"La cartera contiene posiciones negativas; no es seguro simular."}
    if cash_amount<0:return {"error":"El uso de CASH no puede ser negativo."}
    if amount<=0:return {"error":"El monto debe ser positivo."}
    if ticker=="CASH" or ticker not in h:return {"error":"Elegí un activo válido distinto de CASH."}
    if operation not in ("Comprar","Vender"):return {"error":"Operación no válida."}
    before=h.copy()
    total=sum(before.values())
    if not math.isfinite(total) or total<=0:
        return {"error":"El patrimonio inicial debe ser positivo."}
    cash_before=h.get("CASH",0.0)
    value_before=h[ticker]
    source_before=h.get(source,0.0) if source else 0.0
    sale_used=0.0
    source_out=None
    if operation=="Comprar":
        if funding not in ("CASH","Venta de otro activo","CASH + venta de activo","Aporte externo"):
            return {"error":"Origen de fondos inválido."}
        used=amount if funding=="CASH" else cash_amount if funding=="CASH + venta de activo" else 0.0
        if used<0 or used>amount:return {"error":"Uso de CASH fuera del monto de compra."}
        if used>cash_before:return {"error":"CASH insuficiente para la compra."}
        sale_used=amount-used if funding in ("Venta de otro activo","CASH + venta de activo") else 0.0
        if sale_used:
            if not source or source in (ticker,"CASH") or source not in h:
                return {"error":"Elegí otro activo válido para financiar."}
            if sale_used>source_before:
                return {"error":"La venta del activo de origen excede su tenencia."}
            h[source]-=sale_used
            source_out=source
        h["CASH"]=cash_before-used
        h[ticker]+=amount
        new_total=total+(amount if funding=="Aporte externo" else 0.0)
    else:
        if funding not in ("CASH","Retiro externo"):
            return {"error":"Destino de fondos inválido."}
        if amount>value_before:return {"error":"La venta excede la posición disponible."}
        h[ticker]-=amount
        if funding=="CASH":h["CASH"]=cash_before+amount
        new_total=total-(amount if funding=="Retiro externo" else 0.0)
    if not math.isfinite(new_total) or new_total<=0 or any(not math.isfinite(v) or v<0 for v in h.values()):
        return {"error":"El patrimonio o las posiciones resultantes no son válidos."}
    if abs(sum(h.values())-new_total)>0.01:return {"error":"No concilian los fondos simulados."}
    def top5(d,t):return sum(sorted((max(0,v) for v in d.values()),reverse=True)[:5])/t
    return {"ticker":ticker,"operation":operation,"amount":amount,"funding":funding,
        "source_ticker":source_out,"source_before":source_before,
        "source_after":h.get(source,0.0) if source else 0.0,
        "value_before":value_before,"value_after":h[ticker],
        "cash_before":cash_before,"cash_after":h.get("CASH",0),
        "total_before":total,"total_after":new_total,
        "weight_before":value_before/total,"weight_after":h[ticker]/new_total,
        "top5_before":top5(before,total),"top5_after":top5(h,new_total)}
