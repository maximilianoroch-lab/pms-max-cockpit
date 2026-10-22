/**
 * PMS Bersoch - módulo de INGESTA de bonos (NO activo).
 * Copiar a Apps Script ligado a la hoja, revisar/autorizar e instalar solo tras prueba.
 * Nunca actualiza posiciones ni precios validados. Fuente experimental.
 */
const PMS_BOND_SYMBOLS = ['AN29','AO28','AO29','GD35','GD38','GD41'];
const PMS_BOND_SOURCE = 'https://data912.com/live/arg_bonds';

function actualizarBonos() {
  const sheet = SpreadsheetApp.getActive().getSheetByName('bonos_auto_v2');
  if (!sheet) throw new Error('Falta bonos_auto_v2');
  const response = UrlFetchApp.fetch(PMS_BOND_SOURCE, {muteHttpExceptions:true,followRedirects:true});
  if (response.getResponseCode() !== 200) {
    throw new Error('Proveedor no disponible (HTTP '+response.getResponseCode()+'); no se modifica la hoja.');
  }
  const data = JSON.parse(response.getContentText());
  if (!Array.isArray(data)) throw new Error('Respuesta inválida: esperado arreglo; no se modifica la hoja');
  const bySymbol = {};
  data.forEach(x => {
    const symbol = String(x.symbol || '').toUpperCase().trim();
    const price = Number(x.c);
    if (PMS_BOND_SYMBOLS.includes(symbol) && Number.isFinite(price) && price>0) {
      bySymbol[symbol] = price;
    }
  });
  const now = new Date();
  const rows = PMS_BOND_SYMBOLS.map(symbol => {
    const found = Object.prototype.hasOwnProperty.call(bySymbol,symbol);
    return ['',symbol,found ? bySymbol[symbol] : '',
      'Data912 /live/arg_bonds',
      found ? 'SIN_VALIDAR_UNIDAD' : 'SIN_DATO',
      now,
      found ? 'Precio crudo. Sin fecha de mercado ni unidad confirmadas. NO USAR PARA VALUAR.' : 'Conservar cotización previa validada en el circuito productivo.',
      ''];
  });
  // Escritura de staging, A:H. No hay fórmulas productivas conectadas a esta hoja.
  // No afirmar que la fecha de consulta es fecha de mercado.
  sheet.getRange(2,1,rows.length,8).setValues(rows);
  sheet.getRange(2,6,rows.length,1).setNumberFormat('dd/mm/yyyy hh:mm');
  return rows.map(r => ({ticker:r[1],estado:r[4]}));
}
