"use strict";
/* Local canvas projection; relationships come only from the supplied wiki. */
function graphModel(wiki, cards) {
  const visible=new Set(cards.map(c=>c.id));
  const nodes=cards.map((c,i)=>{
    const y=1-2*(i+0.5)/Math.max(1,cards.length), radius=Math.sqrt(Math.max(0,1-y*y)), angle=i*Math.PI*(3-Math.sqrt(5));
    return {id:c.id,title:c.title,status:c.status,x:Math.cos(angle)*radius,y,z:Math.sin(angle)*radius};
  });
  const edges=wiki.relations.filter(r=>visible.has(r.from)&&visible.has(r.to)).map(r=>({id:r.id,from:r.from,to:r.to,type:r.type,certainty:r.certainty,rationale:r.rationale}));
  return {nodes,edges};
}
function mountGraph(canvas,onSelect) {
  if(!canvas || typeof canvas.getContext!=="function") return {update(){},reset(){},zoom(){},stop(){}};
  const ctx=canvas.getContext("2d");
  if(!ctx) return {update(){},reset(){},zoom(){},stop(){}};
  let model={nodes:[],edges:[]},selected=null,yaw=0.35,pitch=-0.2,scale=1,drag=null,projected=[];
  function draw() {
    const box=canvas.getBoundingClientRect(),w=Math.max(1,box.width),h=Math.max(1,box.height),dpr=Math.min(window.devicePixelRatio||1,2);
    if(canvas.width!==Math.round(w*dpr)||canvas.height!==Math.round(h*dpr)){canvas.width=Math.round(w*dpr);canvas.height=Math.round(h*dpr);}
    ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,w,h);
    ctx.fillStyle="#070b18";ctx.fillRect(0,0,w,h);
    // Decorative stars are deterministic and contain no records or relations.
    ctx.fillStyle="#45506e";
    for(let i=0;i<95;i++){ctx.globalAlpha=0.25+(i%4)*0.12;ctx.fillRect((i*137.7)%w,(i*i*31.3)%h,1.2,1.2);}ctx.globalAlpha=1;
    const size=Math.min(w*0.33,h*0.34)*scale;
    projected=model.nodes.map(n=>{
      const x=n.x*Math.cos(yaw)+n.z*Math.sin(yaw),z=-n.x*Math.sin(yaw)+n.z*Math.cos(yaw),y=n.y*Math.cos(pitch)-z*Math.sin(pitch),depth=n.y*Math.sin(pitch)+z*Math.cos(pitch),perspective=2.7/(2.7-depth*0.5);
      return {...n,px:w/2+x*size*perspective,py:h/2+y*size*perspective,depth,r:7+perspective*4};
    });
    const byId=new Map(projected.map(n=>[n.id,n]));
    for(const e of model.edges){const a=byId.get(e.from),b=byId.get(e.to);ctx.strokeStyle=e.certainty==="uncertain"?"#b48adf":"#54c7c3";ctx.globalAlpha=selected&&(selected===a.id||selected===b.id)?1:0.55;ctx.lineWidth=selected&&(selected===a.id||selected===b.id)?2.5:1.3;ctx.setLineDash(e.certainty==="uncertain"?[5,5]:[]);ctx.beginPath();ctx.moveTo(a.px,a.py);ctx.lineTo(b.px,b.py);ctx.stroke();}
    ctx.globalAlpha=1;ctx.setLineDash([]);
    for(const n of [...projected].sort((a,b)=>a.depth-b.depth)){
      ctx.fillStyle=n.id===selected?"#ffe5ad":"#83d6ef";ctx.shadowColor=ctx.fillStyle;ctx.shadowBlur=n.id===selected?22:12;ctx.beginPath();ctx.arc(n.px,n.py,n.r,0,Math.PI*2);ctx.fill();ctx.shadowBlur=0;
      ctx.fillStyle=n.id===selected?"#fff0ce":"#d6ddef";ctx.font=`${n.id===selected?"600":"400"} 12px system-ui`;ctx.textAlign="center";
      const title=n.title.length>24?n.title.slice(0,23)+"…":n.title;ctx.fillText(title,n.px,n.py+n.r+20,Math.max(100,w*0.4));
    }
    if(!model.nodes.length){ctx.fillStyle="#b9c4da";ctx.textAlign="center";ctx.font="15px system-ui";ctx.fillText("표시할 기록이 없습니다. wiki.json의 기록과 검색 조건을 확인하세요.",w/2,h/2,w-40);}
  }
  canvas.addEventListener("pointerdown",e=>{drag={x:e.clientX,y:e.clientY,startX:e.clientX,startY:e.clientY,moved:false};canvas.setPointerCapture(e.pointerId);});
  canvas.addEventListener("pointermove",e=>{if(!drag)return;const dx=e.clientX-drag.x,dy=e.clientY-drag.y;drag.moved=drag.moved||Math.hypot(e.clientX-drag.startX,e.clientY-drag.startY)>5;yaw+=dx*0.008;pitch=Math.max(-1.4,Math.min(1.4,pitch+dy*0.008));drag.x=e.clientX;drag.y=e.clientY;draw();});
  canvas.addEventListener("pointerup",e=>{if(drag&&!drag.moved){const box=canvas.getBoundingClientRect(),x=e.clientX-box.left,y=e.clientY-box.top;const found=[...projected].reverse().find(n=>Math.hypot(n.px-x,n.py-y)<n.r+12);if(found)onSelect(found.id);}drag=null;});
  canvas.addEventListener("pointercancel",()=>{drag=null;});
  canvas.addEventListener("wheel",e=>{e.preventDefault();scale=Math.max(0.45,Math.min(2.4,scale*Math.exp(-e.deltaY*0.001)));draw();},{passive:false});
  canvas.addEventListener("keydown",e=>{if(["ArrowLeft","ArrowRight","ArrowUp","ArrowDown","+","-","Home"].includes(e.key)){e.preventDefault();if(e.key==="ArrowLeft")yaw-=0.12;if(e.key==="ArrowRight")yaw+=0.12;if(e.key==="ArrowUp")pitch-=0.12;if(e.key==="ArrowDown")pitch+=0.12;if(e.key==="+")scale=Math.min(2.4,scale*1.1);if(e.key==="-")scale=Math.max(0.45,scale/1.1);if(e.key==="Home"){yaw=0.35;pitch=-0.2;scale=1;}draw();}});
  const resize=typeof ResizeObserver!=="undefined"?new ResizeObserver(draw):null;if(resize)resize.observe(canvas);
  window.addEventListener("resize",draw);
  return {update(value,id){model=value;selected=id;draw();},reset(){yaw=0.35;pitch=-0.2;scale=1;draw();},zoom(factor){scale=Math.max(0.45,Math.min(2.4,scale*factor));draw();},stop(){resize?.disconnect();window.removeEventListener("resize",draw);}};
}
if(typeof module!=="undefined")module.exports={graphModel,mountGraph};
