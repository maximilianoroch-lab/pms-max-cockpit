"""Candidate ETF materiality and source-freshness policy, read-only and opt-in.

No price feeds, holdings distribution or investment recommendations.
This module does not trigger an alert and is not connected to the live UI.
"""
import datetime as dt
import math
import pandas as pd


def evaluate_etf_materiality(exposures, coverage, source_metadata,
                             portfolio_total_usd, as_of,
                             materiality_fraction=0.01,
                             uncovered_fraction=0.02,
                             max_source_age_days=30):
    """Return partial-exposure flags with explicit, testable thresholds.

    exposures: columns Activo, Directo USD, ETF parcial USD, Total identificado USD
    coverage: columns ETF, Cobertura, Sin desagregar, Valor sin desagregar USD
    source_metadata: columns ETF, Fecha
    All metrics are informational estimates, not trade signals.
    """
    total = float(portfolio_total_usd)
    if not math.isfinite(total) or total <= 0:
        raise ValueError("Patrimonio total USD debe ser positivo y finito")
    if not (0 < materiality_fraction <= 1) or not (0 < uncovered_fraction <= 1):
        raise ValueError("Umbral porcentual inválido")
    if not isinstance(max_source_age_days, int) or max_source_age_days < 0:
        raise ValueError("Antigüedad máxima inválida")
    day = dt.date.fromisoformat(str(as_of))
    if exposures is None or coverage is None or source_metadata is None:
        raise ValueError("Sin tablas de procedencia no se certifica riesgo ETF")
    required_exposure = {"Activo", "Directo USD", "ETF parcial USD", "Total identificado USD"}
    required_coverage = {"ETF", "Cobertura", "Sin desagregar", "Valor sin desagregar USD"}
    if not required_exposure.issubset(exposures) or not required_coverage.issubset(coverage) or not {"ETF", "Fecha"}.issubset(source_metadata):
        raise ValueError("Columnas de cobertura, exposición o fechas incompletas")
    findings = []
    threshold = total * materiality_fraction
    for _, row in exposures.iterrows():
        identified = float(row["Total identificado USD"])
        indirect = float(row["ETF parcial USD"])
        if not all(math.isfinite(v) and v >= 0 for v in (identified, indirect)):
            raise ValueError("Exposición identificada inválida")
        if identified >= threshold:
            findings.append({"tipo": "EMISOR_IDENTIFICADO_PARCIAL",
                             "activo": str(row["Activo"]),
                             "valor_usd": round(identified, 2),
                             "porcentaje_cartera": round(100 * identified / total, 3),
                             "accion": "Revisar concentración; resto de ETF no desagregado"})
    dated = {}
    for _, row in source_metadata.iterrows():
        etf = str(row["ETF"]).strip().upper()
        date = dt.date.fromisoformat(str(row["Fecha"]))
        if etf in dated and dated[etf] != date:
            raise ValueError("Fuente ETF con fechas mixtas")
        if date > day:
            raise ValueError("Fuente ETF fechada en el futuro")
        dated[etf] = date
    for _, row in coverage.iterrows():
        etf = str(row["ETF"]).strip().upper()
        uncovered = float(row["Valor sin desagregar USD"])
        fraction = float(row["Sin desagregar"])
        if not all(math.isfinite(v) for v in (uncovered, fraction)) or not (0 <= fraction <= 1) or uncovered < 0:
            raise ValueError("Cobertura ETF inválida")
        if uncovered / total >= uncovered_fraction:
            findings.append({"tipo": "FRACCION_ETF_NO_DESAGREGADA_MATERIAL",
                             "activo": etf, "valor_usd": round(uncovered, 2),
                             "porcentaje_cartera": round(100 * uncovered / total, 3),
                             "accion": "No inferir sector/emisor para la fracción sin datos"})
        date = dated.get(etf)
        if date is None:
            findings.append({"tipo": "ETF_SIN_FECHA_FUENTE", "activo": etf,
                             "accion": "No tratar como composición actual"})
        elif (day - date).days > max_source_age_days:
            findings.append({"tipo": "ETF_COMPOSICION_ANTIGUA", "activo": etf,
                             "fecha": date.isoformat(), "dias": (day - date).days,
                             "accion": "Actualizar fuente antes de análisis de concentración"})
    return {"estado": "PROPUESTA_NO_ACTIVADA", "fecha_revision": day.isoformat(),
            "umbral_materialidad_pct": materiality_fraction * 100,
            "umbral_sin_desagregar_pct": uncovered_fraction * 100,
            "antiguedad_maxima_dias": max_source_age_days,
            "no_es_recomendacion": True, "hallazgos": findings}
