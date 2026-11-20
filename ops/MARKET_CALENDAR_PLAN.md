# Calendar for the PMS Bersoch freshness monitor — staged, NOT ACTIVE

The monitor historically treats all Monday–Friday dates as trading sessions. This leads to false positive gaps on exchange holidays.

This change adds optional `PMS_MARKET_HOLIDAYS_CSV` support. **By default, behavior stays unchanged**. Only explicitly vetted holiday dates may be added; no speculative dates, automatic inferred holidays or external scraping.

CSV format:

```csv
date,source
YYYY-MM-DD,official exchange notice reference
```

After manually verifying holidays, store the CSV in the repository or another controlled path and set the workflow environment variable to point to it. `source` should identify an exchange calendar or notice, not a guessed weekday rule.

Tests cover skip of a holiday, omission from missing-day counts, and invalid calendar input.

## Deployment gates

1. Independently verify a full year of relevant Argentine exchange holidays and the treatment of foreign trading days.
2. Confirm whether the monitor should follow BYMA sessions, US exchange sessions, or a per-ticker market calendar. The current optional calendar represents **one explicit portfolio-level session convention**.
3. Add a source-documented CSV and set `PMS_MARKET_HOLIDAYS_CSV` in Actions only after approval.
4. Re-check 12–13 November historical gaps; no historical snapshot backfill is performed by this change.

This change is read-only and does not write to Sheets, install Apps Script or alter historical valuations.


## Calendario oficial preparado (15/11/2026)

Se agregó `ops/byma_no_trading_2026.csv` con las fechas **sin negociación** identificadas en el [calendario oficial BYMA](https://www.byma.com.ar/mercado/calendario-bursatil). La fuente clasifica como **jornada con negociación pero sin liquidación** los días 23/03, 10/07, 06/11, 07/12 y 24/12; estas jornadas **no** se excluyen del monitor de cotizaciones. Los días 09/11 y 10/11 sí figuran como suspensión de actividad. La lista puede actualizarse por disposición oficial; revisar antes de activar.

**No habilitar automáticamente el calendario** sin definir la regla de cartera multibolsa: los activos internacionales pudieron negociar mientras BYMA estaba cerrado. Esta tabla representa únicamente el calendario **BYMA**, no NYSE/Nasdaq/Binance/A3. Los cierres de 12 y 13/11 son ruedas a controlar y siguen pendientes.

Para una futura activación del monitor de **BYMA**, establecer `PMS_MARKET_HOLIDAYS_CSV=ops/byma_no_trading_2026.csv` en el job correspondiente luego de autorizar ese criterio. En el borrador actual se mantiene desactivado. La captura V3 del otro PR todavía usa otra hoja de feriados y necesita reconciliar su calendario con el de este monitor antes de instalar disparadores.
