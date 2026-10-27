"""Pure simulation adapter reused by Bersoch, without Streamlit dependencies."""
from demo_trade import simulate_demo_trade as _engine

def simulate_portfolio_trade(holdings,ticker,operation,amount,funding_mode="CASH",source_ticker=None,cash_amount=0):
    result=_engine(holdings,ticker,operation,amount,funding_mode,source_ticker,cash_amount)
    if "error" not in result:
        result["funding_mode"]=result["funding"]
    return result
