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
const ids={};for(const id of ["notice","list","detail","search","status","archive","demo","file","count"])ids[id]=new Node(id);
const document={getElementById:id=>ids[id],createElement:tag=>new Node(tag),addEventListener:(event,fn)=>{assert.equal(event,"DOMContentLoaded");document.ready=fn;}};
const context={document,window:{LIFE_WIKI_DEMO:wiki},console};vm.createContext(context);vm.runInContext(app,context);document.ready();
ids.demo.events.click();assert.equal(ids.list.children.length,4);assert.equal(ids.detail.children[1].textContent,"LANTERN demonstration pilot");
ids.search.value="CINDER";ids.search.events.input();assert.equal(ids.list.children.length,1);ids.list.children[0].events.click();assert.equal(ids.detail.children[1].textContent,"CINDER visitor guide");
ids.search.value="";ids.status.value="approved";ids.status.events.change();assert.equal(ids.list.children.length,1);
function allText(node){return node.textContent+node.children.map(allText).join(" ");}
const attack=JSON.parse(JSON.stringify(wiki));attack.cards[0].summary='<img src=x onerror="alert(1)">';context.window.LIFE_WIKI_DEMO=attack;ids.demo.events.click();assert(allText(ids.detail).includes('<img src=x onerror="alert(1)">'));
assert(!ids.detail.children.some(n=>n.tag==="img"));
(async()=>{
 ids.file.files=[{size:20,text:async()=>JSON.stringify(wiki)}];await ids.file.events.change({target:ids.file});assert.equal(ids.list.children.length,4);
 ids.file.files=[{size:9*1024*1024,text:async()=>{throw Error("Should not read oversized file");}}];await ids.file.events.change({target:ids.file});assert(ids.notice.textContent.includes("8MB"));
 console.log("Viewer: list, search, status, selected card, local import, size limit, and inert HTML checks passed.");
})().catch(e=>{console.error(e);process.exitCode=1;});
