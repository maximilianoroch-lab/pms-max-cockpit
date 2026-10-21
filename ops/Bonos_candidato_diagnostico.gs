/**
 * PMS v2 — Bonos.gs (candidato, NO instalado).
 * IOL publica precios ARS por 100 VN. Nunca promover cotizaciones viejas.
 * La automatización no modifica tenencias ni valores manuales directamente:
 * sólo llena bonos_auto_v2 para que el motor seleccione una fuente válida.
 */
const BONOS_PMS = ['AN29','AO28','AO29','GD35','GD38','GD41'];
const MAX_ANTIGUEDAD_BONOS_DIAS = 4;

function actualizarBonos() {
  const sh = SpreadsheetApp.getActive().getSheetByName('bonos_auto_v2');
  if (!sh) throw new Error('Falta hoja bonos_auto_v2');
  const errores = [];
  BONOS_PMS.forEach(ticker => {
    try {
      const q = leerCierreIOL_(ticker);
      if (!q) { errores.push(ticker + ': fuente sin dato verificable'); return; }
      if (!cotizacionBonoVigente_(q)) {
        errores.push(ticker + ': cierre histórico ' + Utilities.formatDate(q.fecha,'America/Argentina/Buenos_Aires','dd/MM/yyyy'));
        return;
      }
      upsertBono_(sh, ticker, q);
    } catch (e) { errores.push(ticker + ': ' + e.message); }
  });
  if (errores.length) console.warn('Bonos sin actualización: ' + errores.join(' | '));
  return {actualizados: BONOS_PMS.length - errores.length, pendientes: errores};
}

function cotizacionBonoVigente_(q) {
  if (!(q && q.fecha instanceof Date && isFinite(q.precio) && q.precio > 0)) return false;
  const now = new Date();
  const ms = now.getTime() - q.fecha.getTime();
  return ms >= 0 && ms <= MAX_ANTIGUEDAD_BONOS_DIAS * 86400000;
}

function leerCierreIOL_(ticker) {
  if (!BONOS_PMS.includes(ticker)) throw new Error('Ticker no habilitado');
  const url = 'https://iol.invertironline.com/Titulo/DatosHistoricos?mercado=BCBA&simbolo=' + encodeURIComponent(ticker);
  const r = UrlFetchApp.fetch(url, {muteHttpExceptions: true,followRedirects: true,headers: {'User-Agent':'Mozilla/5.0'}});
  if (r.getResponseCode() !== 200) throw new Error('HTTP '+r.getResponseCode());
  const html = r.getContentText();
  if (!/Cierre/i.test(html)) throw new Error('Sin tabla de cierres');
  const trs = html.match(/<tr\b[\s\S]*?<\/tr>/gi) || [];
  let best = null;
  trs.forEach(tr => {
    const clean = tr.replace(/<script[\s\S]*?<\/script>/gi,' ')
      .replace(/<style[\s\S]*?<\/style>/gi,' ')
      .replace(/<[^>]+>/g,' ').replace(/&nbsp;|&#160;/gi,' ').replace(/\s+/g,' ').trim();
    const dm = clean.match(/\b(\d{2})\/(\d{2})\/(\d{4})\b/);
    if (!dm) return;
    // IOL historical dates are US-style MM/DD/YYYY.
    const month = Number(dm[1]), day = Number(dm[2]), year = Number(dm[3]);
    const fecha = new Date(year,month-1,day);
    if (fecha.getFullYear() !== year || fecha.getMonth() !== month-1 || fecha.getDate() !== day) return;
    const rest = clean.slice(clean.indexOf(dm[0]) + dm[0].length);
    const cols = rest.match(/-?\d[\d,.]*/g) || [];
    if (cols.length < 4) return;
    const precio = Number(cols[3].replace(/,/g,''));
    if (!(precio > 0 && precio < 1000000)) return;
    if (!best || fecha > best.fecha) best = {fecha, precio, fuente:'IOL histórico público'};
  });
  return best;
}

function upsertBono_(sh,ticker,q) {
  const end = Math.max(sh.getLastRow(),2);
  const vals = sh.getRange(2,1,end-1,3).getValues();
  const ix = vals.findIndex(r=>String(r[1]).toUpperCase()===ticker);
  const row = ix>=0?ix+2:sh.getLastRow()+1;
  if (ix>=0 && vals[ix][0] instanceof Date && vals[ix][0]>q.fecha) return;
  sh.getRange(row,1,1,7).setValues([[q.fecha,ticker,q.precio,q.fuente,'OK',new Date(),'Cierre ARS por 100 VN; precio validado al consultar']]);
  sh.getRange(row,1).setNumberFormat('dd/mm/yyyy');
  sh.getRange(row,6).setNumberFormat('dd/mm/yyyy hh:mm');
}

/**
 * Diagnóstico de sólo lectura: nunca actualiza bonos_auto_v2.
 * Requiere autorización de UrlFetchApp pero no escribe en Sheets.
 */
function diagnosticoBonosPMS() {
  const resultado = [];
  BONOS_PMS.forEach(ticker => {
    try {
      const q = leerCierreIOL_(ticker);
      const item = {
        ticker: ticker,
        fecha: q && q.fecha ? Utilities.formatDate(q.fecha, 'America/Argentina/Buenos_Aires', 'yyyy-MM-dd') : null,
        precioARS100VN: q ? q.precio : null,
        fuente: q ? q.fuente : null,
        vigente: cotizacionBonoVigente_(q)
      };
      resultado.push(item);
      Logger.log(JSON.stringify(item));
    } catch (e) {
      const item = {ticker:ticker,error:String(e && e.message || e)};
      resultado.push(item);
      Logger.log(JSON.stringify(item));
    }
  });
  return resultado;
}
