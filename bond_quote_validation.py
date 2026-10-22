"""Validación determinística de cotizaciones de bonos, independiente del proveedor.

No realiza escrituras ni convierte automáticamente especies ARS/USD.
Precios aceptados únicamente cuando el adaptador declara mercado, divisa,
denominador nominal, fecha de mercado y símbolo exacto.
"""
from datetime import date, datetime
from math import isfinite

BONOS = frozenset({"AN29", "AO28", "AO29", "GD35", "GD38", "GD41"})
MAX_AGE_CALENDAR_DAYS = 7

class BondQuoteError(ValueError):
    pass

def validate_bond_quote(quote, today=None):
    if not isinstance(quote, dict):
        raise BondQuoteError("La cotización debe ser un objeto")
    symbol = str(quote.get("symbol", "")).strip().upper()
    if symbol not in BONOS:
        raise BondQuoteError("Símbolo no contemplado")
    market = str(quote.get("market", "")).strip().upper()
    if market != "BYMA":
        raise BondQuoteError("Mercado no verificado")
    currency = str(quote.get("currency", "")).strip().upper()
    if currency not in {"ARS", "USD"}:
        raise BondQuoteError("Moneda no verificada")
    try:
        nominal_basis = float(quote["nominal_basis"])
        price = float(quote["price"])
    except (KeyError, ValueError, TypeError):
        raise BondQuoteError("Precio o base nominal ausentes")
    if nominal_basis != 100.0:
        raise BondQuoteError("Base nominal distinta de 100 VN")
    if not isfinite(price) or price <= 0:
        raise BondQuoteError("Precio inválido")
    raw_date = quote.get("market_date")
    try:
        market_date = date.fromisoformat(raw_date) if isinstance(raw_date, str) else raw_date
        if isinstance(market_date, datetime):
            market_date = market_date.date()
        if not isinstance(market_date, date):
            raise ValueError("Fecha incorrecta")
    except ValueError as exc:
        raise BondQuoteError("Fecha de mercado inválida") from exc
    current = today or date.today()
    age = (current - market_date).days
    if age < 0 or age > MAX_AGE_CALENDAR_DAYS:
        raise BondQuoteError("Fecha futura u obsoleta")
    if not str(quote.get("source", "")).strip():
        raise BondQuoteError("Fuente ausente")
    return {
        "symbol": symbol, "price": price, "currency": currency,
        "market_date": market_date.isoformat(), "market": market,
        "nominal_basis": 100, "source": str(quote["source"]).strip(),
        "status": "VALIDATED_METADATA"
    }

def value_usd(nominal_units, quote, usd_fx=None, today=None):
    """Valuación condicionada; fx = ARS por USD y validado externamente."""
    checked = validate_bond_quote(quote, today=today)
    try:
        units = float(nominal_units)
    except (TypeError, ValueError) as exc:
        raise BondQuoteError("Cantidad nominal inválida") from exc
    if not isfinite(units) or units < 0:
        raise BondQuoteError("Cantidad nominal inválida")
    native_value = units * checked["price"] / 100
    if checked["currency"] == "USD":
        return native_value
    try:
        fx = float(usd_fx)
    except (ValueError, TypeError) as exc:
        raise BondQuoteError("Falta cotización ARS/USD válida") from exc
    if not isfinite(fx) or fx <= 0:
        raise BondQuoteError("Falta cotización ARS/USD válida")
    return native_value / fx
