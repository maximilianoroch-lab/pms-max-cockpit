/** PREPARED ONLY. No installer. Personal PMS only; does not repair history.
 * Approval must name the new handler and set PMS_PERSONAL_SPREADSHEET_ID
 * in Script Properties after verifying the bound spreadsheet. No IDs in code.
 * This preserves legacy layout; it does NOT certify market-close freshness.
 */
function pmsLegacySnapshotSafe() {
  const tz = 'America/Argentina/Buenos_Aires';
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const expectedId = PropertiesService.getScriptProperties().getProperty('PMS_PERSONAL_SPREADSHEET_ID');
  if (!expectedId || !ss || ss.getId() !== expectedId) throw new Error('Base personal no verificada');
  const lock = LockService.getDocumentLock();
  if (!lock || !lock.tryLock(20000)) throw new Error('No se obtuvo bloqueo documental');
  try {
    const now = new Date();
    const day = Utilities.formatDate(now, tz, 'yyyy-MM-dd');
    const weekday = new Date(day + 'T12:00:00Z').getUTCDay();
    if (weekday === 0 || weekday === 6) return {status:'SKIP_WEEKEND'};
    if (Number(Utilities.formatDate(now, tz, 'HH')) < 17) return {status:'SKIP_BEFORE_CLOSE'};
    const names = ['posiciones_v2','historial','historial_precios','tc_diario','control_integridad_v2'];
    const sheets = names.map(n => ss.getSheetByName(n));
    if (sheets.some(s => !s)) throw new Error('Faltan hojas requeridas');
    const [pos,hist,hp,mep,ctl] = sheets;
    SpreadsheetApp.flush();
    const number = v => typeof v === 'number' && Number.isFinite(v);
    const dateKey = v => v instanceof Date && Number.isFinite(v.getTime())
      ? Utilities.formatDate(v,tz,'yyyy-MM-dd') : String(v == null ? '' : v).trim();
    const read = (sh,c,w) => sh.getLastRow() > 1
      ? sh.getRange(2,c,sh.getLastRow()-1,w).getValues() : [];
    const schema = (sh,headers) => {
      const actual = sh.getRange(1,1,1,headers.length).getValues()[0];
      if (headers.some((h,i) => actual[i] !== h)) throw new Error('Esquema inesperado: ' + sh.getName());
    };
    schema(hist,['Foto','Fecha','Fuente','Valor total USD','Nota']);
    schema(hp,['Fecha','Ticker','Tipo','Precio','Moneda','Precio USD','Cantidad','Valor USD','Fuente','Snapshot']);
    const snap = 'SNAP-' + day.replace(/-/g,'');
    const prior = read(hp,1,10).filter(r => String(r[9]) === snap || dateKey(r[0]) === day);
    const heads = read(hist,1,5).filter(r => dateKey(r[1]) === day);
    const expectedCount = ctl.getRange('B2').getValue();
    if (!Number.isInteger(expectedCount) || expectedCount < 1) throw new Error('Universo esperado inválido');
    if (prior.length || heads.length) {
      const tickers = prior.map(r => String(r[1]).trim().toUpperCase());
      const valid = heads.length === 1 && prior.length === expectedCount &&
        new Set(tickers).size === expectedCount && tickers.every(Boolean) &&
        prior.every(r => String(r[9]) === snap && dateKey(r[0]) === day &&
          number(r[6]) && r[6] >= 0 && number(r[7]) && r[7] >= 0 && !(r[6] > 0 && r[7] <= 0)) &&
        number(heads[0][3]) && Math.abs(prior.reduce((s,r)=>s+r[7],0)-heads[0][3]) < 0.01;
      if (!valid) throw new Error('Cierre previo parcial o incongruente: revisión manual, sin reparación automática');
      return {status:'ALREADY_COMPLETE',snap};
    }
    const controls = ctl.getRange('A2:D6').getDisplayValues();
    if (ctl.getRange('D6').getDisplayValue() !== 'APTO' ||
        controls.some(r => r[0] !== 'Snapshot apto' && r[3] !== 'OK')) throw new Error('Integridad no aprobada');
    if (!read(mep,1,3).some(r => r[0] instanceof Date && dateKey(r[0]) === day && number(r[2]) && r[2] > 0)) {
      throw new Error('MEP sin dato válido de hoy');
    }
    const rows = read(pos,1,16).filter(r => r[0]);
    const tickers = rows.map(r => String(r[0]).trim().toUpperCase());
    if (rows.length !== expectedCount || new Set(tickers).size !== expectedCount || !tickers.every(Boolean)) {
      throw new Error('Universo de posiciones inconsistente');
    }
    if (rows.some(r => !number(r[2]) || !number(r[6]) || r[2] < 0 || r[6] < 0 || (r[2] > 0 && r[6] <= 0))) {
      throw new Error('Cantidad o valoración inválida');
    }
    const total = rows.reduce((s,r)=>s+r[6],0);
    if (!Number.isFinite(total) || total < 1000) throw new Error('Total fuera de control');
    const stamp = new Date(day+'T15:00:00Z');
    const out = rows.map(r => [stamp,String(r[0]).trim(),r[9],r[4]||'',r[5]||'',r[2]?r[6]/r[2]:'',r[2],r[6],r[15]||'',snap]);
    // Non-transactional: any uncertain write requires inspection, never auto-repair.
    try {
      hp.getRange(hp.getLastRow()+1,1,out.length,10).setValues(out);
      hist.getRange(hist.getLastRow()+1,1,1,5).setValues([['Foto automática '+day,stamp,'Automático PMS',total,
        'Cierre pendiente de conciliación de aportes/retiros; frescura por ticker no certificada']]);
      SpreadsheetApp.flush();
    } catch (error) {
      throw new Error('Escritura de cierre no confirmada; inspeccionar ambas hojas antes de reintentar: '+error.message);
    }
    return {status:'WRITTEN_UNVERIFIED',snap,tickers:out.length,total};
  } finally { lock.releaseLock(); }
}
