"""Read-only runtime probes injected into a page by the browser helper (only when a capture requests them)."""
from __future__ import annotations

# Optional read-only probe of running animations, expensive effects and layout shift (runs after the screenshot).
PROBE_JS = r'''async(waitMs)=>{let cls=0;try{new PerformanceObserver(l=>{for(const e of l.getEntries())if(!e.hadRecentInput)cls+=e.value}).observe({type:'layout-shift',buffered:true})}catch(_){}
 await new Promise(r=>setTimeout(r,waitMs));const h=document.documentElement.scrollHeight;window.scrollTo(0,h/2);await new Promise(r=>setTimeout(r,Math.max(100,waitMs/2)));window.scrollTo(0,0);await new Promise(r=>setTimeout(r,100));
 const an=(document.getAnimations?document.getAnimations():[]).map(a=>{const t=a.effect&&a.effect.getTiming?a.effect.getTiming():{};return{type:a.constructor.name,name:a.animationName||a.transitionProperty||null,duration:typeof t.duration==='number'?Math.round(t.duration):null,iterations:t.iterations===Infinity?'infinite':t.iterations,easing:t.easing||null}});
 let backdrop=0,blur=0,willChange=0,transitionAll=0,n=0;for(const el of document.querySelectorAll('body *')){if(++n>5000)break;const s=getComputedStyle(el);if(s.backdropFilter&&s.backdropFilter!=='none')backdrop++;if(s.filter&&s.filter.includes('blur'))blur++;if(s.willChange&&s.willChange!=='auto')willChange++;if(s.transitionProperty.split(',').map(x=>x.trim()).includes('all')&&parseFloat(s.transitionDuration)>0)transitionAll++}
 return{schema_version:1,animations:{total:an.length,infinite:an.filter(a=>a.iterations==='infinite').length,items:an.slice(0,50)},effects:{backdrop_filter:backdrop,filter_blur:blur,will_change:willChange},transition_all_elements:transitionAll,elements_scanned:Math.min(n,5000),cumulative_layout_shift:Math.round(cls*1000)/1000,reduced_motion_active:matchMedia('(prefers-reduced-motion: reduce)').matches}}'''

# Optional read-only layout probe (runs after the screenshot): responsive and legibility facts the critique loop
# scores without guessing from pixels.
LAYOUT_PROBE_JS = r'''()=>{const W=window.innerWidth,H=window.innerHeight,de=document.documentElement;
 const sel=el=>{let s=el.tagName.toLowerCase();if(el.id)return s+'#'+el.id;const c=(el.getAttribute('class')||'').trim().split(/\s+/).filter(Boolean).slice(0,2);return c.length?s+'.'+c.join('.'):s};
 const vis=el=>{const r=el.getBoundingClientRect(),st=getComputedStyle(el);return r.width>0&&r.height>0&&st.visibility!=='hidden'&&st.display!=='none'&&parseFloat(st.opacity)>0};
 const overflowing=[],small=[],targets=[];let n=0,textNodes=0;
 for(const el of document.querySelectorAll('body *')){if(++n>6000)break;if(!vis(el))continue;const r=el.getBoundingClientRect();
  if(r.right>W+1&&getComputedStyle(el).position!=='fixed'){let clipped=false;for(let a=el.parentElement;a&&a!==document.body;a=a.parentElement){const o=getComputedStyle(a).overflowX;if(o==='hidden'||o==='clip'||o==='auto'||o==='scroll'){clipped=true;break}}if(!clipped)overflowing.push(sel(el))}
  const own=[...el.childNodes].some(c=>c.nodeType===3&&c.textContent.trim().length>1);if(own){textNodes++;const fs=parseFloat(getComputedStyle(el).fontSize);if(fs<12)small.push(sel(el))}
  if(el.matches('a[href],button,[role="button"],input:not([type="hidden"]),select,textarea,summary')&&(r.width<24||r.height<24)&&!el.closest('p,li')){targets.push(sel(el))}}
 const h=[...document.querySelectorAll('h1,h2,h3,h4,h5,h6')].filter(vis).map(e=>+e.tagName[1]);let skips=0;for(let k=1;k<h.length;k++)if(h[k]-h[k-1]>1)skips++;
 const h1=document.querySelector('h1');const h1r=h1&&vis(h1)?h1.getBoundingClientRect():null;
 const act=[...document.querySelectorAll('main a[href],main button,a[href][class*="bg-"],button[class*="bg-"]')].find(e=>vis(e)&&e.getBoundingClientRect().top<H);
 const imgs=[...document.images].filter(vis);
 return{schema_version:1,viewport:{width:W,height:H},horizontal_overflow_px:Math.max(0,Math.round(de.scrollWidth-W)),
  overflowing_elements:{count:overflowing.length,samples:[...new Set(overflowing)].slice(0,5)},
  small_text:{count:small.length,of:textNodes,samples:[...new Set(small)].slice(0,5)},
  small_targets:{count:targets.length,samples:[...new Set(targets)].slice(0,5)},
  headings:{h1:h.filter(x=>x===1).length,levels:h.slice(0,40),skipped_levels:skips},
  above_fold:{h1_visible:!!(h1r&&h1r.top<H&&h1r.bottom>0),primary_action_visible:!!act},
  images:{count:imgs.length,missing_alt:imgs.filter(i=>!i.hasAttribute('alt')).length},
  page_height:de.scrollHeight}}'''

__all__ = ["PROBE_JS", "LAYOUT_PROBE_JS"]
