// Isolated application-logic tests with a mock document. No browser access or visual assertions.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const bundle=JSON.parse(fs.readFileSync(path.join(root,'demo/review/data.json'),'utf8'));
const source=fs.readFileSync(path.join(root,'demo/review/app.js'),'utf8');
function environment(storage=new Map(), deny=false){
 const elements=new Map(),downloads=[];
 function element(id){if(!elements.has(id))elements.set(id,{id,value:'',hidden:false,innerHTML:'',textContent:'',validation:'',listeners:{},addEventListener(n,f){this.listeners[n]=f;},setCustomValidity(v){this.validation=v;},scrollIntoView(){},reportValidity(){return ['reviewer','note','verdict'].every(n=>element(n).value&&!element(n).validation);}});return elements.get(id);}
 const ctx=vm.createContext({window:{REVIEW_DATA:structuredClone(bundle)},document:{getElementById:element,createElement(){return {click(){downloads.push(this);}};}},location:{hash:''},history:{replaceState(){}},localStorage:{getItem(k){if(deny)throw Error('denied');return storage.get(k)||null;},setItem(k,v){if(deny)throw Error('denied');storage.set(k,v);},removeItem(k){if(deny)throw Error('denied');storage.delete(k);}},Blob,URL:{createObjectURL(){return 'blob:test';},revokeObjectURL(){}},setTimeout:f=>f(),console});
 vm.runInContext(source,ctx);
 return {ctx,element,downloads,storage,run:s=>vm.runInContext(s,ctx),submit(){element('review-form').listeners.submit({preventDefault(){}});}};
}
const e=environment();
assert.match(e.element('evidence').innerHTML,/924/);
assert.match(e.element('evidence').innerHTML,/47,622,058/);
assert.equal(e.element('download').hidden,true);
assert.equal(e.element('verdict').value,'');
e.run("switchCase('gsdmd-tmem106a')");assert.match(e.element('evidence').innerHTML,/48\.7/);
e.run("switchCase('cd274-lacc1')");assert.match(e.element('evidence').innerHTML,/Structure unavailable/);
e.run("switchCase('psap-lgals3')");
e.element('reviewer').value='  ';e.element('note').value='test';e.element('verdict').value='defer';e.submit();assert.equal(e.storage.size,0);
e.element('reviewer').value='UI test reviewer';e.element('reviewer').listeners.input();e.element('note').value='Inspect the source reads before choosing the junction.';e.submit();assert.equal(e.storage.size,1);
let receipt=JSON.parse([...e.storage.values()][0]);assert.equal(receipt.verdict,'defer');assert.equal(receipt.decision_sha256,bundle.cases[0].decision_sha256);assert.match(receipt.record_type,/self_reported/);
const reloaded=environment(e.storage);assert.equal(reloaded.element('reviewer').value,'UI test reviewer');assert.equal(reloaded.element('download').hidden,false);
reloaded.run("switchCase('cd274-lacc1')");assert.equal(reloaded.element('download').hidden,true);assert.equal(reloaded.element('reviewer').value,'');
reloaded.run("switchCase('psap-lgals3')");reloaded.element('download').onclick();assert.equal(reloaded.downloads.length,1);
reloaded.element('clear').onclick();assert.equal(reloaded.storage.size,0);
const blocked=environment(new Map(),true);blocked.element('reviewer').value='UI test';blocked.element('note').value='Test storage fallback.';blocked.element('verdict').value='defer';blocked.submit();assert.equal(blocked.downloads.length,1);assert.match(blocked.element('saved-status').textContent,/unavailable/);
const corrupted=new Map([[`chrna-review-v1:${bundle.cases[0].decision_sha256}`,JSON.stringify({...receipt,decision_sha256:'wrong'})]]);assert.equal(environment(corrupted).element('download').hidden,true);
assert.equal(e.run("esc('<img onerror=alert(1)>')"),'&lt;img onerror=alert(1)&gt;');
console.log('Review application logic passed: three cases, empty-field rejection, persistence, case binding, export, clear, unavailable storage, stale record rejection, text escaping. Visual/browser verification not performed.');
