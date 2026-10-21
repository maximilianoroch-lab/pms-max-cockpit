/**
 * PMS · IOL public historical quotes — READ ONLY diagnostic.
 * Does not write holdings, bonos_auto_v2, or register triggers.
 */
const IOL_BONOS_DIAG = ['AN29','AO28','AO29','GD35','GD38','GD41'];

function diagnosticoIOLPublicoSeguro() {
  return IOL_BONOS_DIAG.map(ticker => {
    try {
      const q = leerCierreIOLSeguro_(ticker);
      const out = {ticker, ...q};
      Logger.log(JSON.stringify(out));
      return out;
    } catch (e) {
      const out = {ticker, error:String(e.message||e)};
      Logger.log(JSON.stringify(out));
      return out;
    }
  });
}

function leerCierreIOLSeguro_(ticker) {
  if (!IOL_BONOS_DIAG.includes(ticker)) throw Error('Especie no autorizada');
  const url = 'https://iol.invertironline.com/Titulo/DatosHistoricos?mercado=BCBA&simbolo='+encodeURIComponent(ticker);
  const r = UrlFetchApp.fetch(url,{muteHttpExceptions:true,followRedirects:true,headers:{'User-Agent':'Mozilla/5.0'}});
  if (r.getResponseCode()!==200) throw Error('IOL HTTP '+r.getResponseCode());
  const html = r.getContentText();
  // Parse exactly the reported tabular sequence: Fecha, Apertura, Maximo, Minimo, Cierre.
  // Do not infer price denomination from magnitude.
  const rows = html.match(/<tr\\b[\\s\\S]*?<\\/tr>/gi)||[];
  let best=null;
  for(const tr of rows) {
    const t=tr.replace(/<script\\b[\\s\\S]*?<\\/script>/gi,' ').replace(/<style\\b[\\s\\S]*?<\\/style>/gi,' ').replace(/<[^>]+>/g,' ').replace(/&nbsp;|&#160;/gi,' ').replace(/\\s+/g,' ').trim();
    const m=t.match(/\\b(\\d{2})\\/(\\d{2})\\/(\\d{4})\\b/);
    if(!m)continue;
    const year=+m[3],month=+m[1],day=+m[2];
    const d=new Date(year,month-1,day);
    if(d.getFullYear()!==year||d.getMonth()!==month-1||d.getDate()!==day)continue;
    const cols=(t.slice(t.indexOf(m[0])+m[0].length).match(/-?\\d[\\d,.]*/g)||[]);
    if(cols.length<7)continue; // OHLC + adjusted close + volumes
    const parse=x=>Number(x.replace(/,/g,''));
    const [open,high,low,close,adjusted]=cols.slice(0,5).map(parse);
    if(![open,high,low,close,adjusted].every(x=>Number.isFinite(x)&&x>0))continue;
    if(low>high||close<low*0.95||close>high*1.05)continue;
    if(!best||d>best.date)best={date:d,close,open,high,low};
  }
  if(!best)throw Error('Sin fila historica verificable en HTML (puede requerir JS)');
  const d=best.date;
  const marketDate=Utilities.formatDate(d,'America/Argentina/Buenos_Aires','yyyy-MM-dd');
  const ageDays=Math.floor((Date.now()-d.getTime())/86400000);
  return {marketDate,closeRaw:best.close,currency:'ARS (pendiente validar)',unit:'NO VERIFICADA',ageDays,eligibleForValuation:false,source:url,
    warning:'Solo diagnostico: confirmar unidad de cierre, especie y frescura antes de escritura'};
}
