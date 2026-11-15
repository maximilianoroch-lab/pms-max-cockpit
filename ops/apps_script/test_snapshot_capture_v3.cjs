// Run: node ops/apps_script/test_snapshot_capture_v3.cjs
// Offline Google Apps Script mocks. No Sheets credentials or network calls.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, 'SnapshotCaptureV3.gs'), 'utf8');
function fixture({holiday=false, apto=true, duplicate=false, partial=false, missingValue=false, repeatedTicker=false, at='2026-11-16T14:02:00.000Z'} = {}) {
  const records = duplicate || partial ? [
    ['OBS-20261116-1100','','','','','AAPL'],
    ...(partial ? [] : [['OBS-20261116-1100','','','','','GOOGL']])
  ] : [];
  const getRows = () => records;
  const target = {
    getLastRow: () => records.length + 1,
    getRange: (r,c,n,w) => ({
      getDisplayValues: () => records.map(x=>x.slice(0,w)),
      setValues: values => { records.push(...values); }
    })
  };
  const pos = {
    getLastRow: () => 3,
    getRange: () => ({getValues: () => [
      ['AAPL','Apple',1,'','', 'ARS', missingValue?0:100, '', '', '', '', '', '', '', '', 'quote'],
      [repeatedTicker?'AAPL':'GOOGL','Alphabet',2,'','', 'ARS', 200, '', '', '', '', '', '', '', '', 'quote']
    ]})
  };
  const integrity = {getRange: key => ({
    getDisplayValue: () => apto?'APTO':'BLOQUEADO',
    getValue: () => 2
  })};
  const holidaySheet = {
    getLastRow:()=>2,
    getRange:()=>({getDisplayValues:()=>[[holiday?'2026-11-16':'2026-11-20']]})
  };
  const ss = {getSheetByName: n=>({
    observaciones_intradiarias_v3:target,
    posiciones_v2:pos,
    control_integridad_v2:integrity,
    feriados_mercado_v3:holidaySheet
  })[n]};
  const RealDate = Date;
  class FixedDate extends RealDate {
    constructor(...args) { super(...(args.length ? args : [at])); }
    static now(){return RealDate.parse(at);}
  }
  const context = {
    Date:FixedDate,
    SpreadsheetApp:{getActiveSpreadsheet:()=>ss,flush:()=>{}},
    LockService:{getDocumentLock:()=>({tryLock:()=>true,releaseLock:()=>{}})},
    Utilities:{formatDate:(d,tz,fmt)=>{
      if(tz!=='America/Argentina/Buenos_Aires') throw Error('Timezone error');
      const parts = new Intl.DateTimeFormat('en-CA',{
        timeZone:tz,year:'numeric',month:'2-digit',day:'2-digit',
        hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'
      }).formatToParts(d);
      const p=Object.fromEntries(parts.map(x=>[x.type,x.value]));
      if(fmt==='yyyy-MM-dd') return p.year+'-'+p.month+'-'+p.day;
      if(fmt==='HH:mm:ss') return p.hour+':'+p.minute+':'+p.second;
      if(fmt==='u') return String(new Date(Date.UTC(Number(p.year), Number(p.month)-1, Number(p.day))).getUTCDay() || 7);
      throw Error('unknown date format '+fmt);
    }}
  };
  vm.createContext(context);vm.runInContext(source,context);
  return {capture:slot=>context.pmsV3_capture_(slot),getRows};
}
function run(){
  const ok=fixture(); const result=ok.capture('11:00');
  assert.equal(result.status,'CAPTURED_UNVERIFIED');
  assert.equal(result.totalUsd,300);
  assert.equal(ok.getRows().length,2);
  assert.equal(ok.capture('11:00').status,'ALREADY_CAPTURED');
  assert.equal(ok.getRows().length,2);
  const blocked=fixture({apto:false});
  assert.throws(()=>blocked.capture('11:00'),/Integridad no apta/);
  assert.equal(blocked.getRows().length,0);
  const badQuote=fixture({missingValue:true});
  assert.throws(()=>badQuote.capture('11:00'),/sin valor válido/);
  assert.equal(badQuote.getRows().length,0);
  const repeated=fixture({repeatedTicker:true});
  assert.throws(()=>repeated.capture('11:00'),/Tickers duplicados/);
  assert.equal(repeated.getRows().length,0);
  const holiday=fixture({holiday:true});
  const bymaHoliday = holiday.capture('11:00');
  assert.equal(bymaHoliday.status,'CAPTURED_UNVERIFIED');
  assert.equal(bymaHoliday.bymaOpen,false);
  assert.equal(holiday.getRows().length,2);
  assert.ok(holiday.getRows().every(x=>x[4]==='OBSERVADO_BYMA_CERRADO_NO_CERTIFICADO'));
  const duplicate=fixture({duplicate:true});
  assert.equal(duplicate.capture('11:00').status,'ALREADY_CAPTURED');
  assert.equal(duplicate.getRows().length,2);
  const partial=fixture({partial:true});
  assert.throws(()=>partial.capture('11:00'),/anterior incompleta/);
  assert.equal(partial.getRows().length,1);
  assert.throws(()=>fixture().capture('12:00'),/Horario no permitido/);
  const weekend=fixture({at:'2026-11-15T14:02:00.000Z'});
  assert.equal(weekend.capture('11:00').status,'SKIP_WEEKEND');
  assert.equal(weekend.getRows().length,0);
  for (const [slot,utcHour] of [['11:00','14'],['14:00','17'],['17:00','20']]) {
    const each=fixture({at:'2026-11-16T'+utcHour+':02:00.000Z'});
    assert.equal(each.capture(slot).status,'CAPTURED_UNVERIFIED');
    assert.equal(each.getRows().length,2);
  }
  assert.throws(()=>fixture().capture('17:00'),/fuera de franja/);
  console.log('PASS: capture/replay, integrity, invalid quote, BYMA holiday observation, weekend skip, complete and partial existing IDs, invalid slot and all three slots');
}
run();
