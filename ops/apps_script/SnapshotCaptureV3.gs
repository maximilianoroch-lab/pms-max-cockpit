/**
 * PMS Bersoch — capture candidate V3 (NOT INSTALLED).
 * Stores 11:00, 14:00 and 17:00 observations separately, append-only.
 * Does NOT certify market close or backfill missing historical valuations.
 * Installation requires owner approval and Google Apps Script permissions.
 */
const PMS_V3 = Object.freeze({
  tz: 'America/Argentina/Buenos_Aires',
  observations: 'observaciones_intradiarias_v3',
  holidays: 'feriados_mercado_v3',
  expectedSlots: ['11:00','14:00','17:00']
});

function pmsV3_localDay_(d) {
  return Utilities.formatDate(d, PMS_V3.tz, 'yyyy-MM-dd');
}
function pmsV3_localHour_(d) {
  return Utilities.formatDate(d, PMS_V3.tz, 'HH:mm:ss');
}
function pmsV3_bymaOpen_(now, ss) {
  const sh = ss.getSheetByName(PMS_V3.holidays);
  if (!sh) throw new Error('Falta calendario de feriados de mercado: instalación incompleta');
  const dates = sh.getLastRow() > 1
    ? sh.getRange(2,1,sh.getLastRow()-1,1).getDisplayValues().flat() : [];
  if (!dates.length) throw new Error('Calendario de feriados vacío: validar antes de habilitar capturas');
  return !dates.some(x => String(x).trim() === pmsV3_localDay_(now));
}
function pmsV3_capture_(slot) {
  if (!PMS_V3.expectedSlots.includes(slot)) throw new Error('Horario no permitido');
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const now = new Date();
  // Apps Script clock triggers can run at any minute within their chosen hour.
  // Never mislabel an execution outside its designated local hour.
  if (!pmsV3_localHour_(now).startsWith(slot.slice(0,2) + ':')) {
    throw new Error('Captura fuera de franja ' + slot + ': ' + pmsV3_localHour_(now));
  }
  const weekDay = Number(Utilities.formatDate(now, PMS_V3.tz, 'u'));
  if (weekDay >= 6) return {status:'SKIP_WEEKEND'};
  // BYMA closure does not imply all USD-listed or crypto assets are closed.
  // Preserve a portfolio observation with an explicit provenance warning.
  const bymaOpen = pmsV3_bymaOpen_(now, ss);
  const lock = LockService.getDocumentLock();
  if (!lock || !lock.tryLock(20000)) throw new Error('No se obtuvo bloqueo documental');
  try {
    const target = ss.getSheetByName(PMS_V3.observations);
    const pos = ss.getSheetByName('posiciones_v2');
    const ctl = ss.getSheetByName('control_integridad_v2');
    if (!target || !pos || !ctl) throw new Error('Faltan hojas requeridas');
    if (ctl.getRange('D6').getDisplayValue().trim().toUpperCase() !== 'APTO') {
      throw new Error('Integridad no apta: se rechaza la captura');
    }
    const day = pmsV3_localDay_(now);
    const snapshotId = 'OBS-' + day.replace(/-/g,'') + '-' + slot.replace(':','');
    const n = pos.getLastRow();
    if (n < 2) throw new Error('No existen posiciones');
    const rows = pos.getRange(2,1,n-1,16).getValues().filter(r => r[0]);
    const expected = Number(ctl.getRange('B2').getValue());
    if (!Number.isFinite(expected) || expected !== rows.length) {
      throw new Error('Cantidad de posiciones inconsistente');
    }
    const invalid = rows.filter(r => !Number.isFinite(Number(r[2])) ||
      Number(r[2]) < 0 || !Number.isFinite(Number(r[6])) ||
      Number(r[6]) < 0 || (Number(r[2]) > 0 && Number(r[6]) <= 0));
    if (invalid.length) throw new Error('Posiciones sin valor válido: ' +
      invalid.map(r=>r[0]).join(','));
    const tickers = rows.map(r => String(r[0]).trim().toUpperCase());
    if (tickers.some(t => !t) || new Set(tickers).size !== tickers.length) {
      throw new Error('Tickers duplicados o vacíos: captura rechazada');
    }
    // Reject incomplete earlier writes rather than silently marking them as done.
    const last = target.getLastRow();
    if (last > 1) {
      const existing = target.getRange(2,1,last-1,6).getDisplayValues();
      const prior = existing.filter(r => r[0] === snapshotId);
      if (prior.length) {
        const presentTickers = new Set(prior.map(r => String(r[5]).trim()));
        const expectedTickers = new Set(rows.map(r => String(r[0]).trim()));
        if (prior.length !== rows.length || presentTickers.size !== expectedTickers.size ||
            [...expectedTickers].some(t => !presentTickers.has(t))) {
          throw new Error('Captura anterior incompleta o incongruente: ' + snapshotId +
            '. Revisar antes de reintentar; no se sobrescribe.');
        }
        return {status:'ALREADY_CAPTURED',snapshotId};
      }
    }
    // Preserve source & displayed value; do not infer an exchange close.
    const marketStatus = bymaOpen ? 'OBSERVADO_NO_CERTIFICADO' :
      'OBSERVADO_BYMA_CERRADO_NO_CERTIFICADO';
    const collectedAt = pmsV3_localHour_(now);
    const out = rows.map(r => [
      snapshotId,day,slot,collectedAt,marketStatus,
      String(r[0]),Number(r[2]),Number(r[6]),String(r[5]||''),
      String(r[15]||''),String(r[8]||''),'Sin prueba de frescura por ticker'
    ]);
    const first = Math.max(target.getLastRow()+1,2);
    target.getRange(first,1,out.length,12).setValues(out);
    SpreadsheetApp.flush();
    return {status:'CAPTURED_UNVERIFIED',bymaOpen,snapshotId,positions:rows.length,
      totalUsd:rows.reduce((s,r)=>s+Number(r[6]),0)};
  } finally { lock.releaseLock(); }
}
function pmsV3_1100() { return pmsV3_capture_('11:00'); }
function pmsV3_1400() { return pmsV3_capture_('14:00'); }
function pmsV3_1700() { return pmsV3_capture_('17:00'); }

/**
 * Intentionally no automatic trigger installer.
 * Owner must inspect calendar, approve installation and run controlled test.
 * Apps Script clock events are approximate, not guaranteed exact minute.
 * If any data source is stale, observations remain UNVERIFIED.
 */
