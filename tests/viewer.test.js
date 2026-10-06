"use strict";
const assert=require("node:assert/strict"),fs=require("node:fs"),path=require("node:path"),vm=require("node:vm");
const root=path.join(__dirname,".."),appPath=path.join(root,"skills/life-wiki/assets/viewer/app.js"),app=fs.readFileSync(appPath,"utf8"),wiki=JSON.parse(fs.readFileSync(path.join(root,"examples/expected/wiki.json"),"utf8"));
const {checkWiki,searchable}=require(appPath);
assert.equal(checkWiki(wiki),wiki);
assert(searchable(wiki.cards[0],wiki,"budget thread"));
assert(searchable(wiki.cards[3],wiki,"same work request"));
assert(!searchable(wiki.cards[0],wiki,"unrelated needle"));
const korean=JSON.parse(JSON.stringify(wiki));
korean.cards[0].summary="업무 승인";
assert(searchable(korean.cards[0],korean,"승인".normalize("NFD")));
const firstEvent=korean.cards[0].timeline[0],firstSource=korean.sources.find(s=>s.id===firstEvent.source_id);
firstSource.excerpt="가상\r\n승인 근거";firstEvent.quote="가상\n승인".normalize("NFD");
assert.equal(checkWiki(korean),korean);
const badHistory=JSON.parse(JSON.stringify(wiki));badHistory.history=[{operation_id:"invalid-time",action:"revise",recorded_at:"not-a-time",reason:"Fictional test"}];
assert.throws(()=>checkWiki(badHistory));
assert.throws(()=>checkWiki({schema_version:1}));
for(const mutate of [w=>w.cards[0].status="constructor",w=>w.cards[2].timeline[0].verification="false",w=>w.cards[2].outcome.state="verified_implemented",w=>w.relations[1].certainty="confirmed",w=>w.cards[0].id+="\n"]) {const invalid=JSON.parse(JSON.stringify(wiki));mutate(invalid);assert.throws(()=>checkWiki(invalid));}
assert(!/\b(fetch|XMLHttpRequest|WebSocket|localStorage|sessionStorage|sendBeacon|innerHTML|outerHTML|insertAdjacentHTML)\b/.test(app));
// Execute actual UI handlers with a strict DOM double: HTML interpretation is forbidden.
class Node {
  constructor(tag){this.tag=tag;this.children=[];this.events={};this.value="";this.checked=false;this.textContent="";this.files=[];}
  append(...nodes){this.children.push(...nodes);}
  replaceChildren(...nodes){this.children=[...nodes];}
  addEventListener(event,fn){this.events[event]=fn;}
  setAttribute(key,value){assert(!["src","href"].includes(key));this[key]=value;}
  set innerHTML(value){throw Error("HTML interpretation forbidden");}
}
const ids={};for(const id of ["notice","list","detail","search","status","archive","demo","file","count","graph-canvas","graph-records","graph-connections","graph-reset","graph-zoom-in","graph-zoom-out","operation-list","operation-summary","nav-map","nav-records","nav-operations","view-map","view-records","view-operations","map-detail","records-detail","nav-decisions","nav-topics","nav-people","nav-references","view-decisions","view-topics","view-people","view-references","decisions-content","topics-content","people-content","references-content"])ids[id]=new Node(id);
const document={getElementById:id=>ids[id],createElement:tag=>new Node(tag),addEventListener:(event,fn)=>{assert.equal(event,"DOMContentLoaded");document.ready=fn;}};
const context={document,window:{LIFE_WIKI_DEMO:wiki},console};vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(root,"skills/life-wiki/assets/viewer/graph.js"),"utf8"),context);vm.runInContext(app,context);document.ready();
ids.demo.events.click();assert.equal(ids.list.children.length,4);
assert.equal(ids["graph-records"].children.length,4);assert.equal(ids["graph-connections"].children.length,2);
assert.equal(ids["view-map"].hidden,false);ids["nav-records"].events.click();assert.equal(ids["view-map"].hidden,true);assert.equal(ids["view-records"].hidden,false);
ids["nav-operations"].events.click();assert.equal(ids["view-operations"].hidden,false);assert(ids["operation-summary"].textContent.includes("판본 0"));
assert.equal(ids["operation-list"].children[0].textContent,"최초 기록 · 저장된 운영 변경이 없습니다.");ids["nav-map"].events.click();
assert.equal(ids["references-content"].children.length,wiki.sources.length);
assert(ids["people-content"].children[0].textContent.includes("사람·역할 필드가 없습니다"));
for(const name of ["decisions","topics","people","references"]){ids["nav-"+name].events.click();assert.equal(ids["view-"+name].hidden,false);assert.equal(ids["view-map"].hidden,true);}ids["nav-map"].events.click();assert.equal(ids.detail.children[1].textContent,"LANTERN demonstration pilot");
ids.search.value="CINDER";ids.search.events.input();assert.equal(ids.list.children.length,1);assert.equal(ids["graph-records"].children.length,1);assert.equal(ids["graph-connections"].children.length,1);assert(ids["graph-connections"].children[0].textContent.includes("연결이 없습니다"));ids.list.children[0].events.click();assert.equal(ids.detail.children[1].textContent,"CINDER visitor guide");
ids.search.value="";ids.status.value="approved";ids.status.events.change();assert.equal(ids.list.children.length,1);
const demoContext={window:{}};vm.createContext(demoContext);vm.runInContext(fs.readFileSync(path.join(root,"skills/life-wiki/assets/viewer/demo-data.js"),"utf8"),demoContext);
context.window.LIFE_WIKI_DEMO=demoContext.window.LIFE_WIKI_DEMO;ids.demo.events.click();assert.equal(ids.list.children.length,6);assert(ids.count.textContent.includes("6개 기록"));
ids.search.value="work-islet";ids.search.events.input();assert.equal(ids.list.children.length,1);ids.list.children[0].events.click();assert.equal(ids.detail.children[1].textContent,"ISLET 여행 예약 변경");
ids.search.value="";ids.status.value="implemented";ids.status.events.change();assert.equal(ids.list.children.length,2);
function allText(node){return node.textContent+node.children.map(allText).join(" ");}
const attack=JSON.parse(JSON.stringify(wiki));attack.cards[0].summary='<img src=x onerror="alert(1)">';context.window.LIFE_WIKI_DEMO=attack;ids.demo.events.click();assert(allText(ids.detail).includes('<img src=x onerror="alert(1)">'));
assert(!ids.detail.children.some(n=>n.tag==="img"));
(async()=>{
 ids.file.files=[{size:20,text:async()=>JSON.stringify(wiki)}];await ids.file.events.change({target:ids.file});assert.equal(ids.list.children.length,4);
 ids.file.files=[{size:9*1024*1024,text:async()=>{throw Error("Should not read oversized file");}}];await ids.file.events.change({target:ids.file});assert(ids.notice.textContent.includes("8MB"));
 delete ids.demo;
 context.window.LIFE_WIKI_INITIAL=wiki;document.ready();
 assert(ids.count.textContent.includes("4개 기록"));assert.equal(ids.detail.children[1].textContent,"LANTERN demonstration pilot");
 context.window.LIFE_WIKI_INITIAL={invalid:true};document.ready();assert(ids.notice.textContent.includes("저장된 기록을 읽을 수 없습니다"));
 context.window.LIFE_WIKI_INITIAL=null;document.ready();
 ids.file.files=[{size:100,text:async()=>JSON.stringify({schema_version:1,revision:0,cards:[],sources:[],relations:[],history:[]})}];await ids.file.events.change({target:ids.file});
 assert(ids.count.textContent.includes("0개 기록"));assert(ids.detail.children[0].textContent.includes("현재 카드가 없습니다"));
 console.log("Viewer: menus, graph alternatives, list, search, status, selected card, local import, size limit, and inert HTML checks passed.");
})().catch(e=>{console.error(e);process.exitCode=1;});
