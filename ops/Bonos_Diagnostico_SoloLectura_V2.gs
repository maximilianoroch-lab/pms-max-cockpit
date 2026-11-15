/** PMS Bersoch — bond public-source diagnostics only. NOT INSTALLED.
 * Quotes from HTML are only candidates. No guarantee currency, price unit,
 * settlement method, freshness or instrument identity. NEVER writes Sheets.
 */
const PMS_BOND_TICKERS_V2 = Object.freeze(['AN29','AO28','AO29','GD35','GD38','GD41']);
function pmsBondReadOnlyDiagnose_() {
  const results = [];
  PMS_BOND_TICKERS_V2.forEach(ticker => {
    const url = 'https://iol.invertironline.com/Titulo/DatosHistoricos?mercado=BCBA&simbolo='+encodeURIComponent(ticker);
    try {
      const response=UrlFetchApp.fetch(url,{
        muteHttpExceptions:true,followRedirects:true,
        headers:{'User-Agent':'Mozilla/5.0 PMS-Bond-Diagnostic/2.0'}
      });
      const code=response.getResponseCode();
      if(code!==200)throw new Error('Fuente HTTP '+code);
      const html=String(response.getContentText()||'');
      const hasDate=/<tr\b/i.test(html)&&/\b\d{2}\/\d{2}\/\d{4}\b/.test(html);
      const item={
        ticker,url,status:hasDate?'HTML_CON_FECHA_SIN_CERTIFICAR':'HTML_SIN_TABLA_FECHADA',
        certificate:false,priceUsableForValuation:false,
        unit:'SIN_VALIDAR',currency:'SIN_VALIDAR',
        verifiedQuote:null,
        inspectedAt:Utilities.formatDate(new Date(),'America/Argentina/Buenos_Aires','yyyy-MM-dd HH:mm:ss')
      };
      results.push(item);
    } catch(error) {
      results.push({ticker,url,status:'ERROR_FUENTE',error:String(error?.message||error),
                    certificate:false,priceUsableForValuation:false});
    }
  });
  return results;
}
/** Diagnostic does not write holdings, quotes, historical series or install triggers. */
function diagnosticoBonosSoloLecturaV2() {
  return pmsBondReadOnlyDiagnose_();
}
