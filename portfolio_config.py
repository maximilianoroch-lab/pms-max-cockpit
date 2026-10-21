
PORTFOLIO = {
    "id": "pms_max",
    "display_name": "PMS Bersoch",
    "sheet_id": "18qu9LXo55qQZq4oEAq42u_DKaI7e9lZL_PkfUZiu0T0",
    "base_currency": "USD",
    "app_name": "PMS Bersoch · Cockpit",
    "privacy_scope": "private_instance",
    "rules": {
        "primary_wealth_excludes_crypto": True,
        "crypto_separate": True,
        "fut_analytics_class": "Crypto",
        "gld_class": "Oro",
        "gld_type": "ETF",
        "global_direct": ["MELI", "VIST", "GLOB"],
        "argentina_direct": ["YPF", "YPFD", "GGAL"],
        "manual_required": ["FUT", "CASH", "GALILEO", "SCHROD"],
        "forbidden_performance_metrics": ["TWR", "XIRR", "Modified Dietz"],
        "weekend_last_valid_ok": True,
    }
}
