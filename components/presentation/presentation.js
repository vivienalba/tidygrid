/* One lifecycle, one motion owner per surface. Content is visible before animation. */
export default function({parentElement,data,setTriggerValue}) {
 const root=parentElement.querySelector('.presentation');
 const fontStyle=parentElement.querySelector('.fonts');if(fontStyle.textContent!==data.fonts)fontStyle.textContent=data.fonts||'';
 const {fonts,animate:entrance,...content}=data;const signature=JSON.stringify(content);
 const changed=root.dataset.signature!==signature;
 root._dispose?.();
 if(changed){
 root.dataset.signature=signature;root.replaceChildren();root.className='presentation '+data.kind;
 const make=(tag,cls,text)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n};
 if(data.kind==='navigation'){
  const brand=make('div','mobile-brand');brand.innerHTML=data.logo;root.append(brand);
  const toggle=make('button','menu-toggle');toggle.type='button';toggle.setAttribute('aria-label','Open navigation');toggle.setAttribute('aria-expanded','false');toggle.setAttribute('aria-haspopup','dialog');
  toggle.innerHTML='<span></span><span></span><span></span>';root.append(toggle);
  const dialog=make('dialog','mobile-dialog');dialog.id='tidygrid-mobile-menu';dialog.setAttribute('aria-label','Navigation');toggle.setAttribute('aria-controls',dialog.id);
  const panel=make('div','mobile-menu-panel'),head=make('div','mobile-menu-head');
  const title=make('div','mobile-menu-title','TidyGrid'),close=make('button','menu-close','Close');close.type='button';head.append(title,close);panel.append(head);
  const nav=make('nav','mobile-menu-links');nav.setAttribute('aria-label','Main navigation');panel.append(nav);
  const items=data.workspace?[['Back to Home','Home'],...data.pages.map(p=>[p,p])]:[['The workspace','#the-workspace'],['Import data','#import-dataset']];
  for(const[label,value]of items){const item=make('button','mobile-menu-item',label);item.type='button';item.dataset.destination=value;if(value===data.page)item.setAttribute('aria-current','page');nav.append(item)}
  dialog.append(panel);root.append(dialog);
 }else if(data.kind==='art'){
  root.style.height=data.height+'px';root.style.setProperty('--art-height',data.height+'px');const img=make('img');img.src=data.src;img.alt=data.alt||'';img.loading='lazy';img.decoding='async';root.append(img);
 }else if(data.kind==='summary'){
  if(data.variant==='cards'){root.classList.add('summary-cards')}else{root.append(make('h2','summary-title',data.title||'Your data in numbers'))}
  const grid=make('div','stats-grid');grid.style.setProperty('--columns',data.items.length);grid.setAttribute('role','list');grid.setAttribute('aria-label',data.title||'Dataset summary');root.append(grid);
  for(const item of data.items){const el=make('div','metric');el.setAttribute('role','listitem');el.append(make('div','metric-label',item.label),make('div','metric-value',item.value),make('div','metric-detail',item.detail));grid.append(el)}
 }else if(data.kind==='quality'){
  for(const item of data.items){
   const row=make('div','quality-row'),head=make('div','quality-head');
   head.append(make('div','quality-label',item.label),make('div','quality-count',`${item.filled} / ${item.total}`));
   const track=make('div','quality-track'),fill=make('div','quality-fill');
   track.setAttribute('role','progressbar');track.setAttribute('aria-label',`${item.label}: filled cells`);track.setAttribute('aria-valuemin','0');track.setAttribute('aria-valuemax',String(Math.max(1,item.total)));track.setAttribute('aria-valuenow',String(item.filled));
   fill.style.width=(item.total?item.filled/item.total*100:0)+'%';track.append(fill);row.append(head,track);root.append(row);
  }
 }else if(data.kind==='comparison'){
  const top=make('div','comparison-top');top.append(make('h2',null,'Small fixes. Clear difference.'),make('p',null,'Examples from your actual changed cells.'));root.append(top);
  if(!data.pairs.length){const empty=make('div','empty');empty.append(make('div','empty-title','Already in good order.'),make('p',null,'Your selected rules already match these values.'));root.append(empty)}
  else{const table=make('div','comparison-table');table.setAttribute('role','table');table.setAttribute('aria-label','Actual values before and after cleaning');root.append(table);const head=make('div','comparison-head');head.setAttribute('role','row');['Column','Before','After'].forEach(t=>{const cell=make('span',null,t);cell.setAttribute('role','columnheader');head.append(cell)});table.append(head);
   const shown=v=>{const s=String(v),a=s.length-s.trimStart().length,b=s.length-s.trimEnd().length;return s?('␣'.repeat(a)+s.trim()+'␣'.repeat(b)):'Blank'};
   for(const[field,before,after]of data.pairs){const row=make('div','compare-row');row.setAttribute('role','row');for(const[cls,value]of [['field',field],['before',shown(before)],['after',shown(after)]]){const cell=make('div',cls,value);cell.setAttribute('role','cell');row.append(cell)}table.append(row)}
  }
 }
 }
 if(data.kind==='navigation'){
  const toggle=root.querySelector('.menu-toggle'),dialog=root.querySelector('dialog'),panel=root.querySelector('.mobile-menu-panel'),close=root.querySelector('.menu-close');
  const gsap=globalThis.gsap,reduced=matchMedia('(prefers-reduced-motion: reduce)'),desktop=matchMedia('(min-width:701px)');
  let timeline,disposed=false;const context=gsap?.context(()=>{},root);
  const tween=fn=>context?context.add(fn):fn();
  const finish=()=>{if(!dialog.open)return;dialog.close();toggle.setAttribute('aria-expanded','false');toggle.focus({preventScroll:true})};
  const hide=(done)=>{timeline?.kill();toggle.setAttribute('aria-expanded','false');if(!gsap||reduced.matches){finish();done?.();return}tween(()=>{timeline=gsap.timeline({onComplete:()=>{finish();done?.()}}).to(panel,{x:-20,opacity:0,duration:.16,ease:'power2.in'},0).to(dialog,{opacity:0,duration:.16},0)})};
  const show=()=>{timeline?.kill();if(!dialog.open)dialog.showModal();toggle.setAttribute('aria-expanded','true');close.focus({preventScroll:true});if(!gsap||reduced.matches){dialog.style.opacity='1';panel.style.opacity='1';panel.style.transform='none';return}tween(()=>{timeline=gsap.timeline().fromTo(dialog,{opacity:0},{opacity:1,duration:.18,ease:'power2.out'},0).fromTo(panel,{x:-24,opacity:.7},{x:0,opacity:1,duration:.24,ease:'power3.out'},0)})};
  const cancel=e=>{e.preventDefault();hide()};const backdrop=e=>{if(e.target===dialog)hide()};
  const choose=e=>{const button=e.target.closest('[data-destination]');if(!button)return;const target=button.dataset.destination;
   hide(()=>{if(disposed)return;if(target.startsWith('#')){const section=document.getElementById(target.slice(1));section?.scrollIntoView({behavior:reduced.matches?'instant':'smooth',block:'start'})}else{setTriggerValue('navigate',target)}});
  };
  const change=()=>{timeline?.kill();context?.revert();if(desktop.matches){finish()}else if(dialog.open){dialog.style.opacity='1';panel.style.opacity='1';panel.style.transform='none'}};
  const closeClick=()=>hide();toggle.addEventListener('click',show);close.addEventListener('click',closeClick);dialog.addEventListener('cancel',cancel);dialog.addEventListener('click',backdrop);panel.addEventListener('click',choose);reduced.addEventListener('change',change);desktop.addEventListener('change',change);
  const dispose=()=>{disposed=true;timeline?.kill();context?.revert();if(dialog.open)dialog.close();toggle.removeEventListener('click',show);close.removeEventListener('click',closeClick);dialog.removeEventListener('cancel',cancel);dialog.removeEventListener('click',backdrop);panel.removeEventListener('click',choose);reduced.removeEventListener('change',change);desktop.removeEventListener('change',change)};
  root._dispose=dispose;return dispose;
 }
 let media,scope,disposed=false;
 // Own only component-local nodes. Native Streamlit tables and controls stay stable.
 if(globalThis.gsap){
  const gsap=globalThis.gsap;media=gsap.matchMedia();
  media.add({motion:'(prefers-reduced-motion: no-preference)',hover:'(hover: hover) and (pointer: fine)'},ctx=>{
   if(!ctx.conditions.motion)return;
   let observer;
   const enter=()=>ctx.add(()=>{
    if(disposed)return;
    const tl=gsap.timeline({defaults:{duration:.3,ease:'power2.out'}});
    if(data.kind==='art')tl.fromTo(root.querySelector('img'),{opacity:.65,y:12},{opacity:1,y:0,duration:.38,clearProps:'opacity,transform'});
    if(data.kind==='summary')tl.fromTo(root.querySelectorAll('.metric'),{opacity:.65,y:7},{opacity:1,y:0,stagger:.045,clearProps:'opacity,transform'});
    if(data.kind==='quality')tl.fromTo(root.querySelectorAll('.quality-fill'),{scaleX:0},{scaleX:1,transformOrigin:'left center',duration:.4,stagger:.04,clearProps:'transform'});
    if(data.kind==='comparison')tl.fromTo(root.querySelectorAll('.compare-row'),{opacity:.7,y:5},{opacity:1,y:0,stagger:.035,clearProps:'opacity,transform'});
   });
   if(entrance){observer=new IntersectionObserver(entries=>{if(entries.some(e=>e.isIntersecting)){observer.disconnect();enter()}},{threshold:.1});observer.observe(root)}
   const img=root.querySelector('img');
   // One interruptible hover tween, with no decorative loop or scroll listener.
   const over=()=>ctx.add(()=>gsap.to(img,{y:-4,duration:.22,ease:'power2.out',overwrite:'auto'}));
   const out=()=>ctx.add(()=>gsap.to(img,{y:0,duration:.22,ease:'power2.out',overwrite:'auto',clearProps:'transform'}));
   if(img&&ctx.conditions.hover){root.addEventListener('pointerenter',over);root.addEventListener('pointerleave',out)}
   // Anime owns only value opacity on a changed summary, never GSAP's card transform.
   if(changed&&!entrance&&data.kind==='summary'&&globalThis.anime){scope=globalThis.anime.createScope({root}).add(()=>globalThis.anime.animate(root.querySelectorAll('.metric-value'),{opacity:[.7,1],duration:140,ease:'out(3)'}))}
   return()=>{observer?.disconnect();root.removeEventListener('pointerenter',over);root.removeEventListener('pointerleave',out);scope?.revert()};
  },root);
 }
 const dispose=()=>{if(disposed)return;disposed=true;media?.revert();scope?.revert()};
 root._dispose=dispose;
 return dispose;
}
