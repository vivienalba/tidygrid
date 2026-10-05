/* One lifecycle, one motion owner per surface. Content is visible before animation. */
export default function({parentElement,data}) {
 const root=parentElement.querySelector('.presentation');
 const fontStyle=parentElement.querySelector('.fonts');if(fontStyle.textContent!==data.fonts)fontStyle.textContent=data.fonts||'';
 const {fonts,animate:entrance,...content}=data;const signature=JSON.stringify(content);
 if(root.dataset.signature===signature)return()=>{};
 root.dataset.signature=signature;root.replaceChildren();root.className='presentation '+data.kind;
 const make=(tag,cls,text)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n};
 if(data.kind==='art'){
  root.style.height=data.height+'px';root.style.setProperty('--art-height',data.height+'px');const img=make('img');img.src=data.src;img.alt=data.alt||'';img.loading='lazy';img.decoding='async';root.append(img);
 }else if(data.kind==='summary'){
  root.append(make('h2','summary-title',data.title||'Your data in numbers'));
  const grid=make('div','stats-grid');grid.style.setProperty('--columns',data.items.length);grid.setAttribute('role','list');grid.setAttribute('aria-label',data.title||'Dataset summary');root.append(grid);
  for(const item of data.items){const el=make('div','metric');el.setAttribute('role','listitem');el.append(make('div','metric-label',item.label),make('div','metric-value',item.value),make('div','metric-detail',item.detail));grid.append(el)}
 }else if(data.kind==='comparison'){
  const top=make('div','comparison-top');top.append(make('h2',null,'Small fixes. Clear difference.'),make('p',null,'Examples from your actual changed cells.'));root.append(top);
  if(!data.pairs.length){const empty=make('div','empty');empty.append(make('div','empty-title','Already in good order.'),make('p',null,'Your selected rules already match these values.'));root.append(empty)}
  else{const table=make('div','comparison-table');table.setAttribute('role','table');table.setAttribute('aria-label','Actual values before and after cleaning');root.append(table);const head=make('div','comparison-head');head.setAttribute('role','row');['Column','Before','After'].forEach(t=>{const cell=make('span',null,t);cell.setAttribute('role','columnheader');head.append(cell)});table.append(head);
   const shown=v=>{const s=String(v),a=s.length-s.trimStart().length,b=s.length-s.trimEnd().length;return s?('␣'.repeat(a)+s.trim()+'␣'.repeat(b)):'Blank'};
   for(const[field,before,after]of data.pairs){const row=make('div','compare-row');row.setAttribute('role','row');for(const[cls,value]of [['field',field],['before',shown(before)],['after',shown(after)]]){const cell=make('div',cls,value);cell.setAttribute('role','cell');row.append(cell)}table.append(row)}
  }
 }
 let observer,media,scope,disposed=false;
 const preference=matchMedia("(prefers-reduced-motion: reduce)");
 const reduce=()=>{if(preference.matches)scope?.revert()};preference.addEventListener("change",reduce);
 const start=()=>{
  if(disposed||!entrance)return;
  if(data.kind==='art'&&globalThis.gsap){
   media=globalThis.gsap.matchMedia();media.add('(prefers-reduced-motion: no-preference)',()=>{
    const img=root.querySelector('img');if(!img)return;globalThis.gsap.fromTo(img,{opacity:.8},{opacity:1,duration:.24,ease:'power2.out',clearProps:'opacity'});
   },root);
  }else if(globalThis.anime&&!matchMedia('(prefers-reduced-motion: reduce)').matches){
   const {createScope,animate}=globalThis.anime;scope=createScope({root}).add(()=>{
    const target=root.querySelectorAll(data.kind==='summary'?'.metric-value':'.after');
    animate(target,{opacity:[.8,1],duration:150,ease:'out(3)'});
   });
  }
 };
 if(entrance){observer=new IntersectionObserver(entries=>{if(entries.some(e=>e.isIntersecting)){observer.disconnect();start()}},{threshold:.1});observer.observe(root)}
 return()=>{disposed=true;preference.removeEventListener("change",reduce);observer?.disconnect();media?.revert();scope?.revert()};
}
