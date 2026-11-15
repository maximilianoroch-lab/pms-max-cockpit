const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const source=fs.readFileSync('ops/Bonos_Diagnostico_SoloLectura_V2.gs','utf8');
let writes=0,fetches=0;
const context={
  SpreadsheetApp:{getActive(){writes++;throw Error('No access to Sheets allowed')}},
  UrlFetchApp:{fetch(url){fetches++;return {
    getResponseCode(){return 200},
    getContentText(){return '<table><tr><td>11/12/2026</td><td>5000</td></tr></table>'}
  }}},
  Utilities:{formatDate(){return '2026-11-15 08:00:00'}},
  Date
};
vm.createContext(context);
vm.runInContext(source,context);
const results=context.diagnosticoBonosSoloLecturaV2();
assert.equal(results.length,6);
assert.equal(fetches,6);
assert.equal(writes,0);
assert.ok(results.every(x=>x.priceUsableForValuation===false && x.certificate===false));
assert.ok(results.every(x=>x.verifiedQuote===null && x.status==='HTML_CON_FECHA_SIN_CERTIFICAR'));
const failures={...context,UrlFetchApp:{fetch(){throw Error('blocked')}}};
vm.createContext(failures);
vm.runInContext(source,failures);
const fallback=failures.diagnosticoBonosSoloLecturaV2();
assert.equal(fallback.length,6);
assert.ok(fallback.every(x=>x.status==='ERROR_FUENTE' && x.priceUsableForValuation===false));
console.log('PASS: six bonds diagnosed read-only with error handling and no prices promoted');
