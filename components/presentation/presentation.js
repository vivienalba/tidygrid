/* Supported Streamlit v2 lifecycle. Bundled Anime.js is prepended by Python. */
export default function({parentElement,data}) {
 const root=parentElement.querySelector('.presentation');
 parentElement.querySelector('.fonts').textContent=data.fonts||'';root.replaceChildren();root.className='presentation '+data.kind;
 const make=(tag,cls,text)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n};
 const mq=matchMedia('(prefers-reduced-motion: reduce)');let scope;const listeners=[];
 if(data.kind==='art'){root.style.height=data.height+'px';root.style.setProperty('--art-height',data.height+'px');const img=make('img');img.src=data.src;img.alt=data.alt||'';root.append(img)}
 else if(data.kind==='summary'){root.setAttribute('role','list');root.setAttribute('aria-label','Dataset summary');for(const item of data.items){const el=make('div','metric');el.setAttribute('role','listitem');el.append(make('div','metric-label',item.label),make('div','metric-value',item.value),make('div','metric-detail',item.detail));root.append(el)}}
 else if(data.kind==='comparison'){
 const top=make('div','comparison-top');top.append(make('h2',null,'Small fixes. Clear difference.'),make('p',null,'A few examples from your actual changed cells.'));root.append(top);
 if(!data.pairs.length){const empty=make('div','empty');empty.append(make('div','empty-title','Already in good order.'),make('p',null,'No text changes to show. Your selected rules already match these values.'));root.append(empty)}
 else{const table=make('div','comparison-table');table.setAttribute('role','table');table.setAttribute('aria-label','Actual values before and after cleaning');root.append(table);const head=make('div','comparison-head');head.setAttribute('role','row');['Column','Before','After'].forEach(t=>{const cell=make('span',null,t);cell.setAttribute('role','columnheader');head.append(cell)});table.append(head);
 const shown=v=>{const s=String(v),a=s.length-s.trimStart().length,b=s.length-s.trimEnd().length;return s?('␣'.repeat(a)+s.trim()+'␣'.repeat(b)):'Blank'};
 for(const[field,before,after]of data.pairs){const row=make('div','compare-row');row.setAttribute('role','row');for(const[cls,value]of [['field',field],['before',shown(before)],['after',shown(after)]]){const cell=make('div',cls,value);cell.setAttribute('role','cell');row.append(cell)}table.append(row)}}}
 const clearListeners=()=>{for(const[el,type,fn]of listeners)el.removeEventListener(type,fn);listeners.length=0};
 const reveal=()=>{scope?.revert();if(mq.matches||!globalThis.anime)return;const{animate,createTimeline,createScope,stagger}=globalThis.anime;scope=createScope({root}).add(()=>{
 if(data.kind==='art'){const img=root.querySelector('img');createTimeline({defaults:{ease:'out(3)'}}).add(img,{opacity:[.82,1],y:[8,0],duration:340});const hover=()=>{if(matchMedia('(hover:hover) and (pointer:fine)').matches)animate(img,{y:-3,duration:180,ease:'out(3)'})},leave=()=>animate(img,{y:0,duration:220,ease:'out(3)'});img.addEventListener('pointerenter',hover);img.addEventListener('pointerleave',leave);listeners.push([img,'pointerenter',hover],[img,'pointerleave',leave])}
 else if(data.kind==='summary')animate(root.querySelectorAll('.metric'),{opacity:[.8,1],y:[4,0],duration:220,delay:stagger(25),ease:'out(3)'});
 else if(data.kind==='comparison')createTimeline({defaults:{ease:'out(3)'}}).add(root.querySelectorAll('.after'),{opacity:[.75,1],duration:180});})};
 const onChange=()=>{clearListeners();reveal()};mq.addEventListener('change',onChange);reveal();return()=>{clearListeners();mq.removeEventListener('change',onChange);scope?.revert()};
}
