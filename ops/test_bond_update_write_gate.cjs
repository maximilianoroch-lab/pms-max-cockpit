const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const code=fs.readFileSync('ops/Bonos_candidato_diagnostico.gs','utf8');
let sheetReads=0;
const context={
  SpreadsheetApp:{getActive(){sheetReads++;throw Error('production access forbidden')}},
  UrlFetchApp:{fetch(){throw Error('external access forbidden')}},
};
vm.createContext(context);
vm.runInContext(code,context);
assert.throws(()=>context.actualizarBonos(),/BLOQUEADO/);
assert.equal(sheetReads,0);
console.log('PASS: updater cannot write or touch Sheets while bond quote unit/market source is uncertified');
