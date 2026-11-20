const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const source = fs.readFileSync(require('node:path').join(__dirname,'LegacySnapshotSafe.gs'),'utf8');
function fixture(options={}) {
  const D = Date;
  class Clock extends D { constructor(...a) {super(...(a.length?a:['2026-11-18T21:05:00Z']));} }
  const stamp=new Clock('2026-11-18T15:00:00Z');
  let released=0, writes=0, fail=options.fail;
  const rows={
    posiciones_v2:[[],['AAA','',2,'','','USD',1200,'','','share','','','','','','quote'],['BBB','',3,'','','USD',1800,'','','share','','','','','','quote']],
    historial:[['Foto','Fecha','Fuente','Valor total USD','Nota']],
    historial_precios:[['Fecha','Ticker','Tipo','Precio','Moneda','Precio USD','Cantidad','Valor USD','Fuente','Snapshot']],
    tc_diario:[[],[stamp,0,1500]],
    control_integridad_v2:[[]]
  };
  if(options.blank) rows.posiciones_v2[1][2]='';
  if(options.zero) rows.posiciones_v2[1][6]=0;
  if(options.duplicate) rows.posiciones_v2[2][0]='AAA';
  if(options.noMep) rows.tc_diario=[[]];
  if(options.badSchema) rows.historial[0][0]='Changed';
  const sheets=Object.fromEntries(Object.entries(rows).map(([name,data])=>[name,{
    getName:()=>name,getLastRow:()=>data.length,
    getRange:(r,c,n=1,w=1)=>({
      getValue:()=>options.badCount?'2':2,
      getDisplayValue:()=>options.blocked?'BLOQUEADO':'APTO',
      getDisplayValues:()=>[['Posiciones','2','2','OK'],['Sin valor','0','0','OK'],['Caja','0','0','OK'],['Total','','','OK'],['Snapshot apto','','','APTO']],
      getValues:()=>Array.from({length:n},(_,i)=>Array.from({length:w},(_,j)=>data[r-1+i]?.[c-1+j]??'')),
      setValues:v=>{writes++;if(fail===name){fail=null;throw Error('injected failure');}v.forEach((row,i)=>{data[r-1+i]=Array.from(row);});}
    })
  }]));
  const ss={getId:()=>options.wrongBase?'DEMO':'PERSONAL',getSheetByName:n=>sheets[n]};
  const ctx={Date:Clock,PropertiesService:{getScriptProperties:()=>({getProperty:()=>options.noConfig?null:'PERSONAL'})},
    SpreadsheetApp:{getActiveSpreadsheet:()=>ss,flush:()=>{}},
    LockService:{getDocumentLock:()=>({tryLock:()=>!options.busy,releaseLock:()=>released++})},
    Utilities:{formatDate:(d,tz,f)=>{const p=Object.fromEntries(new Intl.DateTimeFormat('en-CA',{timeZone:tz,year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',hourCycle:'h23'}).formatToParts(d).map(x=>[x.type,x.value]));return f==='HH'?p.hour:p.year+'-'+p.month+'-'+p.day;}}
  };
  vm.createContext(ctx);vm.runInContext(source,ctx);
  return {run:()=>ctx.pmsLegacySnapshotSafe(),rows,stats:()=>({writes,released})};
}
test('complete write is idempotent, preserves existing rows',()=>{
  const f=fixture();assert.equal(f.run().status,'WRITTEN_UNVERIFIED');
  const before=JSON.stringify(f.rows);assert.equal(f.run().status,'ALREADY_COMPLETE');
  assert.equal(JSON.stringify(f.rows),before);assert.equal(f.stats().writes,2);
});
test('failure after detail never becomes false success or automatic repair',()=>{
  const f=fixture({fail:'historial'});assert.throws(f.run,/no confirmada/);
  assert.equal(f.rows.historial.length,1);assert.equal(f.rows.historial_precios.length,3);
  assert.throws(f.run,/parcial o incongruente/);assert.equal(f.stats().writes,2);assert.equal(f.stats().released,2);
});
test('failure before any write can safely retry',()=>{
  const f=fixture({fail:'historial_precios'});assert.throws(f.run,/no confirmada/);
  assert.equal(f.run().status,'WRITTEN_UNVERIFIED');
});
for(const [name,option,pattern] of [
  ['wrong base','wrongBase',/Base personal/],['missing config','noConfig',/Base personal/],
  ['lock contention','busy',/bloqueo/],['blank quantity','blank',/valoración/],
  ['zero positive holding value','zero',/valoración/],['duplicate ticker','duplicate',/Universo/],
  ['missing current MEP','noMep',/MEP/],['integrity blocked','blocked',/Integridad/],
  ['changed schema','badSchema',/Esquema/],['nonnumeric expected count','badCount',/Universo esperado/]
]) test(name+' blocks without writes',()=>{const f=fixture({[option]:true});assert.throws(f.run,pattern);assert.equal(f.stats().writes,0);});
test('existing total mismatch is rejected without mutation',()=>{
  const f=fixture();f.run();f.rows.historial[1][3]=1;
  assert.throws(f.run,/parcial o incongruente/);assert.equal(f.stats().writes,2);
});
test('existing duplicate tickers with correct row count are rejected',()=>{
  const f=fixture();f.run();f.rows.historial_precios[2][1]='AAA';
  assert.throws(f.run,/parcial o incongruente/);
});
test('header without details is rejected',()=>{
  const f=fixture();f.run();f.rows.historial_precios.splice(1);
  assert.throws(f.run,/parcial o incongruente/);
});
