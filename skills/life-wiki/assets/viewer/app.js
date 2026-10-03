"use strict";
/* Original local viewer: no network, browser storage, or HTML interpretation. */
const labels = {unknown:"미확인",proposed:"제안",requested:"요청",approved:"승인",implemented:"실행 근거 있음",reported_implemented:"실행 보고",verified_implemented:"독립 확인",active:"현재 카드",retired:"이전 카드",related:"관련 업무",depends_on:"의존 업무",possible_same_work:"같은 업무일 가능성",confirmed:"근거 확인",uncertain:"불확실"};
function textValue(v) { if (typeof v !== "string") throw new Error("문자열 형식을 확인하세요."); return v; }
function checkWiki(w) {
  const phases=["unknown","proposed","requested","approved","implemented"];
  const id=v=>typeof v==="string"&&/^[a-z][a-z0-9-]{0,79}$/.test(v)&&!/[\r\n]/.test(v);
  const stamp=v=>typeof v==="string"&&/T.*(?:Z|[+-]\d{2}:\d{2})$/i.test(v)&&Number.isFinite(Date.parse(v));
  if (!w || w.schema_version !== 1 || !Number.isInteger(w.revision) || w.revision < 0 || !Array.isArray(w.cards) || !Array.isArray(w.sources) || !Array.isArray(w.relations) || !Array.isArray(w.history)) throw new Error("지원하는 wiki.json 형식이 아닙니다.");
  const ids=new Set(),sources=new Map(),events=new Map();
  for(const s of w.sources) {
    for(const key of ["id","sent_at","captured_at","content_sha256","excerpt"]) textValue(s[key]);
    if(!id(s.id)||sources.has(s.id)||!stamp(s.sent_at)||!stamp(s.captured_at)||!s.excerpt)throw new Error("출처 형식을 확인하세요.");
    if(s.uri !== undefined)textValue(s.uri);sources.set(s.id,s);
  }
  for (const c of w.cards) {
    if(!id(c.id)||ids.has(c.id))throw new Error("카드 식별자를 확인하세요.");ids.add(c.id);
    for(const key of ["title","summary","status","lifecycle"])textValue(c[key]);
    if(!phases.includes(c.status)||!["active","retired"].includes(c.lifecycle)||!Number.isInteger(c.revision)||c.revision<0||!Array.isArray(c.timeline)||!c.timeline.length||!Array.isArray(c.unknowns)||!Array.isArray(c.replaced_by)||!c.outcome||!["unknown","reported_implemented","verified_implemented"].includes(c.outcome.state)||!Array.isArray(c.outcome.evidence_ids))throw new Error("카드 형식을 확인하세요.");
    c.unknowns.forEach(textValue);c.replaced_by.forEach(textValue);c.outcome.evidence_ids.forEach(textValue);
    const local=new Map();
    for(const e of c.timeline) {
      for(const key of ["id","source_id","source_timestamp","kind","summary","quote","basis"])textValue(e[key]);
      const source=sources.get(e.source_id);
      if(!id(e.id)||local.has(e.id)||!stamp(e.source_timestamp)||!phases.includes(e.kind)||!["explicit","inferred"].includes(e.basis)||typeof e.verification!=="boolean"||!source||e.source_timestamp!==source.sent_at||!e.quote||!source.excerpt.includes(e.quote))throw new Error("기록과 출처 근거를 확인하세요.");
      if(e.verification&&(e.kind!=="implemented"||e.basis!=="explicit"))throw new Error("독립 확인 근거를 확인하세요.");
      if(events.has(e.id)) {const prior=events.get(e.id);if(["source_id","source_timestamp","kind","summary","quote","basis","verification"].some(k=>prior[k]!==e[k]))throw new Error("동일 근거 식별자의 내용이 다릅니다.");}
      local.set(e.id,e);events.set(e.id,e);
    }
    if(c.status!=="unknown"&&![...local.values()].some(e=>e.kind===c.status&&(c.status!=="implemented"||e.basis==="explicit")))throw new Error("상태를 뒷받침하는 근거를 확인하세요.");
    if(c.outcome.state==="unknown") {if(c.outcome.evidence_ids.length||c.status==="implemented")throw new Error("결과와 상태가 일치하지 않습니다.");}
    else {
      if(c.status!=="implemented"||!c.outcome.evidence_ids.length)throw new Error("실행 결과의 근거가 없습니다.");
      for(const eid of c.outcome.evidence_ids){const e=local.get(eid);if(!e||e.kind!=="implemented"||e.basis!=="explicit"||(c.outcome.state==="verified_implemented"&&!e.verification))throw new Error("실행 결과의 근거를 확인하세요.");}
    }
  }
  for(const c of w.cards)if((c.lifecycle==="active"&&c.replaced_by.length)||(c.lifecycle==="retired"&&!c.replaced_by.length)||c.replaced_by.some(cid=>!ids.has(cid)||cid===c.id))throw new Error("이전 카드 연결을 확인하세요.");
  const relationIds=new Set();
  for(const r of w.relations) {
    for(const key of ["id","from","to","type","certainty","rationale","recorded_at"])textValue(r[key]);
    const evidence=new Set(w.cards.filter(c=>c.id===r.from||c.id===r.to).flatMap(c=>c.timeline.map(e=>e.id)));
    if(!id(r.id)||relationIds.has(r.id)||!ids.has(r.from)||!ids.has(r.to)||r.from===r.to||!["related","depends_on","possible_same_work"].includes(r.type)||!["confirmed","uncertain"].includes(r.certainty)||!r.rationale||!stamp(r.recorded_at)||!Array.isArray(r.evidence_ids)||r.evidence_ids.some(eid=>!evidence.has(eid))||(r.certainty==="confirmed"&&!r.evidence_ids.length)||(r.type==="possible_same_work"&&r.certainty!=="uncertain"))throw new Error("업무 관계를 확인하세요.");
    relationIds.add(r.id);
  }
  for(const h of w.history)for(const key of ["operation_id","action","recorded_at","reason"])textValue(h[key]);
  return w;
}
function searchable(card, wiki, query) {
  const related=wiki.relations.filter(r=>r.from===card.id||r.to===card.id);
  const values=[card.id,card.title,card.summary,...card.unknowns,...card.timeline.flatMap(e=>[e.summary,e.quote]),...related.flatMap(r=>[r.rationale,r.type,r.certainty])];
  return values.join(" ").toLocaleLowerCase().includes(query.toLocaleLowerCase());
}
function element(tag, value, className) {
  const node=document.createElement(tag);
  if(value !== undefined) node.textContent=String(value);
  if(className) node.className=className;
  return node;
}
function mount() {
  const $=id=>document.getElementById(id);
  let wiki=null,selected=null;
  function notice(value){$("notice").textContent=value;}
  function showCard(id) {
    const c=wiki.cards.find(x=>x.id===id); if(!c)return;
    selected=id; const detail=$("detail"); detail.replaceChildren();
    detail.append(element("div",`${c.id} · r${c.revision}`,"eyebrow"),element("h1",c.title));
    const badges=element("div",undefined,"badges");
    badges.append(element("span",labels[c.status],"badge"),element("span",`결과: ${labels[c.outcome.state]}`,`badge ${c.outcome.state==="unknown"?"unknown":""}`),element("span",labels[c.lifecycle],"badge"));
    detail.append(badges,element("p",c.summary,"summary"),element("h2","시간순 기록"));
    const timeline=element("ol",undefined,"timeline");
    for(const e of [...c.timeline].sort((a,b)=>Date.parse(a.source_timestamp)-Date.parse(b.source_timestamp)||a.id.localeCompare(b.id))) {
      const li=element("li"),time=element("time",e.source_timestamp);time.dateTime=e.source_timestamp;
      li.append(time,element("span",`${labels[e.kind]||e.kind} · ${e.basis==="explicit"?"명시된 근거":"해석 포함"}`,"kind"),element("p",e.summary),element("blockquote",e.quote),element("small",`${e.id} · ${e.source_id}${e.verification?" · 독립 확인":""}`,"evidence"));timeline.append(li);
    }
    detail.append(timeline,element("h2","연결된 업무"));
    const relations=wiki.relations.filter(r=>r.from===id||r.to===id);
    if(!relations.length) detail.append(element("p","기록된 연결이 없습니다."));
    for(const r of relations) {
      const otherId=r.from===id?r.to:r.from,other=wiki.cards.find(x=>x.id===otherId),box=element("div",undefined,"relation"),button=element("button",other?other.title:otherId);button.type="button";
      button.addEventListener("click",()=>{if(other.lifecycle==="retired") $("archive").checked=true;$("search").value="";$("status").value="";showCard(otherId);renderList();});
      box.append(button,element("p",`${r.from===id?"이 업무 →":"이 업무 ←"} ${labels[r.type]} · ${labels[r.certainty]}`,r.certainty==="uncertain"?"unknown":""),element("p",r.rationale),element("small",`근거: ${r.evidence_ids.join(", ")||"없음"}`,"evidence"));detail.append(box);
    }
    detail.append(element("h2","아직 알 수 없는 것"));
    if(c.unknowns.length){const list=element("ul",undefined,"questions");for(const u of c.unknowns)list.append(element("li",u));detail.append(list);}else detail.append(element("p","추가 미확인 사항은 기록되지 않았습니다. 완료 판정은 아닙니다."));
    if(c.replaced_by.length) detail.append(element("p",`이어지는 카드: ${c.replaced_by.join(", ")}`));
    const provenance=element("details");provenance.append(element("summary","출처와 변경 이력"));
    const used=new Set(c.timeline.map(e=>e.source_id));
    for(const s of wiki.sources.filter(x=>used.has(x.id))) {
      const box=element("div",undefined,"source");box.append(element("strong",s.id),element("div",`원문 시각 ${s.sent_at} · 수집 시각 ${s.captured_at}`),element("div",`SHA-256 ${s.content_sha256}`));if(s.uri)box.append(element("div",`출처 위치: ${s.uri}`));provenance.append(box);
    }
    for(const h of wiki.history) provenance.append(element("div",`${h.operation_id} · ${h.action} · ${h.recorded_at} · ${h.reason}`,"history"));
    if(!wiki.history.length) provenance.append(element("p","최초 기록 · 판본 0"));
    detail.append(provenance);renderList();
  }
  function renderList() {
    const list=$("list");list.replaceChildren();if(!wiki)return;
    const cards=wiki.cards.filter(c=>($("archive").checked||c.lifecycle==="active")&&(!$("status").value||c.status===$("status").value)&&searchable(c,wiki,$("search").value));
    $("count").textContent=`${cards.length}개 업무 · 전체 판본 ${wiki.revision}`;
    for(const c of cards){const button=element("button");button.type="button";button.className=c.id===selected?"selected":"";button.setAttribute("aria-pressed",String(c.id===selected));button.append(element("strong",c.title),element("small",`${labels[c.status]} · 결과 ${labels[c.outcome.state]}`));button.addEventListener("click",()=>showCard(c.id));list.append(button);}
    if(!cards.length)list.append(element("p","검색에 맞는 업무가 없습니다. 검색어나 상태를 바꿔 보세요."));
  }
  function load(value,name) {
    wiki=checkWiki(value);selected=null;$("search").value="";$("status").value="";$("archive").checked=false;renderList();
    const first=wiki.cards.find(c=>c.lifecycle==="active");if(first)showCard(first.id);else $("detail").replaceChildren(element("p","현재 카드가 없습니다. 이전 카드를 포함해서 살펴보세요."));
    notice(`${name} · 이 화면은 읽기 전용입니다. 의미와 근거의 전체 검사는 wiki.py validate로 확인하세요.`);
  }
  $("demo").addEventListener("click",()=>{try{load(window.LIFE_WIKI_DEMO,"가상 예제");}catch{notice("가상 예제를 읽을 수 없습니다. 패키지의 demo-data.js를 확인하세요.");}});
  $("file").addEventListener("change",async event=>{
    const file=event.target.files[0];if(!file)return;
    try {if(file.size>8*1024*1024)throw new Error("파일이 8MB를 넘습니다. 선택한 업무만 새로 내보내세요.");load(JSON.parse(await file.text()),"선택한 파일");}
    catch(error){notice(`열 수 없습니다. ${error instanceof SyntaxError?"JSON 형식을 확인하세요.":error.message}`);}finally{event.target.value="";}
  });
  $("search").addEventListener("input",renderList);$("status").addEventListener("change",renderList);$("archive").addEventListener("change",renderList);
}
if(typeof document!=="undefined") document.addEventListener("DOMContentLoaded",mount);
if(typeof module!=="undefined") module.exports={checkWiki,searchable};
