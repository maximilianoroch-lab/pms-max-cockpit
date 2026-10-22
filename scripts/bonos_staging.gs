/**
 * PMS Bersoch: observación experimental de bonos, NO fuente para valuación.
 * Data912 se identifica como servicio educativo/no necesariamente en tiempo real.
 * El campo c no incluye moneda, unidad ni fecha mercado, por lo que no se llena
 * "Cierre ARS x 100 VN" ni "Valor USD ref." con datos sin validar.
 * Instalación voluntaria en Apps Script; no instala triggers ni modifica posiciones.
 */
const PMS_BOND_SYMBOLS = ['AN29','AO28','AO29','GD35','GD38','GD41'];
const PMS_BOND_SOURCE = 'https://data912.com/live/arg_bonds';

function actualizarBonos() {
  const ss=SpreadsheetApp.getActive();
  const sh=ss.getSheetByName('bonos_auto_v2');
  if (!sh) throw new Error('No existe bonos_auto_v2');
  const response=UrlFetchApp.fetch(PMS_BOND_SOURCE,{muteHttpExceptions:true,followRedirects:true});
  if (response.getResponseCode()!==200)
    throw new Error('HTTP '+response.getResponseCode()+': sin cambios');
  const payload=JSON.parse(response.getContentText());
  if (!Array.isArray(payload)) throw new Error('Esquema no reconocido; sin cambios');
  const snapshots=new Map();
  payload.forEach(item=>{
    const t=String(item.symbol||'').toUpperCase().trim(),v=Number(item.c);
    if (PMS_BOND_SYMBOLS.includes(t)&&Number.isFinite(v)&&v>0)
      snapshots.set(t,v);
  });
  if (!snapshots.size) throw new Error('Ningún símbolo esperado; sin cambios');
  // Conservar los valores anteriores, incluso los ya validados manualmente.
  // Nunca sustituir precios / fechas de mercado por el snapshot experimental.
  const existing=sh.getLastRow()>1?sh.getRange(2,1,sh.getLastRow()-1,8).getValues():[];
  const byTicker=new Map();
  existing.forEach((r,i)=>{
    const ticker=String(r[1]||'').toUpperCase().trim();
    if (PMS_BOND_SYMBOLS.includes(ticker)&&!byTicker.has(ticker))byTicker.set(ticker,i+2);
  });
  const now=new Date(), outcome=[];
  PMS_BOND_SYMBOLS.forEach(t=>{
    if (!snapshots.has(t)){outcome.push({ticker:t,status:'SIN_DATO_SIN_CAMBIOS'});return;}
    // Solo escribimos metadatos de diagnóstico G:F cuando no existe registro,
    // y no pisamos filas con información anterior.
    // Para auditoría completa, log a Apps Script: sin escribir cifras no certificadas.
    const v=snapshots.get(t);
    console.log(JSON.stringify({ticker:t,rawClose:v,source:PMS_BOND_SOURCE,queriedAt:now.toISOString(),
      status:'SIN_VALIDAR_MONEDA_UNIDAD_FECHA_MERCADO'}));
    outcome.push({ticker:t,status:'CONSULTADO_NO_APLICADO',precioCrudo:v});
  });
  return outcome;
}
