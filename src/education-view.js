import { articleFigures } from './article-figures.js';
import { explainers, explainerBody } from '../education/src/research-explainers.js';
import { englishArticles } from '../education/src/content-en.js';
import { chineseArticles } from '../education/src/content-zh.js';
const esc=v=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function educationView(lang,slug){
 const zh=lang==='zh', articles=zh?chineseArticles:englishArticles;
 const cards=items=>items.map(a=>`<a class="panel reading-card" href="#article-${a.slug}"><small>${a.category==='gene'?(zh?'免疫分子':'Immune molecules'):'CVID'}</small><h2>${esc(a.title)}</h2><p>${esc(a.excerpt)}</p><span>${zh?'阅读全文':'Read article'} →</span></a>`).join('');
 const paperCards=()=>explainers.map((a,i)=>`<a class="panel reading-card" href="#cvid/paper/${i}"><small>${esc(a.type[zh?0:1])} · ${a.date}</small><h2>${esc(a.title[zh?0:1])}</h2><p>${esc(a.intro[zh?0:1])}</p><span>${zh?'阅读解读':'Read explainer'} →</span></a>`).join('');
 if(slug?.startsWith('paper/')){const i=Number(slug.slice(6)),a=explainers[i];if(!a)return educationView(lang,'topic/papers');return `<section class="page-shell education-article"><a href="#cvid/topic/papers">← ${zh?'论文解读':'Paper explainers'}</a><h1>${esc(a.title[zh?0:1])}</h1><p class="article-lead">${esc(a.intro[zh?0:1])}</p><p>${esc(a.type[zh?0:1])} · ${esc(a.sample[zh?0:1])}</p><article>${explainerBody(i,!zh)}</article></section>`;}
 if(slug==='topic/papers')return `<section class="page-shell education-library"><a href="#cvid/topic/research">← ${zh?'了解研究':'Understanding research'}</a><h1>${zh?'论文解读':'Paper explainers'}</h1><p>${zh?'从研究问题、方法到发现与局限，逐篇理解。':'Explore each paper’s question, methods, findings and limitations.'}</p><div class="angle-grid learning-groups">${paperCards()}</div></section>`;
 const groups=[['basics','Start with CVID','从了解 CVID 开始',['infection','multi-organ','lab-results']],['genetics','Genetics & immune molecules','遗传与免疫分子',['genetics',...articles.filter(a=>a.category==='gene').map(a=>a.slug)]],['living','Treatment & family life','治疗与家庭生活',['immunoglobulin-replacement','family']],['research','Understanding research','了解研究',['research-progress','research-participation']]];
 if(!slug || slug.startsWith('topic/')){
   const group=groups.find(g=>slug==='topic/'+g[0]);
   const paperBranch=`<a class="panel reading-card" href="#cvid/topic/papers"><h2>${zh?'论文解读':'Paper explainers'}</h2><p>${zh?'逐篇了解研究问题、发现与局限':'Explore questions, findings and limitations'} · ${explainers.length} ${zh?'篇文章':'articles'}</p><span>→</span></a>`;
   const overview=group?.[0]==='genetics'?`<div class="genetics-overview">${cards(articles.filter(a=>a.slug==='genetics'))}</div>`:'';
   const items=group?articles.filter(a=>group[3].includes(a.slug)&&!(group[0]==='genetics'&&a.slug==='genetics')):[];
   return `<section class="page-shell education-library"><a href="#cvid">← ${zh?'了解 CVID':'Understand CVID'}</a><h1>${group?(zh?group[2]:group[1]):(zh?'从哪里开始了解？':'Where would you like to begin?')}</h1>${overview}<div class="angle-grid learning-groups ${group?'article-three-columns':''}">${group?cards(items)+(group[0]==='research'?paperBranch:''):groups.map(([id,en,cn,slugs])=>`<a class="panel reading-card" href="#cvid/topic/${id}"><h2>${zh?cn:en}</h2><p>${zh?'按主题逐步阅读':'Explore this topic step by step'} · ${slugs.length} ${zh?'篇文章':'articles'}${id==='research'?(zh?'及论文解读':' and paper explainers'):''}</p><span>→</span></a>`).join('')}</div></section>`;
 }

 const article=articles.find(a=>a.slug===slug);
 if(!article)return `<section class="page-shell"><a href="#cvid">${zh?'返回科普目录':'Return to the learning hub'}</a></section>`;
 const figure=articleFigures[slug];
 const blocks=article.blocks;
 const insertAt=figure?Math.max(0,blocks.findIndex(b=>b.type!=='heading'&&figure[1].test(b.text))):-1;
 const illustration=figure?`<figure><img src="education/assets/${figure[0]}" alt="${esc(figure[zh?2:3])}"><figcaption>${esc(figure[zh?2:3])}</figcaption></figure>`:'';
 const body=blocks.map((b,i)=>(b.type==='heading'?`<h2 id="reading-${i}">${esc(b.text)}</h2>`:`<p>${esc(b.text).replaceAll('\\n','<br>')}</p>`)+(i===insertAt?illustration:'')).join('');
 return `<section class="page-shell education-article"><a class="back-link" href="#cvid">← ${zh?'了解 CVID':'Learn about CVID'}</a><h1>${esc(article.title)}</h1><p class="article-lead">${esc(article.excerpt)}</p><article>${body}<h2>${zh?'参考资料':'References'}</h2><ol>${article.sources.map(s=>`<li>${esc(s)}</li>`).join('')}</ol></article><h2>${zh?'继续阅读':'Continue reading'}</h2><div class="angle-grid">${cards(articles.filter(a=>a.slug!==slug&&a.category===article.category))}</div></section>`;
}
