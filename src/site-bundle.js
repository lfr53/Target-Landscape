/* Generated from source modules by work/build-preview.cjs. */
(function(){
'use strict';
const modules={"src/main.js": function(require, exports) {
const { homepage, patientEntry, localizeNavigation } = require("src/final-homepage.js");
const { patientForm, bindPatientForm } = require("src/patient-form.js");
const { exploration, bindExploration } = require("src/exploration.js");
const { educationView } = require("src/education-view.js");
const { directory, extraProjects } = require("src/network-directory.js");
const { bindDirectory } = require("src/expanded-teams.js");
const research=[
{id:'nih-cvid-natural-history',title:'Studies of Immune Regulation in Patients with CVID and Related IEI',institution:'National Institute of Allergy and Infectious Diseases, NIH',country:'United States',status:'Recruiting',types:['Natural history','Observational','Family study'],diagnoses:['cvid','antibody_deficiency','suspected_iei'],features:['recurrent_infections','gi_disease','glild','autoimmunity'],who:'People with CVID, related antibody deficiencies or repeated infections suspected of IEI. Some unaffected relatives may also participate.',question:'Understanding causes, immune abnormalities and long-term progression across pulmonary, gastrointestinal, liver and autoimmune complications.',participation:'Clinical assessments · blood sampling · immune studies · imaging · family comparison samples',source:'NIH Clinical Center / ClinicalTrials.gov'},
{id:'bologna-id-type',title:'Immunodysregulation as an Expression of Underlying Inborn Errors of Immunity',institution:'IRCCS Azienda Ospedaliero-Universitaria di Bologna',country:'Italy',status:'Recruiting',types:['Observational','Genetics','Cohort'],diagnoses:['suspected_iei','antibody_deficiency','cvid'],features:['autoimmunity','lymphoproliferation','recurrent_infections'],who:'Children and adults with confirmed or suspected IEI, particularly people showing immune dysregulation.',question:'Characterising people with suspected or confirmed IEI and identifying underlying immune abnormalities.',participation:'Immunoglobulin testing · immune-cell phenotyping · vaccine response · genetic panels',source:'ClinicalTrials.gov / CenterWatch'},
{id:'cincinnati-abcvild',title:'Abatacept for CVID With Interstitial Lung Disease',institution:"Cincinnati Children's Hospital Medical Center",country:'United States',status:'Recruiting',types:['Clinical trial'],diagnoses:['cvid'],features:['glild'],who:'People with CVID and interstitial lung disease / GLILD meeting study criteria.',question:'Investigating treatment-associated immune changes in CVID-associated interstitial lung disease.',participation:'Treatment intervention · pulmonary evaluation · immune monitoring',source:'ClinicalTrials.gov'},
{id:'freiburg-arise',title:'Abatacept Restores Immune System Equilibrium',institution:'University Medical Center Freiburg',country:'Germany',status:'Completed',types:['Clinical trial'],diagnoses:['cvid'],features:['glild'],who:'Adults with CVID or related disorders and interstitial lung or granulomatous disease.',question:'Historical research into restoration of immunological balance during abatacept treatment.',participation:'Historical study record',source:'EU Clinical Trials Register'},
{id:'esid-unpad',title:'Unclassified Antibody Deficiency Study (unPAD)',institution:'ESID Registry',country:'Europe',status:'Recruiting',types:['Registry','Observational','Cohort'],diagnoses:['antibody_deficiency','cvid'],features:['recurrent_infections'],who:'People with less well-characterised hypogammaglobulinaemia, including specific antibody deficiency, IgA/IgG subclass deficiency and selective IgM deficiency.',question:'Characterising poorly understood antibody-deficiency phenotypes and comparing them with CVID.',participation:'Registry / cohort participation',source:'ESID Registry'}];
const researchers=[['nih-team','NIH CVID / related IEI research team','National Institute of Allergy and Infectious Diseases, NIH','Natural history · immune regulation'],['bologna-team','Bologna ID-TYPE research team','IRCCS Bologna, Italy','Suspected IEI · immunodysregulation · genetics'],['helen-leavis','Dr Helen L. Leavis','University Medical Center Utrecht','CVID enteropathy · multicentre cohorts'],['robert-yellon','Dr Robert L. Yellon','UK CVID research team','CVID · inflammation · patient involvement'],['david-lowe','Dr David Lowe','UK CVID research team','CVID · cardiovascular inflammation']];
const demoCases=[{diagnosis:'cvid',features:['glild','autoimmunity'],immune:['low_switched_memory_b'],genetic:'negative'},{diagnosis:'antibody_deficiency',features:['recurrent_infections','splenomegaly'],immune:['low_igg'],genetic:'unknown'},{diagnosis:'cvid',features:['autoimmunity','lymphoproliferation'],immune:['high_cd21low_b'],genetic:'negative'}];
const labels={cvid:'CVID',antibody_deficiency:'Antibody deficiency',suspected_iei:'Suspected IEI',undiagnosed:'No diagnosis yet',recurrent_infections:'Recurrent or severe infections',autoimmunity:'Autoimmunity',lymphadenopathy:'Enlarged lymph nodes',splenomegaly:'Enlarged spleen',glild:'GLILD / lung inflammation',bronchiectasis:'Bronchiectasis',gi_disease:'Chronic gastrointestinal problems',enteropathy:'Enteropathy / malabsorption',lymphoproliferation:'Lymphoproliferation',liver_disease:'Liver disease',malignancy:'Cancer / lymphoma',infection_only:'Mainly infections',low_igg:'Low IgG',low_iga:'Low IgA',low_igm:'Low IgM',poor:'Poor vaccine response',normal:'Normal vaccine response',low_switched_memory_b:'Low switched-memory B cells',high_cd21low_b:'Increased CD21low B cells',negative:'Genetic testing negative',unknown:'Genetic testing unknown'};
let state={answers:{},step:0};
const q=[['What is your diagnosis?',['cvid','antibody_deficiency','suspected_iei','undiagnosed','other']],['Which of these have been part of your condition?',['recurrent_infections','autoimmunity','lymphadenopathy','splenomegaly','glild','bronchiectasis','gi_disease','enteropathy','lymphoproliferation','liver_disease','malignancy','infection_only']],['Do you know whether any immunoglobulin levels are abnormal?',['low_igg','low_iga','low_igm','high_igm','abnormal_unspecified','normal','unknown']],['Have your vaccine antibody responses been tested?',['not_tested','poor','normal','mixed','unknown']],['Have you had detailed immune-cell testing or flow cytometry?',['yes','no','unknown']],['Have you had genetic testing?',['not_tested','planned','negative','vus','relevant_finding','unknown']],['Does anyone in your family have similar immune, infection or autoimmune problems?',['familial','apparently_sporadic','unknown']],['Which treatments have you received?',['ivig','scig','antibiotic_prophylaxis','steroids','rituximab','immunosuppressant','targeted_therapy','hsct','other','none']],['When did your symptoms begin?',['childhood','adolescence','adulthood','unknown']]];
function tag(v){return `<span class="tag">${labels[v]||v.replaceAll('_',' ')}</span>`} function chips(values=[]){return values.map(tag).join('')}
function shell(title,intro,body){return `<div class="page-shell"><a class="back-link" href="#home">← CVID Compass</a><h1>${title}</h1><p class="section-intro">${intro}</p>${body}</div>`}
function questionnaire(){let [title,opts]=q[state.step];return shell('Find people like me',"A short, private questionnaire. Your answers stay in this browser unless you choose to contribute an anonymous case.",`<div class="panel question-card"><div class="step-meta">QUESTION ${state.step+1} OF ${q.length}</div><h2>${title}</h2><div class="option-grid">${opts.map(o=>`<button class="option ${state.answers[state.step]?.includes(o)?'selected':''}" data-option="${o}">${labels[o]||o.replaceAll('_',' ')}</button>`).join('')}</div><div class="actions"><button class="secondary" id="prev" ${state.step?'':'disabled'}>Back</button><button class="primary" id="next">${state.step===q.length-1?'See my profile':'Continue'}</button></div></div><div class="callout"><b>Privacy by default.</b> No name, date of birth, address, hospital number or free-text medical history is requested.</div>`)}
function profile(){let selected=Object.values(state.answers).flat();let diagnosis=selected.find(x=>['cvid','antibody_deficiency','suspected_iei','undiagnosed'].includes(x))||'undiagnosed';let feats=selected.filter(x=>labels[x]&&![diagnosis].includes(x));let matched=demoCases.filter(c=>c.diagnosis===diagnosis||feats.some(f=>c.features.includes(f)));let related=research.filter(r=>r.diagnoses.includes(diagnosis)||feats.some(f=>r.features?.includes(f)));return shell('Your case profile','Here is a transparent view of the features you chose — not a diagnosis or a medical match score.',`<div class="panel"><div>${tag(diagnosis)}${chips(feats)}</div><p class="fine-print">Shared features help you explore patterns. They do not mean the same diagnosis or clinical equivalence.</p></div><section class="section"><h2>People like me</h2><p class="section-intro">${matched.length?matched.length+' anonymous demo cases share at least one of these features.':'No anonymous cases with this exact combination have been contributed yet.'}</p><div class="card-grid">${matched.slice(0,3).map((c,i)=>`<article class="researcher-card"><b>Anonymous phenotype case ${i+1}</b><p>${chips([c.diagnosis,...c.features,...c.immune,(c.genetic==='negative'?'negative':'unknown')])}</p><span class="fine-print">Shared tags only · no identity exposed</span></article>`).join('')}</div></section><section class="section"><h2>People like me are being studied</h2><div class="card-grid">${related.map(card).join('')}</div></section><section class="section"><h2>People studying these features</h2><div class="card-grid">${researchers.slice(0,3).map(r=>`<article class="researcher-card"><h3>${r[1]}</h3><p>${r[2]}</p><div>${r[3]}</div></article>`).join('')}</div></section><section class="section"><h2>Communities for people like me</h2><div class="panel"><h3>Patient organisations and IEI communities</h3><p>Explore CVID and broader inborn-errors-of-immunity communities through trusted organisations such as Immunodeficiency UK, IPOPI and the Immune Deficiency Foundation.</p></div></section>`)}
function card(r){return `<article class="research-card"><span class="status ${r.status==='Completed'?'completed':''}">${r.status}</span><h3>${r.title}</h3><p><b>${r.institution}</b> · ${r.country}</p><div>${r.types.map(x=>`<span class="tag">${x}</span>`).join('')}</div><div class="why"><b>Who are they studying?</b><br>${r.who}</div><p><b>What are they trying to understand?</b><br>${r.question}</p><p class="fine-print">Participation may involve: ${r.participation}</p><a class="back-link" href="#research/${r.id}">View research →</a>${r.source.startsWith('https://')?`<p><a href="${r.source}" target="_blank" rel="noopener">Source / 公开来源 ↗</a></p>`:''} </article>`}
function researchGroup(title, intro, items){return `<section class="research-group"><div class="eyebrow">Research pathway</div><h2>${title}</h2><p class="section-intro">${intro}</p><div class="card-grid">${items.map(card).join('')}</div></section>`}
function researchPage(){let recruiting=research.filter(r=>r.status==='Recruiting'&&r.types.some(t=>!['Registry','Cohort'].includes(t)));let active=research.filter(r=>r.status==='Active' || r.status==='Unknown');let historical=research.filter(r=>r.status==='Completed');let registries=research.filter(r=>r.types.includes('Registry')||r.types.includes('Cohort'));return shell('Research involving people with similar features','Studies, cohorts and registries remain useful even while the network is growing. They are grouped by what a user can reasonably infer from their status.',`<div class="callout"><b>Research is discovery, not eligibility.</b> A study appearing here means it involves related features; it does not mean you qualify or should change treatment.</div>${researchGroup('Currently recruiting','Open recruitment is indicated in the curated source record. Follow the original source for current details.',recruiting)}${researchGroup('Active research / recruitment unclear','These projects are active or useful for understanding the phenotype, but current recruitment is not confirmed.',active)}${researchGroup('People like me have been studied','Completed research remains visible because it shows where related patient groups and questions have already been investigated.',historical)}${researchGroup('Registries & ongoing cohorts','Registries and cohorts help map less well-characterised antibody-deficiency patterns. Enrolment routes vary by centre.',registries)}`)}
function explore(title){return shell(title,'Use professional phenotype labels to explore anonymous clusters, related research and people studying similar patterns.',`<div class="panel"><h3>Phenotype filters</h3><div class="filters">${['cvid','autoimmunity','lymphoproliferation','splenomegaly','negative'].map(x=>`<button>${labels[x]}</button>`).join('')}</div><button class="primary" id="demo-explore">Apply filters</button></div><section class="section"><h2>Anonymous cases</h2><div class="empty"><h3>3 phenotype-defined demo cases</h3><p>Aggregate patterns are shown without identity or formal patient records. Future contributed cases can be explored using the same shared ontology.</p></div><h2>Related research</h2><div class="card-grid">${research.slice(0,3).map(card).join('')}</div><h2>People studying this</h2><div class="card-grid">${researchers.map(r=>`<article class="researcher-card"><h3>${r[1]}</h3><p>${r[2]}</p><span class="tag">${r[3]}</span></article>`).join('')}</div></section>`)}
function cvidPage(){return shell('Understanding CVID','A patient-facing starting point for understanding the condition before exploring phenotype patterns and research.',`<div class="card-grid"><article class="panel"><h2>What is CVID?</h2><p>Learn how recurrent infections, low immunoglobulins and immune dysregulation can appear together, while recognising that presentations vary.</p></article><article class="panel"><h2>Clinical features</h2><p>Explore lung inflammation / GLILD, bronchiectasis, gastrointestinal disease, lymphoproliferation, autoimmunity, liver disease and malignancy.</p></article><article class="panel"><h2>Immune mechanisms</h2><p>Understand B cells, antibody responses, immune regulation and why apparently similar patients can have different disease patterns.</p></article><article class="panel"><h2>Tests and genetics</h2><p>Read approachable explainers about immunoglobulins, vaccine responses, flow cytometry and genetic findings.</p></article><article class="panel"><h2>Treatment context</h2><p>Review educational information about immunoglobulin replacement and other therapies. This site does not recommend treatment.</p></article><article class="panel"><h2>Family support</h2><p>Find language for discussing family patterns, uncertainty and questions to take to a qualified clinician.</p></article></div><div class="callout"><b>Next step:</b> Once you have a sense of your features, you can explore where people with similar patterns are represented in cases, research and communities. <a class="back-link" href="#find">Explore your pattern →</a></div>`)}
function render(){let h=location.hash.slice(1)||'home';let html=h==='home'?homepage(document.documentElement.lang):h.startsWith('article-')?educationView(document.documentElement.lang,h.slice(8)):(h.startsWith('cvid/topic/')||h.startsWith('cvid/paper/'))?educationView(document.documentElement.lang,h.slice(5)):h==='cvid'?educationView(document.documentElement.lang):h==='patients'?patientEntry(document.documentElement.lang):h==='find'?patientForm(q,labels,state.answers,document.documentElement.lang):h==='find/results'?profile():h==='research'?researchPage():h==='clinicians'?exploration('clinician',demoCases,research,labels,document.documentElement.lang):h==='researchers/explore'?exploration('researcher',demoCases,research,labels,document.documentElement.lang):h==='researchers'?directory(document.documentElement.lang,'researchers',researchers):h==='community'?directory(document.documentElement.lang,'community'):h.startsWith('research/')?shell('Research detail','A public research record connected to phenotype tags and its source.',card(research.find(r=>r.id===h.split('/')[1])||research[0])):homepage(document.documentElement.lang);document.querySelector('#app').innerHTML=html;document.querySelectorAll('[data-option]').forEach(b=>b.onclick=()=>{let v=b.dataset.option;state.answers[state.step]=state.answers[state.step]||[];state.answers[state.step]=state.answers[state.step].includes(v)?state.answers[state.step].filter(x=>x!==v):[...state.answers[state.step],v];render()});document.querySelector('#prev')?.addEventListener('click',()=>{state.step--;render()});document.querySelector('#next')?.addEventListener('click',()=>{if(state.step<q.length-1){state.step++;render()}else{location.hash='find/results'}});if(h==='clinicians'||h==='researchers/explore')bindExploration(h==='clinicians'?'clinician':'researcher',render);bindPatientForm(state);bindDirectory();localizeNavigation(document.documentElement.lang);const toggle=document.querySelector('#language-toggle');if(toggle){toggle.textContent=document.documentElement.lang==='zh'?'English':'中文';toggle.onclick=()=>{document.documentElement.lang=document.documentElement.lang==='zh'?'en':'zh';render()}}}
research.push(...extraProjects());
window.addEventListener('hashchange',render);render();

Object.assign(exports, {});
},
"src/final-homepage.js": function(require, exports) {
const { symbol, referenceArtwork, closingPanel } = require("src/reference-visuals.js");
const w=(lang,en,zh)=>lang==='zh'?zh:en;
function homepage(lang='en'){
 const t=(en,zh)=>w(lang,en,zh);
 const roles=[['I’m a patient or family member','我是患者或家属','#patients'],['I’m a clinician','我是临床医生','#clinicians'],['I’m a researcher','我是研究者','#researchers/explore']];
 const angles=[['Cases with shared features','具有共同特征的病例','Explore published cases, case series, cohorts and anonymous network cases with related clinical or immune features.','探索具有相关临床或免疫特征的已发表病例、病例系列、队列和匿名网络病例。','Explore cases','探索病例','#patients'],['Research connected to these features','与这些特征相关的研究','Find natural-history studies, cohorts, genetics projects, registries and clinical trials involving similar patient groups.','查找涉及相似患者群体的自然病程研究、队列、遗传学项目、登记系统和临床试验。','Explore research','探索研究','#research'],['People studying this','研究这些问题的人','Find clinicians, researchers and specialist centres working with related CVID phenotypes.','寻找关注相关 CVID 表型的临床医生、研究者与专科中心。','Explore specialists','探索专业团队','#researchers'],['Communities for people like me','与我相关的社群','Find patient organisations and communities connected to CVID and related immune conditions.','寻找与 CVID 和相关免疫疾病有关的患者组织及社群。','Explore communities','探索社群','#community']];
 return `<section class="hero discovery-hero"><div><div class="eyebrow">${t('A more connected view of CVID','以更多连接了解 CVID')}</div><h1>${t('Connecting the CVID community <span>through shared patterns</span>','以共同的疾病特征，<span>连接 CVID 社群</span>')}</h1><p>${t('Bringing together patients and families, clinicians, and researchers around shared clinical features, immune profiles and research.','围绕共同的临床特征、免疫表现和研究，连接患者与家属、临床医生及研究者。')}</p><div class="hero-actions compact-role-actions">${roles.map(([en,zh,url],i)=>`<a class="button ${i?'secondary':'primary'}" href="${url}">${t(en,zh)}</a>`).join('')}</div><p class="hero-support">${t('Explore CVID through what is already known — from published cases and research cohorts to specialist centres, ongoing studies and, over time, anonymous cases contributed to the network.','从已有知识出发探索 CVID：包括已发表病例、研究队列、专科中心、正在进行的研究，以及未来逐渐汇入网络的匿名病例。')}</p></div>${referenceArtwork(lang)}</section><section class="section prominent-roles"><div class="role-grid">${roles.map(([en,zh,url],i)=>`<a class="role-entry" href="${url}">${symbol(['people','clinician','flask'][i])}<h2>${t(en,zh)}</h2><p>${t(['Understand and explore my condition','Explore a case and related expertise','Explore a case or phenotype'][i],['了解并探索我的情况','探索病例与相关专业团队','探索病例或研究表型'][i])}</p><span>${t('Start exploring','开始探索')} →</span></a>`).join('')}</div></section><section class="section"><div class="eyebrow">${t('Explore CVID from different angles','从不同角度探索 CVID')}</div><h2>${t('Find what’s relevant to you','发现与你相关的内容')}</h2><div class="angle-grid">${angles.map(([en,zh,body,bodyZh,cta,ctaZh,url],i)=>`<article class="panel"><div class="angle-heading">${symbol(['document','chart','centre','people'][i])}<h3>${t(en,zh)}</h3></div><p>${t(body,bodyZh)}</p><a class="back-link" href="${url}">${t(cta,ctaZh)} →</a></article>`).join('')}</div></section><section class="section learning-section"><div class="panel education-window"><div><div class="eyebrow">${t('Learn about CVID','了解 CVID')}</div><h2>${t('Build a clearer understanding','建立更清晰的理解')}</h2><p>${t('Understand how CVID is diagnosed, why patients can look very different from one another, and how clinical features, immune findings and genetics fit together.','了解 CVID 如何诊断、为什么患者的表现可能截然不同，以及临床特征、免疫检测和遗传学之间的联系。')}</p><div class="hero-actions"><a class="button primary" href="#cvid">${t('Learn about CVID','了解 CVID')}</a><a class="button secondary" href="#find">${t('Explore a CVID case','探索一个 CVID 病例')}</a></div></div></div>${closingPanel(lang)}</section>`;
}
function patientEntry(lang){const t=(en,zh)=>w(lang,en,zh);return `<div class="page-shell"><h1>${t('Understand and explore my condition','了解并探索我的情况')}</h1><p>${t('Learn about CVID and use what you already know about your symptoms, immune tests, genetics, family history and treatment to explore related cases, research, specialists and communities.','了解 CVID，使用已知的症状、免疫检测、遗传学、家族史和治疗信息，探索相关病例、研究、专业团队及社群。')}</p><div class="hero-actions"><a class="button primary" href="#find">${t('Explore my case','探索我的病例')}</a><a class="button secondary" href="#cvid">${t('Learn about CVID','了解 CVID')}</a></div></div>`}
function localizeNavigation(lang){const t=(en,zh)=>w(lang,en,zh);document.querySelector('.site-header nav').innerHTML=[['CVID','了解 CVID','#cvid'],['Explore Cases','探索病例','#patients'],['Research','研究','#research'],['Researchers','研究团队','#researchers'],['Community','社群','#community']].map(([en,zh,url])=>`<a href="${url}">${t(en,zh)}</a>`).join('');let cta=document.querySelector('#header-explore');if(!cta){cta=document.createElement('a');cta.id='header-explore';cta.className='button primary';cta.href='#find';document.querySelector('.site-header').insertBefore(cta,document.querySelector('#language-toggle'));}cta.textContent=t('Explore my case','探索我的病例');}

Object.assign(exports, {homepage,patientEntry,localizeNavigation});
},
"src/reference-visuals.js": function(require, exports) {
function symbol(type){const paths={people:'<circle cx="16" cy="8" r="4"/><circle cx="6" cy="11" r="3"/><circle cx="26" cy="11" r="3"/><path d="M9 28v-6a7 7 0 0 1 14 0v6ZM1 26v-5a5 5 0 0 1 6-5M31 26v-5a5 5 0 0 0-6-5"/>',clinician:'<path d="M6 3v10a7 7 0 0 0 14 0V3M6 3h3M17 3h3M13 20v3a7 7 0 0 0 14 0v-5"/><circle cx="27" cy="15" r="3"/>',flask:'<path d="M12 2h8M13 2v11L5 27q-1 3 3 3h16q4 0 2-3l-7-14V2M10 21h12"/>',document:'<path d="M6 2h14l6 6v22H6ZM20 2v8h6M11 14h10M11 19h10M11 24h7"/>',chart:'<path d="M4 30V18h5v12M14 30V10h5v20M24 30V3h5v27"/>',centre:'<path d="M3 30V12h8V5h10v8h8v17M11 30V5M21 30V5M14 9h4M16 7v4M14 16h3M14 21h3M7 17v2M25 18v2M14 30v-4h4v4"/>',compass:'<circle cx="16" cy="16" r="12"/><path d="M16 1v5M16 26v5M1 16h5M26 16h5M22 10l-4 9-8 3 4-9Z M14 13l4 6"/>',heart:'<path d="M16 28 3 15C-3 2 11 0 16 9 21 0 35 2 29 15Z"/>',bulb:'<path d="M12 23c0-5-6-7-6-13a10 10 0 0 1 20 0c0 6-6 8-6 13M12 25h8M13 29h6M16 1V0"/>'};return `<svg class="reference-icon" viewBox="0 0 32 32" aria-hidden="true">${paths[type]||paths.people}</svg>`;}
function referenceArtwork(lang){const zh=lang==='zh';return `<div class="reference-art live-network"><img src="assets/network-background.png" alt="" draggable="false"><div class="network-centre">${symbol('compass')}<span>${zh?'共同的<br>CVID 特征':'Shared<br>CVID patterns'}</span></div>${[['Patients & Families','患者与家属','#patients','people','Real experiences','真实经历'],['Clinicians','临床医生','#clinicians','clinician','Clinical expertise','临床专长'],['Cases','病例','#patients','document','Published & community cases','已发表与社群病例'],['Research','研究','#research','chart','Cohorts, registries & clinical trials','队列、登记与临床试验'],['Communities','社群','#community','people','Support & connection','支持与连接'],['Researchers','研究团队','#researchers','flask','New discoveries','探索新发现']].map(([en,cn,url,icon,sub,subZh])=>`<a href="${url}">${symbol(icon)}<span><strong>${zh?cn:en}</strong><small>${zh?subZh:sub}</small></span></a>`).join('')}<span class="network-note">${zh?'不同的旅程。<br>更清晰的理解。<br>携手同行。':'Different journeys.<br>A clearer picture.<br>Together.'}</span></div>`;}
function closingPanel(lang){const t=(en,zh)=>lang==='zh'?zh:en;return `<aside class="closing-panel"><div><blockquote>${t('CVID can look different from one person to another. By connecting what we already know, we can move towards earlier recognition, better understanding and new opportunities for research and care.','CVID 在不同人身上的表现可能不同。连接已有知识，帮助我们更早识别、更深入理解，并发现研究与照护的新机会。')}</blockquote><strong>CVID Compass</strong><small>People · Patterns · Progress</small></div><ul><li>${symbol('compass')}${t('More connections','更多连接')}</li><li>${symbol('bulb')}${t('More understanding','更多理解')}</li><li>${symbol('heart')}${t('A stronger community','更紧密的社群')}</li></ul></aside>`;}

Object.assign(exports, {symbol,referenceArtwork,closingPanel});
},
"src/patient-form.js": function(require, exports) {
function patientForm(q,labels,answers,lang){const t=(en,zh)=>lang==='zh'?zh:en;const titles=['Diagnosis','Clinical features','Immunoglobulins','Vaccine response','Immune-cell testing','Genetics','Family history','Treatment history','Age / onset'];const zhTitles=['诊断','临床表现','免疫球蛋白','疫苗应答','免疫细胞检测','遗传学','家族史','治疗史','年龄 / 起病阶段'];return `<div class="page-shell"><h1>${t('Explore my case','探索我的病例')}</h1><p>${t('Add what you already know. Leave anything you are unsure about blank.','填写你已经知道的信息。不确定的项目可以留空。')}</p><a class="back-link" href="#cvid">${t('Learn about CVID','了解 CVID')} →</a><div class="patient-form-grid">${q.map(([question,options],i)=>`<fieldset class="panel"><legend>${lang==='zh'?zhTitles[i]:titles[i]}</legend><div class="option-grid">${options.map(o=>`<label class="option"><input type="${[1,2,7].includes(i)?'checkbox':'radio'}" name="dimension-${i}" data-question="${i}" value="${o}" ${answers[i]?.includes(o)?'checked':''}> ${labels[o]||o.replaceAll('_',' ')}</label>`).join('')}</div></fieldset>`).join('')}</div><div class="hero-actions"><button class="primary" id="explore-profile">${t('Explore my profile','探索我的档案')}</button></div></div>`;}
function bindPatientForm(state){document.querySelectorAll('[data-question]').forEach(input=>input.onchange=()=>{const i=Number(input.dataset.question);state.answers[i]=[...document.querySelectorAll(`[data-question="${i}"]:checked`)].map(el=>el.value)});const submit=document.querySelector('#explore-profile');if(submit)submit.onclick=()=>location.hash='find/results';}

Object.assign(exports, {patientForm,bindPatientForm});
},
"src/exploration.js": function(require, exports) {
const selections = { clinician: [], researcher: [] };
function caseValues(c) { return [c.diagnosis, ...c.features, ...c.immune, c.genetic]; }
function selectCases(cases, filters) {
  return cases.filter(c => filters.every(f => caseValues(c).includes(f)));
}
function distribution(cases, field) {
  const counts = new Map();
  cases.forEach(c => {
    const values = Array.isArray(c[field]) ? c[field] : [c[field] || 'not_recorded'];
    [...new Set(values.length ? values : ['not_recorded'])].forEach(v => counts.set(v, (counts.get(v) || 0) + 1));
  });
  return [...counts].sort((a,b) => b[1]-a[1]);
}
function exploration(mode, cases, projects, labels, lang) {
  const zh = lang === 'zh';
  const t = (en,cn) => zh ? cn : en;
  const chosen = selections[mode];
  const found = selectCases(cases, chosen);
  const name = v => ({not_recorded:t('Not recorded','未记录'),cvid:'CVID',autoimmunity:t('Autoimmunity','自身免疫'),glild:t('GLILD','肺部炎症 / GLILD'),negative:t('No relevant genetic finding','未发现相关遗传结果'),unknown:t('Unknown','未知'),lymphoproliferation:t('Lymphoproliferation','淋巴增殖'),splenomegaly:t('Splenomegaly','脾大'),low_switched_memory_b:t('Low switched-memory B cells','转换记忆 B 细胞减少'),high_cd21low_b:t('Increased CD21low B cells','CD21low B 细胞增多'),antibody_deficiency:t('Antibody deficiency','抗体缺陷'),recurrent_infections:t('Recurrent infections','反复感染'),low_igg:t('Low IgG','IgG 降低')}[v] || labels[v] || v);
  const groups = [
    [t('Diagnosis','诊断'), ['cvid','antibody_deficiency','suspected_iei','undiagnosed']],
    [t('Clinical features','临床表现'), ['autoimmunity','glild','lymphoproliferation','splenomegaly','recurrent_infections']],
    [t('Immune findings','免疫检测'), ['low_switched_memory_b','high_cd21low_b','low_igg']],
    [t('Genetic testing','遗传检测'), ['negative','unknown']]
  ];
  const chart = (heading, field) => `<article class="panel"><h3>${heading}</h3>${found.length ? distribution(found,field).map(([v,n])=>`<div class="distribution-row"><span>${name(v)}</span><strong>${n} / ${found.length}</strong><meter min="0" max="${found.length}" value="${n}" aria-label="${name(v)}"></meter></div>`).join('') : `<p>${t('No cases in this group.','当前群体暂无病例。')}</p>`}</article>`;
  const related = projects.filter(p => !chosen.length || chosen.some(v=>[...p.diagnoses,...p.features].includes(v)));
  const projectList = related.map(p=>`<article class="panel"><div>${p.types.join(' · ')}</div><h3>${p.title}</h3><p>${p.institution}</p><p>${t('Shared features','共同特征')}: ${chosen.filter(v=>[...p.diagnoses,...p.features].includes(v)).map(name).join(' · ') || t('Browse all research','浏览全部研究')}</p><a class="back-link" href="#research/${p.id}">${t('View research','查看研究')} →</a></article>`).join('');
  const institutions = [...new Set(related.map(p=>p.institution))];
  return `<div class="page-shell"><a class="back-link" href="#home">← CVID Compass</a><h1>${mode==='clinician'?t('Explore similar cases','探索相似病例'):t('Explore patient groups','探索患者群体')}</h1><p class="section-intro">${mode==='clinician'?t('Have you seen a case like mine? Start with the findings in one case.','有没有人见过类似的病例？从一个病例的检测结果和临床表现开始。'):t('Where are the patients with the phenotype I want to study? Define the group below.','我想研究的表型对应哪些患者？在下方定义你关注的群体。')}</p>
  <div class="panel"><h2>${mode==='clinician'?t('Features of your case','病例特征'):t('Define your group','定义研究群体')}</h2>${groups.map(([title,values])=>`<fieldset><legend>${title}</legend><div class="filters">${values.map(v=>`<button data-phenotype="${v}" aria-pressed="${chosen.includes(v)}" class="${chosen.includes(v)?'active':''}">${name(v)}</button>`).join('')}</div></fieldset>`).join('')}<button class="secondary" data-clear-filters>${t('Clear filters','清除筛选')}</button><p>${t('Cases must contain every selected feature. Counts update as you select.','病例须包含所有已选特征；数量随筛选更新。')}</p></div>
  <p class="demo-notice">${t('Illustrative demo cases only — these counts do not represent contributed patients. Family links and treatment responses have not been recorded.','仅为虚构演示病例，数量不代表真实贡献的患者。尚未记录家族关联与治疗反应。')}</p>
  <section aria-live="polite"><h2>${mode==='clinician'?t('Similar anonymous cases','相似匿名病例'):t('Group overview','群体概况')}</h2><div class="card-grid"><article class="panel"><h3>${t('Case count','病例数')}</h3><strong>${found.length}</strong></article>${mode==='researcher'?`<article class="panel"><h3>${t('Family cluster count','家族簇数量')}</h3><strong>${t('Not available','暂无数据')}</strong><p>${t('Family clusters require recorded relationships; familial cases alone do not establish a cluster.','家族簇需有已记录的亲属关联，不能将有家族史的病例直接计作家族簇。')}</p></article>`:''}</div>
  ${!found.length?`<div class="empty">${t('No anonymous cases with this combination yet. Related research and centres are listed below.','暂未有包含这一组合的匿名病例。下方仍可探索相关研究和中心。')}</div>`:''}
  ${mode==='clinician'?`<div class="card-grid">${found.map(c=>`<article class="panel"><h3>Demo ${cases.indexOf(c)+1}</h3>${caseValues(c).map(v=>`<span class="tag">${name(v)}</span>`).join('')}</article>`).join('')}</div><div class="panel"><h3>${t('Features shared across these cases','这些病例的共同特征')}</h3>${found.length?distribution(found,'features').filter(([,n])=>n===found.length).map(([v])=>`<span class="tag">${name(v)}</span>`).join('') || t('No clinical feature is shared by every case.','没有所有病例都具备的临床表现。'):t('Select a broader set of cases to compare.','请放宽筛选以比较病例。')}</div>`:`<div class="card-grid">${chart(t('Phenotype distribution','表型分布'),'features')}${chart(t('Genetics status distribution','遗传检测状态分布'),'genetic')}${chart(t('Treatment-response distribution','治疗反应分布'),'treatmentResponses')}</div><p>${t('A case may have several clinical features.','一个病例可具有多种临床表现。')}</p>`}</section>
  <section><h2>${mode==='clinician'?t('Related research projects & cohorts','相关研究项目与队列'):t('Existing cohorts, trials & registries','已有队列、试验与登记系统')}</h2><div class="card-grid">${projectList || t('No curated research shares these filters.','现有研究条目暂无共同的筛选特征。')}</div></section>
  <section><h2>${mode==='clinician'?t('Researchers & specialist centres','研究团队与专科中心'):t('Related clinicians & centres','相关临床团队与中心')}</h2><div class="card-grid">${institutions.map(i=>`<article class="panel"><h3>${i}</h3>${related.filter(p=>p.institution===i).map(p=>`<p><a class="back-link" href="#research/${p.id}">${p.title} →</a></p>`).join('')}</article>`).join('')}</div></section></div>`;
}
function bindExploration(mode, rerender) {
  document.querySelectorAll('[data-phenotype]').forEach(button => button.onclick = () => {
    const v = button.dataset.phenotype;
    selections[mode] = selections[mode].includes(v) ? selections[mode].filter(x=>x!==v) : [...selections[mode],v];
    rerender();
    document.querySelector(`[data-phenotype="${v}"]`)?.focus();
  });
  const reset = document.querySelector('[data-clear-filters]');
  if(reset) reset.onclick = () => { selections[mode] = []; rerender(); };
}

Object.assign(exports, {selections,caseValues,selectCases,distribution,exploration,bindExploration});
},
"src/education-view.js": function(require, exports) {
const { articleFigures } = require("src/article-figures.js");
const { explainers, explainerBody } = require("education/src/research-explainers.js");
const { englishArticles } = require("education/src/content-en.js");
const { chineseArticles } = require("education/src/content-zh.js");
const esc=v=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function educationView(lang,slug){
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

Object.assign(exports, {educationView});
},
"src/article-figures.js": function(require, exports) {
const articleFigures={
      'multi-organ':['immune-organs-v2.png',/免疫|immun/i,'抗体防御不足与免疫调节失衡是两条可重叠的路径。感染可能损伤气道；炎症及自身免疫也可影响组织。天平仅代表调节失衡，并非两类 T 细胞的数量比较。','Reduced antibody protection and immune dysregulation can overlap. Infections may damage airways, while inflammation and autoimmunity can affect tissues. The balance is a metaphor, not a comparison of two T-cell counts.'],
      genetics:['gene-protein-function-v2.png',/基因|gene/i,'以确认的 BAFF-R 缺陷为例：某些致病变异影响 B 细胞存活信号和成熟。这不是所有 CVID 的共同病因，遗传结果需结合具体变异与临床证据解释。','Confirmed BAFF-R deficiency illustrates how disease-causing variants can impair B-cell survival and maturation. It is not a universal cause of CVID; interpretation depends on the variant and clinical evidence.'],
      infection:['plasma-antibodies-v2.png',/浆细胞|Plasma cells/i,'以依赖 T 细胞帮助的应答为例：B 细胞识别抗原后激活、增殖和成熟，产生分泌抗体的浆细胞及参与再次应答的记忆 B 细胞。','A simplified T-cell-dependent response: B cells recognise antigen, activate, expand and mature, generating antibody-secreting plasma cells and memory B cells for later responses.'],
      'tnfrsf13b-taci':['receptor-signal-v2.png',/TACI/,'BAFF/APRIL 与 TACI 结合后，可通过包括 MyD88 在内的胞内信号支持抗体类别转换；这一过程需要其他信号配合。图示不是分子真实结构。','BAFF/APRIL binding to TACI can support antibody class switching through intracellular signals including MyD88, together with other signals. Shapes are schematic, not molecular structures.'],
      'immunoglobulin-replacement':['immunoglobulin-replacement-v2.png',/IgG|免疫球蛋白|antibod/i,'补充的 IgG 支持抗感染防御，但不会直接修复 B 细胞成熟或所有免疫调节环节。','Replacement IgG supports infection defence but does not directly repair B-cell maturation or every immune-regulatory pathway.'],
      'research-participation':['patient-registry-v2.png',/登记|registr/i,'在知情同意下长期记录感染、治疗和器官健康，可帮助描述病程与规划研究；观察到的关联不等于治疗因果关系。','With informed consent, longitudinal records of infections, treatment and organ health help describe disease patterns and plan research. Associations do not establish treatment causation.']
    };

Object.assign(exports, {articleFigures});
},
"education/src/research-explainers.js": function(require, exports) {
// Editorial explanations, with primary-source links and explicit study boundaries.
const { addResearchDepth } = require("education/src/research-depth.js");
const { completeEnglishExplainers } = require("education/src/research-parity.js");
const explainers = [
{
 date:'2026-01-13',type:['人体样本机制研究','Human-sample mechanistic study'],sample:['114 名 CVID 患者；21 名健康对照；各分析样本数不同','114 participants with CVID; 21 controls; assay subsets vary'],
 title:['抗体不足，为什么还会发炎？从 IgA 和肠道屏障寻找答案','Why can antibody deficiency coexist with inflammation? Clues from IgA and the gut'],
 paper:'IgA defects in CVID lead to bacterial translocation, increased serum γ-interferon, and BAFF',
 source:'https://pmc.ncbi.nlm.nih.gov/articles/PMC12829748/',
 intro:['一项 2026 年研究把 IgA、肠道微生物成分和免疫激活联系起来，为 CVID 的炎症表现提供了一条值得继续验证的机制线索。','A 2026 study connects low IgA, microbial material and immune activation, offering a mechanism to investigate further.'],
 sections:[
 ['从患者关心的问题出发','The patient question','免疫球蛋白替代治疗帮助许多人减少感染，但部分患者仍有肠道、肺部或自身免疫问题。研究人员因此追问：炎症是否可能与抗体防御缺口有关，而不是完全独立的另一件事？这篇论文关注的正是抗体不足与免疫过度活跃之间的联系。','Why can inflammation persist when infection prevention improves? This study investigates a possible connection between the antibody deficit and excessive immune activation.'],
 ['IgA 在哪里发挥作用？','Where does IgA fit?','IgA 是黏膜防御的重要成员。可以把肠道想成一个既要吸收营养、又要管理微生物接触的界面。研究中的假设是：IgA 缺失与黏膜屏障缺陷一起，可能让更多微生物成分进入身体，持续刺激免疫系统。血液中检测到细菌 DNA，并不等于发生了活菌引起的血流感染。','IgA helps contain microbes at mucosal surfaces. Reduced containment could increase exposure to microbial material. Detecting bacterial DNA is not the same as diagnosing a bloodstream infection.'],
 ['研究怎样寻找线索？','How the researchers investigated','团队分析 CVID 患者与健康对照的血液样本，比较 IgA、类别转换记忆 B 细胞、细菌 16S DNA，以及 IFN-γ、CXCL9 和 BAFF 等指标。它们分别提供抗体记忆、微生物暴露和免疫激活的信息；并非所有指标都在全部参与者中完成。','Blood analyses examined IgA, switched-memory B cells, bacterial DNA and inflammatory mediators, including IFN-γ and BAFF. Different assays used different subsets.'],
 ['发现如何连成一条线？','Connecting the findings','较低的 IgA 和较少的类别转换记忆 B 细胞，与较高的细菌 DNA 或炎症信号相关。作者提出一条解释：黏膜防御不足增加微生物暴露，继而促进 IFN-γ 和 BAFF 等信号。BAFF 有助于 B 细胞存活，但信号失去平衡时可能参与免疫失调。这里呈现的是研究支持的机制框架，不是每位患者都相同的固定过程。','The associations support a proposed sequence: impaired containment, microbial exposure and inflammatory signalling. They do not establish that this sequence explains every patient.'],
 ['这项发现离治疗还有多远？','What remains to be tested','论文提出了围绕黏膜防御开展治疗研究的可能性，但没有检验补充 IgA 能否安全有效地改善 CVID。观察到相关性，也不能完整证明先后顺序或因果关系。它的价值是把下一项实验和临床研究的问题变得更具体，而不是提供一项现在就可以自行尝试的治疗。','No IgA treatment benefit was tested. Timing, causality and therapeutic safety need further study. The contribution is a more specific research hypothesis.']
 ]},
{
 date:'2022-04-01',type:['单细胞多组学机制研究','Single-cell multi-omics'],sample:['一对同卵双胞胎起始研究，并以独立患者与对照队列验证','Discovery in one discordant twin pair, with patient/control validation'],
 title:['同样的遗传起点，B 细胞为什么走向不同？','Why can B cells behave differently despite a shared genetic starting point?'],
 paper:'Single-cell Atlas of common variable immunodeficiency shows germinal center-associated epigenetic dysregulation in B-cell responses',
 source:'https://www.nature.com/articles/s41467-022-29450-x',
 intro:['这项代表性机制研究逐个观察细胞，追踪 B 细胞形成免疫记忆时，基因的使用方式发生了什么变化。','A foundational mechanistic study examines how gene regulation changes as B cells develop immune memory.'],
 sections:[
 ['为什么从双胞胎开始？','Why study twins?','研究从一对同卵双胞胎出发，其中一人患有 CVID，另一人没有。相近的遗传背景使研究者能更集中地观察：除了 DNA 序列，细胞怎样使用基因，是否也是疾病差异的一部分？这是一种寻找机制的研究设计，不能用一对双胞胎代表所有患者。','A twin pair discordant for CVID offered a way to examine differences beyond inherited sequence. One pair cannot represent all patients.'],
 ['基因的使用方式是什么意思？','What is gene regulation?','DNA 可以比作一本说明书，但不同细胞不会同时阅读所有章节。DNA 甲基化、染色质开放程度和基因转录，影响哪些信息在某个阶段被使用。它们共同构成调控层面的线索。研究这些变化，不等于已经发现了一个致病突变，也不意味着疾病由个人生活方式造成。','Cells regulate which genetic instructions are accessible and used. Epigenetic changes are not equivalent to a new mutation, and do not imply personal blame.'],
 ['为什么要逐个观察细胞？','Why examine individual cells?','一管血液里混合了多种免疫细胞。把它们全部平均，可能掩盖某一小群细胞的问题。团队结合单细胞 DNA 甲基化、染色质和 RNA 信息，把初始 B 细胞与不同记忆 B 细胞分开比较，并进一步观察细胞受到激活后的反应。','Single-cell measurements separate cell populations that bulk blood averages can conceal. The team compared naïve and memory B cells and their responses to activation.'],
 ['研究看到了什么？','What did it reveal?','异常尤其集中于记忆 B 细胞：一些本应在成熟过程中调整的调控状态没有按预期改变，并伴随基因表达及细胞间通信异常。后续患者与对照分析支持部分发现。它提示，CVID 的问题可能不只是细胞数量少，也涉及细胞能否完成成熟和协作。','Memory B cells showed regulatory and transcriptional abnormalities associated with altered communication. Patient/control analyses supported selected findings.'],
 ['对理解 CVID 有什么价值？','Why it matters','这项研究解释了为何“找不到单个致病基因”不等于“没有生物学原因”。不过，细胞状态也可能受到既往疾病和治疗影响，因果顺序仍需研究。现阶段它属于机制探索，尚不能凭这套图谱为个人制定治疗或预测未来。','It expands the biological questions beyond single-gene explanations. Causality and clinical prediction remain unresolved; this is not a treatment-selection test.']
 ]},
{
 date:'2024-01-11',type:['单中心临床与遗传队列','Single-centre clinical/genetic cohort'],sample:['405 名 CVID 患者','405 people with CVID'],
 title:['能从症状猜出基因吗？405 名患者带来的提醒','Can symptoms identify a genetic cause? Lessons from 405 people'],
 paper:'Genetics and clinical phenotypes in common variable immunodeficiency',
 source:'https://www.frontiersin.org/journals/genetics/articles/10.3389/fgene.2023.1272912/full',
 intro:['把临床表现和遗传发现放在一起，既能寻找规律，也能看清“有某种症状就对应某个基因”的局限。','Clinical and genetic findings can reveal patterns, but symptoms do not map neatly onto individual genes.'],
 sections:[
 ['为什么这个问题很实际？','Why this question matters','同样被诊断为 CVID，有人主要反复感染，有人还有自身免疫、肺病或肠病。患者自然会问：这些差异能不能告诉我，是哪一个分子出了问题？研究人员把一个中心 405 名患者的临床和遗传信息放在一起，专门分析这种联系。','People with the same diagnosis can have very different complications. This cohort examined whether clinical patterns help identify a genetic explanation.'],
 ['研究比较的是什么？','What was compared?','团队比较有遗传发现与没有已知遗传原因患者的疾病表现，包括自身免疫和多种器官并发症。这类研究观察已有患者之间的差异，没有随机分配治疗，因此它回答的是“哪些特征一起出现”，而不是“哪种治疗更好”。','The investigators compared complications across genetic groups. This was observational analysis, not a randomized treatment comparison.'],
 ['遗传线索有价值，但不是症状密码','Useful clues, not a symptom code','队列中可以识别一部分遗传缺陷，但不同遗传背景的患者仍有重叠表现。研究强调临床表现与具体基因的联系并不紧密。某种器官表现可能让团队更关注遗传评估，却不能单独锁定一个基因；相反，没有典型表现也不能简单排除遗传原因。','Clinical patterns overlapped. A feature can motivate investigation without uniquely identifying a gene or excluding a genetic explanation when absent.'],
 ['为什么变异需要再解释？','Why interpretation still matters','报告上的变异，需要与遗传方式、家族信息、免疫检查和功能证据放在一起。某些风险相关变异和明确致病缺陷也不能混为一谈。特别是 TACI 相关结果，需要谨慎区分易感因素与足以解释疾病的证据。','Variant interpretation requires inheritance, clinical context and functional evidence. Susceptibility variants, including some TACI findings, need particular care.'],
 ['患者可以带走的认识','What this adds to understanding','更具体的遗传诊断可以帮助理解免疫通路，但不能替代随访中对真实表现的观察。单中心人群还会受到转诊和检测选择影响，不能把该队列的比例当作每个人找到基因的概率。这篇研究最有用的提醒是：临床与遗传信息应相互补充。','Genetics complements clinical follow-up. Referral and testing patterns limit generalisation; cohort percentages are not an individual probability of finding a cause.']
 ]},
{
 date:'2025-07-17',type:['国际患者登记研究','International registry report'],sample:['30,628 名 IEI 患者；194 个中心','30,628 people with IEI; 194 centres'],
 title:['每个人的长期经历，怎样汇成罕见病的证据？','How do individual experiences become evidence for rare diseases?'],
 paper:'Inborn errors of immunity: Manifestation, treatment, and outcome—an ESID registry 1994–2024 report on 30,628 patients',
 source:'https://pubmed.ncbi.nlm.nih.gov/41347188/',
 intro:['ESID 登记报告展示了患者与中心长期参与的意义：让分散在不同地方的诊疗经历，有机会共同回答更大的问题。','The ESID report illustrates how sustained participation helps centres learn from experiences spread across many countries.'],
 sections:[
 ['一个中心看不到的全貌','Beyond one centre','罕见病患者分散在不同医院。即使一个团队经验丰富，也可能只有少数某种表现的患者，很难观察到足够多的长期变化。登记系统把不同中心的数据按相对一致的方式汇集，让少见的疾病和结局更容易被研究。','Individual centres may see too few cases to understand uncommon patterns. Registries allow experiences to be considered together.'],
 ['这篇报告汇集了什么？','What this report assembled','这份 ESID 报告覆盖 1994—2024 年登记资料，涉及 194 个中心的 30,628 名先天性免疫错误患者，整理疾病表现、治疗与结局。这里包括多类免疫疾病，不能把全部人数称为 CVID 患者，也不能把整体数据直接套在 CVID 个体身上。','The 1994–2024 report covers manifestations, treatment and outcomes across many IEI diagnoses. Its full population is not a CVID cohort.'],
 ['长期记录为什么有价值？','Why follow-up matters','一次检查告诉我们一个时间点的情况。持续记录则有机会显示：诊断用了多久，哪些并发症后来出现，不同人接受了哪些治疗，以及长期结局有什么差异。它可以帮助形成更具体的研究问题，也为以后设计研究提供现实背景。','Repeated records can describe diagnostic delays and evolving outcomes. Such observations help formulate research questions and future studies.'],
 ['登记资料也有盲区','Where uncertainty remains','参与中心并不等于所有医院，登记患者也不等于所有患者。资料可能缺失，各地检查、转诊和记录方式也有差异。登记中两件事同时出现，并不证明其中一件造成另一件；治疗比较还可能受到病情轻重的影响。','Missing data and differences in referral, recording and illness severity limit comparisons. Associations do not by themselves establish treatment effects.'],
 ['参与可以从了解开始','Participation can begin with learning','研究参与不只有尝试新药。患者登记、自然病程观察、样本研究都可能帮助疾病认识向前推进。可以先阅读研究说明，了解要提供什么、花多少时间、资料怎样使用，再决定是否参与。你写下的经历有价值，而是否分享、分享多少，仍由你作出知情选择。','Registries and natural-history studies are also forms of participation. Read the study information, expected commitments and data-use arrangements before deciding.']
 ]}
];
addResearchDepth(explainers);
completeEnglishExplainers(explainers);
function explainerCardData(en=false){return explainers.map(x=>({date:x.date,type:x.type[en?1:0],sample:x.sample[en?1:0],title:x.title[en?1:0],finding:x.intro[en?1:0],source:x.source}));}
function explainerBody(index,en=false){const x=explainers[index];if(!x)return '';return x.sections.map(s=>'<section><h2>'+s[en?1:0]+'</h2><p>'+s[en?3:2]+'</p></section>').join('')+'<section><h2>'+(en?'Original paper':'原始论文')+'</h2><p>'+x.paper+'</p><a href="'+x.source+'" target="_blank" rel="noopener">'+(en?'Read the source ↗':'查看原文 ↗')+'</a></section>';}

Object.assign(exports, {explainers,explainerCardData,explainerBody});
},
"education/src/research-depth.js": function(require, exports) {
// Additional patient context: distinguish explanatory background from paper findings.
function addResearchDepth(items) {
 const additions = [
 [
 ['为什么“抗体少”和“免疫活跃”并不矛盾？','Why low antibodies and immune activation can coexist','抗体不是免疫系统的全部。它们有助于限制病原体和微生物成分的接触，而感受这些成分的细胞仍可能被激活。可以把这理解为一道防线不够严密，后面的警报系统却仍在工作，甚至持续收到刺激。因此，免疫缺陷不等于身体所有免疫反应都低下；炎症也不能简单理解为“免疫力太强”。这段背景有助于理解论文提出的联系，但并不能凭症状确定某位患者正在经历同一过程。','Antibodies are one part of immunity, not a measure of the activity of the whole system. They help limit exposure to microbes and their products. Cells that sense those products may still respond even when antibody protection is inadequate. A useful analogy is an imperfect barrier with an alarm system behind it: a gap in containment may increase the signals reaching that alarm. This explains why deficiency and activation are not logical opposites. It does not establish that this particular mechanism causes a given person’s symptoms.'],
 ['这些指标分别能说明什么？','What the measurements do—and do not—represent','类别转换记忆 B 细胞提示抗体反应经历过某些成熟过程，但不能单靠数量判断全部防御能力。16S DNA 是微生物来源线索，不告诉我们细菌是否仍然存活，也不能独自定位材料来自哪里。IFN-γ、CXCL9 与 BAFF 则反映不同的免疫信号。把它们放在一起，可以提出相互联系的假设；把某一个指标单独拿出来，却很容易把研究发现误当成已经可以用于个人诊断的检验。','Switched-memory B cells provide information about part of the history of an antibody response, rather than a complete measure of protection. Bacterial DNA is a clue to microbial material; it does not establish that living bacteria are present or identify the source by itself. Inflammatory mediators report other aspects of immune activity. Considering several measurements together can support a biological hypothesis. Turning one measurement into an individual diagnostic test would require additional evidence about reliability, interpretation and usefulness.'],
 ['从联系到干预，还差哪些证据？','What would strengthen the explanation?','要判断这条机制是否能成为治疗方向，需要更清楚地观察时间顺序：屏障变化、微生物暴露和炎症信号是否按预期先后出现？还需要在不同患者群体中重复观察，并检验改变某个环节能否改变有意义的结局，例如症状或器官炎症，而不只是改变一个血液指标。这篇论文没有完成这些治疗验证。尤其不能由“低 IgA 与炎症有关”直接推导出补 IgA、用益生菌或改变饮食就能解决问题。','Stronger causal evidence would clarify the order of events and test whether changing a proposed step changes a meaningful outcome. Repeating an association in independent groups is useful, but is still different from demonstrating a safe intervention. A future treatment study would need to examine symptoms, organ outcomes and harms—not only a blood marker. This paper does not show that IgA supplementation, probiotics or a dietary change improves CVID. Its importance is in making a possible connection testable, not in supplying a new self-treatment.']
 ],
 [
 ['“单细胞”为什么不是“只研究一个细胞”？','What single-cell analysis adds','单细胞技术把混合样本拆开，分别读取许多细胞的信息。研究人员可以比较不同成熟阶段，而不是只看一管血的平均值。不过，测到很多细胞不等于研究了很多患者：来自同一位参与者的细胞共享许多背景因素。因此，发现阶段的细胞数量和独立验证的人数回答的是不同问题，都需要注意。','Single-cell methods read many cells separately rather than averaging them together. This can reveal differences between developmental stages or small populations that would otherwise be obscured. However, thousands of measured cells are not thousands of independent patients. Cells from one person share clinical and biological context. The number of people and the number of cells therefore answer different questions about how detailed a result is and how widely it might apply.'],
 ['甲基化、开放程度和 RNA 如何互相补充？','Three views of gene regulation','可以把 DNA 甲基化理解为调控状态的一部分，把染色质开放程度理解为一段信息是否容易被细胞接触，把 RNA 理解为当时正在被读取的信息。这个比喻是简化的：甲基化不是任何位置都等于“关闭”，RNA 变化也不一定最终变成蛋白功能变化。多种读数相互支持，能使机制解释更有说服力，却仍不等于已经证明最初的致病原因。','DNA methylation describes one regulatory layer, chromatin accessibility asks which regions are physically available, and RNA records which instructions are being transcribed. These are complementary views, not interchangeable measurements. Methylation is not a universal off switch, and an RNA difference does not necessarily translate into a corresponding change in protein function. Agreement between layers can strengthen an interpretation while still leaving the original cause uncertain.'],
 ['为什么这篇较早的论文仍值得读？','Why a foundational paper remains useful','这篇论文发表于 2022 年，因此这里把它作为代表性的机制研究，而不是今天刚出现的新发现。它的重要性在于改变观察问题的角度：同样叫 B 细胞，成熟阶段和调控状态可能很不同；没有找到明确单基因原因，也不代表细胞内部没有可研究的变化。这种认识能够帮助理解后续研究，但不能把“表观遗传”解释成患者可以自行纠正的生活习惯问题。','This paper was published in 2022 and is presented as foundational work, not a newly released finding. Its value is the perspective it offers: the label “B cell” contains different stages and regulatory states. An unresolved single-gene explanation does not mean there is no biology to investigate. Equally, epigenetics should not be interpreted as proof that a patient’s habits caused the disease or that an untested lifestyle intervention can reverse it.']
 ],
 [
 ['症状重叠，为什么仍值得寻找机制？','Why mechanisms matter when symptoms overlap','不同通路可能影响同一个结果，例如抗体不足；同一条通路也可能参与几个器官的问题。用症状直接反推基因，就像只凭灯不亮来判断电路里究竟哪个零件坏了：症状指出需要排查，却未必能定位。遗传信息的价值是增加一层解释，而不是用一个基因名字取代完整的临床观察。','Different pathways can lead to a shared outcome, such as reduced antibody production, while one pathway can influence several organs. Working backwards from a symptom is therefore difficult. A symptom can identify something that needs investigation without locating the precise molecular cause. Genetics adds another layer of explanation; it does not replace the clinical history or make every complication a direct consequence of one variant.'],
 ['队列中的比例，为什么不能直接变成个人概率？','Why a cohort percentage is not a personal forecast','一家专科中心收治的人群可能有更复杂的表现，也可能更容易获得某些检测。检测范围、变异判读标准和入组方式都会影响研究中“找到遗传线索”的比例。同样重要的是，报告把什么算作遗传发现：易感变异和证据充分的致病变异并不是同一类信息。因此，讨论自己的检测时，更有用的是明确检测能回答什么，而不是期待复制一个论文百分比。','A specialist centre may see more complex cases and have different access to testing than other services. Test coverage, selection and interpretation affect the proportion with genetic findings. The definition of a finding also matters: susceptibility and a well-supported causal defect are not identical categories. A cohort percentage should not be treated as the chance that any particular reader will receive a molecular diagnosis.'],
 ['结果怎样与长期随访配合？','How genetics and follow-up complement each other','一个明确诊断可能帮助团队关注特定机制、讨论家属评估或寻找相应研究。但是症状是否出现、何时出现、影响到什么程度，仍需要实际随访。暂时没有明确遗传结果的患者，同样需要根据已经存在的表现得到照护。这篇研究支持的是把不同证据拼在一起，而不是把患者分成“有基因所以有答案”和“没基因所以没答案”两组。','A confirmed diagnosis may help focus questions about a pathway, relatives or research opportunities. Follow-up still establishes whether a complication develops and how it affects the person. Someone without a resolved genetic finding still needs care for their actual clinical problems. The useful distinction is not between people with an answer and people without one, but between what each type of evidence can currently explain and what remains uncertain.']
 ],
 [
 ['登记不是把所有经历混成一个平均数','A registry is more than one average','不同疾病、年龄和治疗背景的人不能不加区分地比较。规范的登记需要尽量统一疾病定义、记录项目和时间点，再在适当人群中提出具体问题。例如，了解诊断延迟与研究治疗结局需要不同的分析。大样本能让少见的情况被看见，但不能自动消除资料缺失和人群差异。','People with different diagnoses, ages and treatment histories cannot simply be treated as interchangeable. A useful registry needs consistent definitions, records and timing, followed by an analysis suited to the question. Studying diagnostic delay is different from comparing outcomes after treatment. Large numbers help reveal uncommon experiences, but do not automatically remove missing data or differences between populations.'],
 ['为什么登记不等于试药？','Why a registry is different from a treatment trial','登记通常记录已经发生的诊疗与随访，而临床试验会按照研究方案分配某种干预。两者的目的、额外负担和风险可能不同。一项登记发现可以提示值得开展试验的问题，却不能仅凭记录中某组结局更好，就认定那项治疗一定造成改善。医生选择治疗时本来就会考虑病情，这也会影响结果比较。','A registry commonly records care and follow-up, whereas a clinical trial assigns an intervention under a protocol. Their commitments and risks can differ. Registry observations may identify questions for a trial without proving why one group did better. Treatment choices already depend on illness severity and other characteristics, which can influence later comparisons. This is why observational evidence and intervention testing complement each other.'],
 ['在这个网站表达兴趣，和正式登记有什么区别？','Interest here is not formal enrolment','在网站选择关注方向，只能表达你想进一步了解什么。正式患者登记由具体项目负责，需要说明资料用途、授权范围、退出方式以及适用的伦理和隐私安排。读到一篇登记论文，不代表作者正在通过本站招募；填写演示表单也不会进入 ESID 或其他登记系统。你可以先访问项目官方信息，再决定是否询问研究团队。','Selecting an interest on this website is not enrolment in ESID or another registry. Formal participation is handled by the project and requires its own information and consent process. Reading a report does not mean its authors are recruiting through this site, and our demonstration form does not send information to them. The next step, if you wish, is to read the project’s official information and ask its team about participation.']
 ]
 ];
 additions.forEach((sections,index)=>items[index].sections.push(...sections));
 items.push({
 date:'2023-05-08',type:['系统综述','Systematic review'],sample:['58 项研究；共描述 796 名患者','58 studies describing 796 patients'],
 title:['肺部检查各在寻找什么？读懂 CVID 间质性肺病的研究','What are lung tests looking for? Understanding research on CVID-related lung disease'],
 paper:'Diagnostic testing for interstitial lung disease in common variable immunodeficiency: a systematic review',
 source:'https://www.frontiersin.org/journals/immunology/articles/10.3389/fimmu.2023.1190235/full',
 intro:['CT、肺功能、灌洗和活检不是重复检查。研究梳理了不同检查提供的线索，以及现有证据为何还不能给出适用于所有人的单一方案。','Scans, lung function, lavage and biopsy answer different questions. This review examines the evidence and why it does not yield one universal testing plan.'],
 sections:[
 ['为什么不能把肺部问题都看成感染？','Why infection is not the only question','CVID 患者的肺部问题可能来自反复感染造成的气道损伤，也可能涉及肺组织炎症。有些人在不同时间会面对不止一种问题。呼吸困难、咳嗽或影像异常本身不能把这些情况完全区分开。这篇研究聚焦 CVID 相关间质性肺病的诊断检查，而不是所有肺部并发症，也不是比较哪种药最好。','People with CVID can have airway damage associated with infection, inflammation involving lung tissue, or more than one process. Symptoms and abnormal imaging do not independently identify the cause. This review addresses investigations for CVID-related interstitial lung disease. It is not a review of every respiratory complication and does not compare which medicine works best.'],
 ['研究如何整理已有证据？','How the evidence was assembled','作者汇集 58 项研究，共描述 796 名患者。这里的数字是已发表研究中的患者总数，不是一项新开展的、统一安排所有检查的试验。纳入资料的研究设计和检查选择并不一致，这会限制直接比较。综述能展示临床研究实际使用了哪些方法，也能指出证据仍薄弱的地方。','The authors assembled 58 studies describing 796 patients. This is a collection of published evidence, not one new experiment in which every participant received the same tests. Differences in study design and investigation choices limit direct comparison. A review can show how methods have been used and identify gaps without establishing a universally best sequence.'],
 ['影像与肺功能，分别看结构和功能','Structure and function are different views','高分辨率 CT 提供肺部结构变化的信息，帮助发现异常分布；肺功能检查则从另一角度描述呼吸系统的工作情况。两者不是互相替代的“同一种答案”。结构改变与功能影响未必在同一个时间、以同样幅度出现。因此，单次结果需要结合既往情况和临床表现理解，而不是在网页上套用一个阈值自行判断。','Imaging describes structural patterns; lung-function measurements describe aspects of how the respiratory system works. They are not duplicate answers. Structural and functional changes do not necessarily appear at the same time or move in parallel. Their meaning depends on the person’s history and clinical context. This explanatory distinction is not a recommendation that every reader needs every test.'],
 ['灌洗和组织取样回答更具体的问题','Sampling asks more specific questions','综述中，支气管肺泡灌洗常用于帮助排查感染；肺活检能够提供组织层面的信息。但能取得更多组织信息，不等于每个人都需要活检。取样方式、能够回答的问题和操作负担不同，需要由临床团队权衡。不能把论文中“有多少项研究使用了活检”，误读为“有多少患者应该做活检”。','In the review, bronchoalveolar lavage was commonly used to help exclude infection, while biopsy provided tissue information. More tissue information does not imply that everyone needs a biopsy. Methods differ in what they can answer and in their burdens and risks. The proportion of publications reporting a procedure is not the proportion of patients who should undergo it.'],
 ['这些结果为什么还不能成为统一检查清单？','Why this is not a universal checklist','许多资料来自观察性研究、小系列或病例报告，不同团队使用的定义和检查组合也有差异。如果某种检查主要用于病情较复杂的人群，其结果就不能直接与另一种人群相比。综述揭示的是证据的组成与不足，而不是用一个排名替代多学科判断。它发表于 2023 年，阅读时还应注意后续证据可能更新。','Much of the evidence comes from observational work and small reports with differing definitions and investigation pathways. A test used mainly in complex cases cannot be fairly compared with another used in a different population without accounting for that difference. Published in 2023, this review provides context for understanding the evidence rather than a current personalised testing checklist.'],
 ['患者可以怎样理解这一组检查？','What a patient can take from this','最有帮助的认识是：医生可能在同时回答几个问题——有没有感染、结构哪里改变、功能受到多少影响，以及是否需要组织证据。你可以询问某项检查主要想澄清什么，它的结果会怎样影响下一步安排。具体是否进行检查，应由了解你情况的团队决定。把不同证据放在一起，比把任何一个结果当成全部答案更接近这篇研究的意义。','The useful takeaway is that a team may be asking several questions: whether infection is present, where tissue has changed, how function is affected and whether tissue evidence is needed. Asking what an investigation is intended to clarify can make the process easier to understand. Whether to perform it remains an individual clinical decision. The point is to combine complementary evidence rather than make one result carry the whole diagnosis.']
 ]});
}

Object.assign(exports, {addResearchDepth});
},
"education/src/research-parity.js": function(require, exports) {
// English explanations of the original Chinese sections, not one-line summaries.
function completeEnglishExplainers(items){
 const paragraphs=[
 [
 'Immunoglobulin replacement helps many people have fewer infections, yet some continue to experience gut, lung or autoimmune problems. Researchers therefore ask whether inflammation can be connected to the gap in antibody protection, rather than being an entirely separate issue. This paper examines that possible connection. It does not suggest that every continuing symptom has the same cause, or that infection prevention is unimportant.',
 'IgA is an important part of mucosal defence. Think of the gut as an interface that must absorb nutrients while managing constant microbial contact. The proposed explanation is that inadequate IgA and impaired containment may increase exposure to microbial material, sustaining immune stimulation. Bacterial DNA in a blood sample is not equivalent to an infection of the bloodstream by living bacteria. That distinction matters when interpreting the study.',
 'The team compared blood samples from people with CVID and healthy controls, examining IgA, switched-memory B cells, bacterial 16S DNA and signals including IFN-γ, CXCL9 and BAFF. These measurements concern different parts of the proposed mechanism: antibody memory, microbial exposure and immune activation. Not every participant contributed to every analysis. The total cohort size should therefore not be treated as the sample size for each individual result.',
 'Lower IgA and fewer switched-memory B cells were associated with measures of bacterial material or inflammatory activity. The authors propose a connection between reduced mucosal defence, microbial exposure and signals such as IFN-γ and BAFF. BAFF supports B-cell survival, but the balance of such signals also matters for immune regulation. This is a framework supported by the study, not a fixed sequence demonstrated in every person with CVID.',
 'The paper raises questions about whether improving mucosal defence could eventually help, but it did not test whether replacing IgA safely improves CVID outcomes. Associations do not establish the complete order of events or prove that one finding causes another. Its contribution is a more concrete hypothesis for further experiments and clinical investigation, rather than an intervention that a patient can now be expected to try.'
 ],
 [
 'The starting point was a pair of identical twins, one with CVID and the other without it. A closely shared inherited background helps researchers focus on another question: might the way cells use genetic information contribute to their different immune function? This is a valuable design for finding mechanisms. It is not a basis for assuming that one pair represents the biological diversity of everyone with CVID.',
 'DNA contains instructions, but a cell does not use every instruction at once. DNA methylation, the accessibility of chromatin and transcription help describe how information is regulated at a particular stage. Investigating these layers is different from identifying a disease-causing mutation. It also does not imply that a patient caused their illness through lifestyle or that changing a habit would reverse the regulatory differences.',
 'Blood contains a mixture of immune cells, so averaging them together can hide changes in a smaller population. The researchers combined single-cell measurements of DNA methylation, chromatin and RNA. They separated naïve and memory B-cell populations and examined responses after activation. This provided several views of maturation and communication rather than relying only on the overall number of B cells present.',
 'The findings were particularly prominent in memory B cells. Regulatory changes expected during maturation were altered, alongside differences in gene expression and communication after activation. Additional patient and control analyses supported selected findings. The work suggests that the problem can involve completing a developmental programme and cooperating with other cells, rather than simply having too few cells in the blood.',
 'The study gives biological substance to the idea that an unresolved single-gene diagnosis is not an absence of an underlying mechanism. However, cell states may also reflect prior illness, immune activation and treatment. The order of cause and consequence needs further investigation. This is a mechanistic research resource, not a validated test for choosing an individual treatment or predicting a person’s future.'
 ],
 [
 'People with the same CVID diagnosis can experience very different combinations of infection, autoimmunity, lung disease and gut disease. It is natural to wonder whether those differences reveal which molecule is affected. This study brought clinical and genetic information from 405 people at one centre together to investigate that relationship. The question is about patterns across people, not diagnosing a reader from a symptom list.',
 'The investigators examined clinical manifestations, including autoimmune and organ complications, in relation to genetic findings. Observational comparisons can identify features that occur together and suggest useful questions for further investigation. They do not randomly assign treatment, and this analysis cannot establish which treatment would work best for a person. The nature of the comparison determines what the result can answer.',
 'Genetic findings provided explanations or clues for part of the cohort, but manifestations overlapped across genetic backgrounds. Clinical patterns did not identify particular genes neatly. An organ complication may support a discussion of genetic assessment without pointing to one unique cause. Conversely, not having a textbook presentation does not automatically exclude a genetic explanation. Symptoms remain important, but are not a molecular code.',
 'A variant needs to be interpreted with its inheritance, family information, immune measurements and evidence of biological function. A risk-associated variant and a well-supported causal defect are not the same category. TACI findings are an important example of why this distinction matters: a result can influence susceptibility without being sufficient to explain the whole condition. A gene name alone is not the interpretation.',
 'A more specific genetic diagnosis can help explain a pathway while ongoing care follows the person’s actual manifestations. The study population also reflects referral and testing decisions at one centre. Its proportions should not be presented as the chance that every patient will find a gene. Clinical and genetic information are most useful when they inform one another rather than compete as alternative explanations.'
 ],
 [
 'Rare-disease experiences are spread across hospitals and countries. Even an experienced team may see too few people with a particular feature to describe how it changes over many years. A registry brings records together in a more consistent format, creating opportunities to investigate uncommon diagnoses and outcomes. It extends the view beyond one centre without making every participating person’s circumstances identical.',
 'The ESID report covers registry information from 1994 to 2024, describing manifestations, treatments and outcomes in 30,628 people from 194 centres. It includes many types of inborn errors of immunity. The full number must not be labelled a CVID population, and results across all diagnoses cannot simply be applied to one person with CVID. Both scale and the mixture of conditions matter.',
 'A single test describes one moment; repeated records can reveal what happens later. They can help describe diagnostic delay, the emergence of complications, treatment experience and longer-term outcomes. These observations give future studies a more realistic starting point and may help formulate more specific questions. They are also a way for experiences that are individually uncommon to become visible to researchers.',
 'Participating centres do not represent every hospital, and registered patients do not represent everyone living with an immune disorder. Missing records and differences in investigation, referral and documentation affect comparisons. Two events occurring together do not establish causality. Comparing treatments is especially complicated when people with more severe illness are more likely to receive a particular intervention in the first place.',
 'Research is not limited to trying a new medicine. Registries, natural-history projects and sample studies can all contribute to understanding disease. Before deciding, read what information is requested, how much time is involved and how records will be used. Sharing an experience can be valuable, but whether to share it—and under which consent arrangements—remains a voluntary and informed choice.'
 ]
 ];
 paragraphs.forEach((texts,i)=>texts.forEach((text,j)=>items[i].sections[j][3]=text));
}

Object.assign(exports, {completeEnglishExplainers});
},
"education/src/content-en.js": function(require, exports) {
// English companion articles. Chinese manuscripts remain unchanged.
const { chineseArticles } = require("education/src/content-zh.js");
const records = {
 'infection': ['Let’s begin with an infection', 'Follow the journey from an invading microbe to antibodies and lasting immune memory.', [
 ['A microbe reaches the entrance', 'Skin, mucus and the lining of the airways and gut provide the first barriers. If a microbe crosses them, innate immune cells respond. Neutrophils and macrophages can engulf microbes; dendritic cells carry information to lymph nodes. This early response buys time, but it cannot replace the more specific protection that develops next.'],
 ['A B cell recognises its target', 'Each B cell carries a receptor that recognises a particular molecular shape. Binding a target is an important first step, but effective activation also depends on other signals. Helper T cells can recognise material presented by the B cell and provide instructions that support its growth and differentiation. Antibody production is therefore a coordinated response, not a task performed by one cell alone.'],
 ['An early response and a longer training programme', 'Some activated B cells quickly produce antibodies, often including IgM. Others enter germinal centres in lymphoid tissue. Here, B cells multiply, refine how well their antibodies bind and undergo selection with help from follicular helper T cells. They may switch antibody class, for example to IgG or IgA. Changing class changes how the antibody works without simply changing its target.'],
 ['What remains after the infection?', 'Plasma cells are specialised antibody producers. Some can keep making antibodies for a long time. Memory B cells retain the capacity to respond again when a related target appears. The amount of antibody in the blood, the quality of a response and the number of memory cells describe related but different parts of protection.'],
 ['Where CVID can interrupt the journey', 'Many people with CVID have circulating B cells, yet make insufficient protective antibodies. Difficulties can involve activation, cooperation with other cells, maturation or the formation of effective memory. The same broad diagnosis does not mean the same molecular step is affected in everyone. This is why specialists combine infection history with several laboratory measurements.'],
 ['Neither a personal failing nor one single error', 'CVID is not caused by failing to try hard enough to stay healthy. Understanding the immune pathway helps explain why low antibodies can have more than one biological cause, and why a normal B-cell count does not necessarily mean normal antibody protection.']]],
 'multi-organ': ['Why can CVID affect more than one organ?', 'Infection defence and control of inflammation can be affected at the same time.', [
 ['The immune system also needs to stand down', 'Immunity must recognise threats, avoid attacking the body and settle after a response. These functions depend on overlapping networks of cells and signals. In CVID, reduced antibody protection may coexist with immune dysregulation. A weaker response to some microbes does not mean every immune response is weak.'],
 ['Lungs: infection is not the whole story', 'Repeated respiratory infections can damage airways, sometimes leading to bronchiectasis. A separate group of inflammatory changes can involve lung tissue, including granulomatous–lymphocytic interstitial lung disease, or GLILD. Infection and inflammation can have overlapping symptoms. A scan finding alone does not establish which process is responsible.'],
 ['Gut: a busy boundary', 'The intestine must absorb nutrients while managing constant contact with microbes. Infection, inflammation and impaired absorption can each contribute to symptoms in CVID. Persistent diarrhoea should not automatically be assigned one explanation. Research is exploring how mucosal antibodies, microbes and immune cells influence one another.'],
 ['Blood cells, spleen and lymph nodes', 'Immune responses can sometimes target platelets or red blood cells, causing immune cytopenias. The spleen and lymph nodes may enlarge when immune cells accumulate or remain activated. Enlargement has several possible causes; it is neither automatically harmless nor automatically cancer. Its meaning depends on the wider clinical assessment.'],
 ['The liver can also be involved', 'Some people develop liver abnormalities associated with immune disease or other causes. These may not produce obvious symptoms at first. Organ assessment therefore depends on the individual history and findings rather than on assuming that every person will develop the same complications.'],
 ['Why replacement antibodies are only part of the answer', 'Immunoglobulin replacement supports antibody protection, particularly against infections, but does not repair every immune-regulatory pathway. Persistent organ problems do not necessarily mean replacement treatment has failed. Infection prevention and investigation of inflammation answer different needs.'],
 ['A different combination for each person', 'The list of possible manifestations is not a prediction of your future. Some people mainly experience infections; others have overlapping complications. Long-term care follows the person’s actual pattern and how it changes.']]],
 'genetics': ['Monogenic immune deficiencies and genetic clues', 'A more specific molecular diagnosis can explain some antibody deficiencies, but every variant needs interpretation.', [
 ['CVID is an umbrella description', 'CVID brings together clinical and laboratory findings, rather than naming one defective molecule. People can share low immunoglobulins and impaired antibody responses while having different underlying biology. Genetic investigation sometimes identifies a more specific condition within this broader clinical starting point.'],
 ['When the diagnosis gains a more specific name', 'A confirmed disease-causing change in a gene can identify the pathway involved. This may clarify why antibody deficiency occurs alongside immune dysregulation or other organ findings. These defined conditions should not all be described as interchangeable CVID subtypes: some have a broader pattern of immune dysfunction.'],
 ['Genes are not the only level of explanation', 'A negative genetic test does not make symptoms less real. Current tests cannot identify every possible cause. Several genetic influences, gene regulation and other biological factors may contribute. Research methods and variant interpretation also continue to change.'],
 ['What makes a genetic clue useful?', 'Early or unusual disease, a family history, marked immune dysregulation or additional features may prompt specialist consideration of genetic testing. No single feature proves a genetic cause. The choice of investigation depends on the whole clinical picture and what a result could help clarify.'],
 ['A report is more than its conclusion', 'Interpretation considers the exact variant, inheritance, its frequency in populations, the person’s features and evidence about protein function. A variant of uncertain significance is not a confirmed diagnosis. A susceptibility variant may influence risk without being sufficient to explain disease on its own.'],
 ['The same variant can lead to different experiences', 'Penetrance describes whether a condition appears in people carrying a variant; expressivity describes how it appears. Both can vary. A relative without symptoms does not automatically settle the meaning of a result, and a shared result does not predict an identical course.'],
 ['What a confirmed result may change', 'A molecular diagnosis can support more focused counselling, assessment of relatives or consideration of disease-specific studies. It does not automatically identify an available treatment. Clinical findings and follow-up remain essential alongside the genetic explanation.']]],
 'research-progress': ['Where CVID research stands', 'Researchers are connecting antibody production, immune regulation and long-term patient experience.', [
 ['Returning to the B cell', 'A B-cell count cannot describe everything that cell can do. Researchers examine activation, antibody class switching, memory formation and plasma-cell differentiation. They also study the signals provided by T cells and the environments in which these steps occur.'],
 ['Deficiency and overactivity can coexist', 'One major question is why impaired defence against infection can accompany autoimmunity and inflammation. Studies connect cell populations, cytokines and tissue findings, looking for mechanisms that explain these combinations rather than treating them as unrelated labels.'],
 ['Looking beyond recurrent pneumonia', 'Lung research distinguishes airway damage from inflammatory tissue disease and asks how changes can be recognised and followed. A useful marker must eventually tell clinicians something meaningful about outcomes, not merely differ between groups in a study.'],
 ['The gut and its microbial environment', 'Mucosal antibodies help manage contact with microbes. Studies of IgA, microbial material and inflammatory signals explore whether altered containment contributes to immune activation. Such associations are clues, not proof that a particular dietary change or supplement treats CVID.'],
 ['Genetics and single-cell methods', 'Genetic studies can provide a more specific diagnosis for some people. Single-cell methods investigate how different immune populations use genes and communicate. Many measured cells can reveal detail, but cannot substitute for studying enough independent patients.'],
 ['From a mechanism to better care', 'Finding an altered pathway creates a question for further testing. Establishing a treatment requires evidence about benefit, harm, dose and the people for whom it is appropriate. Results in a related monogenic disease cannot simply be transferred to all CVID.'],
 ['Registries reveal changes over time', 'Long-term records help describe complications, diagnostic delays and treatment experiences. They complement laboratory research and can help plan trials. Missing information and differences between centres still matter when interpreting comparisons.'],
 ['What is established, and what remains open?', 'CVID is biologically and clinically varied. Antibody protection, immune regulation and organ health are connected. The remaining challenge is to make those connections useful for individual care without claiming more certainty than the evidence provides.']]],
 'lab-results': ['What is my immunoglobulin report telling me?', 'Antibody amounts, specific responses and B-cell measurements answer different questions.', [
 ['IgG: protection in blood and tissues', 'IgG is a major antibody class in circulation. A result describes its concentration at a particular time; it does not measure every aspect of immune protection. Age, laboratory reference ranges, treatment and the broader clinical history matter. Results during replacement therapy also reflect the antibodies that have been given.'],
 ['IgA and IgM: different roles', 'IgA is important at mucosal surfaces such as the gut and airways. A blood measurement does not directly describe every mucosal compartment. IgM often contributes early in an antibody response. These classes are not interchangeable, and one normal value does not cancel out all other findings.'],
 ['Specific antibody titres', 'A titre asks about antibodies against a particular target, rather than the total amount of an antibody class. Specialists may use response testing to investigate function in an appropriate clinical setting. Timing and prior immunoglobulin replacement can complicate interpretation, so numbers should not be judged in isolation.'],
 ['IgG subclasses and B-cell populations', 'IgG subclasses provide another layer of information, but a subclass value alone does not establish CVID. B-cell testing distinguishes populations at different stages, including switched-memory cells. Having B cells and being able to develop an effective antibody response are not the same thing.'],
 ['What the report cannot tell you alone', 'A single result does not forecast your entire disease course or determine a treatment plan. Trends, infections, organ findings and alternative causes of low antibodies all contribute to assessment. The useful question is what the test adds to your particular clinical picture.']]],
 'immunoglobulin-replacement': ['What does immunoglobulin replacement actually replace?', 'It supplies protective antibodies; it is not a general-purpose immune boost.', [
 ['Whose antibodies are these?', 'Replacement products contain immunoglobulin, mainly IgG, prepared from donated plasma and processed under controlled manufacturing conditions. They provide a range of antibodies rather than teaching your own B cells to make an entirely new immune response.'],
 ['What it can do', 'For people who need it, replacement supports protection against infections when their own antibody production is inadequate. Its effect is judged through clinical experience as well as laboratory results. Infection frequency, severity and day-to-day treatment burden all matter.'],
 ['What it cannot do', 'Replacement does not correct every cause of immune dysregulation or reliably resolve every inflammatory complication. It is also not the same as restoring normal IgA protection at every mucosal surface. Other symptoms may need their own assessment even when IgG replacement is helping.'],
 ['Intravenous and subcutaneous delivery', 'Intravenous treatment delivers immunoglobulin into a vein; subcutaneous treatment delivers it under the skin for gradual absorption. The approaches differ in schedule, practical demands and patterns of blood levels. Suitability and training depend on clinical circumstances and local services.'],
 ['Changes between doses', 'Some people notice symptoms towards the end of a treatment interval. These experiences are worth discussing, but do not by themselves prove a particular cause or justify changing a dose. Clinicians consider the pattern alongside infections, results and treatment tolerability.'],
 ['Safety is part of individual care', 'Products, routes and patient circumstances differ. The treating team should explain possible reactions and what to do if they occur. This article explains the principle of replacement; it is not an instruction to start, stop or adjust treatment.']]],
 'family': ['What should family members know?', 'Understanding, practical help and respect for independence can make a difference.', [
 ['CVID is not contagious', 'You cannot catch CVID from a family member. The diagnosis describes an immune problem, not an infection that spreads between people. Everyday support starts by separating the condition from the infections a person may experience.'],
 ['There is no single answer about inheritance', 'Some families have a defined genetic cause; many do not. Whether relatives need assessment depends on the diagnosis, family history and specialist advice. Having CVID does not automatically mean every child or sibling will have the same condition.'],
 ['Practical help can be specific', 'Support may involve listening, helping with appointments when invited, or making room for fatigue and treatment schedules. Ask what would help rather than assuming. Someone who looks well may still be managing a substantial burden, while someone with a diagnosis still needs ordinary independence and interests.'],
 ['Explaining it to children and teenagers', 'Use language appropriate to their age: parts of the immune system need extra support, and the care team helps provide it. The explanation should allow questions without making the child feel responsible for being ill. Involve young people in decisions in ways they can understand.'],
 ['Families also have feelings', 'Uncertainty can bring frustration, worry or exhaustion. Those feelings do not mean the family is failing. Honest conversation and appropriate support can help everyone adapt without allowing the diagnosis to define every part of family life.']]],
 'research-participation': ['What does joining a patient registry or research study involve?', 'Patient experiences can help research answer questions that one hospital cannot answer alone.', [
 ['One person’s experience can help many others', 'Repeated infections, lung investigations, gut symptoms, genetic findings and treatment experiences all contain questions that medicine has not fully answered. Bringing these experiences together has helped show that CVID is not only an antibody deficiency, and that its course differs between people.\nParticipation is more than contributing a number. It can help research address daily life as well as laboratory measurements. Some people mainly experience infection; others find fatigue, inflammation or the burden of treatment more difficult.'],
 ['Patient registries: a longer view of disease', 'A registry usually records diagnosis, treatment, investigations and follow-up in a structured way. It is not, by itself, a trial of a new medicine and generally does not assign a change in treatment. By combining records, researchers can investigate which problems occur together and how illness changes over time.\nSystems such as ESID and USIDNET bring together experiences across centres. What is collected, how often it is updated and who can access it depend on the particular registry. A website interest form is not the same as joining one of these formal registries.'],
 ['Scientific studies: asking why', 'Research may involve genetics, immune cells, biological samples or quality of life. A study might ask for blood, saliva or another sample, or ask about fatigue, school, work or infusion experiences. These approaches can explore mechanisms that are not visible in routine tests.\nThere may be no direct personal benefit. A sample may contribute to a molecular discovery, while a questionnaire may help researchers measure whether a treatment improves everyday life. The study information should explain exactly what participation involves.'],
 ['Clinical trials: testing an approach properly', 'Clinical trials test an intervention under a defined protocol. They ask about safety and benefit, rather than assuming that a promising mechanism will work in patients. Participants may be allocated to different groups, and some studies use a comparison treatment or placebo. The arrangements vary by study.\nA trial may examine a medicine, a dosing strategy or another intervention. Participation does not guarantee improvement. Ethics review, safety monitoring and a clear explanation of uncertainty are essential parts of responsible research.'],
 ['Participation is a partnership', 'Wanting future patients to receive answers sooner is one reason to participate, but it is not an obligation. It is also reasonable to want clearer information and to know whether research findings will be shared with you. Additional contact with a research team should not be confused with a guarantee of better care.\nPeople living with a rare disease, families, clinicians and scientists bring different knowledge to the same questions. Participation works best when those contributions are respected.'],
 ['Informed consent means an informed choice', 'Before enrolment, ask what information or samples are needed, what visits are involved, what risks and potential benefits exist, and how data will be stored and used. Ask about withdrawal and what can happen to data already analysed. These details belong in the study’s consent process, not in a general website promise.\nYou can ask questions and reconsider participation. Declining research should not affect your ordinary care. Expressing interest here is not consent to a study, does not share your records with a centre and does not determine eligibility.'],
 ['Patients should also help set the questions', 'Fatigue, recovery after infection, treatment schedules and the ability to study, work or travel can matter as much as a laboratory result. Patient involvement can help decide which outcomes studies measure and which questions deserve priority.\nYou can begin by learning about a project and its practical demands. Only the official research team can confirm whether it is open to you. Whether to contact them and whether to take part remain your decisions.']]],
};
const genes = [
 ['cd19','CD19: helping B cells hear the activation signal','A co-receptor that strengthens B-cell signalling.',[
 ['A signal amplifier, not the antigen receptor itself','The B-cell receptor recognises a target. CD19 helps strengthen the signal that follows, acting with partners including CD21 and CD81. This coordination helps a B cell respond appropriately rather than simply responding to every contact.'],
 ['From recognition to memory','Activation is an early step on a longer path to antibody production and memory. If signals are inadequate, having B cells in the blood does not guarantee that they will develop effective specific antibody responses.'],
 ['When CD19 function is impaired','Rare inherited CD19 deficiency can cause antibody deficiency despite the presence of B cells. Clinical interpretation combines antibody measurements, responses and genetic evidence. A low CD19 measurement alone is not equivalent to a confirmed inherited disorder.'],
 ['What this teaches us about CVID','CD19 provides a specific example of how a signalling problem can underlie an antibody-deficiency presentation. It does not explain all CVID. Research into this co-receptor system helps distinguish cell numbers from the quality of a response.'],
 ['Interpreting a genetic finding','The exact variant, inheritance and supporting functional evidence matter. A gene name on a report does not establish a diagnosis or indicate that a treatment targeting the same molecule would be appropriate.']]],
 ['cd81','CD81: organising the B-cell signalling platform','A membrane organiser that supports the CD19 co-receptor complex.',[
 ['Building a stable platform','CD81 belongs to the tetraspanin family of membrane proteins. Rather than recognising an antigen itself, it helps organise proteins at the cell surface and supports the normal presentation and function of CD19.'],
 ['Why a partner matters','A receptor system depends on its components being in the right place. A problem with CD81 can therefore disrupt a response even when the gene encoding CD19 itself is not the underlying cause. This illustrates why immune signalling is studied as a network.'],
 ['When CD81 is deficient','Rare inherited deficiency has been associated with impaired antibody responses. Similarities to CD19 deficiency arise from their functional partnership, but the molecular diagnoses are distinct. Patient numbers are small, so the full range of outcomes is not precisely known.'],
 ['Genetic clues and current knowledge','Clinical findings, surface-protein measurements and genetic evidence can be considered together. Research links membrane organisation with antibody responses; it does not establish that every CD81 variant causes disease or that every person with CVID has this defect.']]],
 ['cr2-cd21','CR2/CD21: recognising a target tagged by complement','CD21 connects complement recognition with B-cell activation.',[
 ['A tag that helps a target stand out','Complement proteins can attach fragments to a target. CD21 can recognise certain complement fragments, helping link the target with the B-cell co-receptor system. The tag analogy describes an immune signal, not conscious recognition by a cell.'],
 ['Working with CD19 and CD81','CD21 participates in a complex that helps strengthen B-cell signalling. Antigen recognition and complement recognition can cooperate. CD21 also has roles in antigen handling within lymphoid tissue, illustrating that the same molecule can contribute in more than one location.'],
 ['Deficiency is not the same as a low-expression population','Rare CR2 defects can impair antibody responses. However, CD21-low B cells reported on an immune phenotype are a cell population with reduced surface expression; their presence does not by itself diagnose inherited CD21 deficiency. This distinction prevents two very different findings being confused.'],
 ['What researchers can learn','Studying rare defects helps explain how complement supports adaptive immunity. Interpreting an individual result still needs the exact genetic finding and clinical evidence. Small numbers of documented cases limit confident predictions about the course of disease.']]],
 ['ms4a1-cd20','MS4A1/CD20: supporting the signals that activate a B cell','CD20 is involved in B-cell function, including calcium signalling.',[
 ['Signals also travel inside the cell','Recognition at the surface is followed by internal changes. Calcium acts as an intracellular messenger, contributing to activation. CD20 is a membrane protein involved in B-cell signalling; a simplified calcium analogy does not describe every detail of its function.'],
 ['What inherited deficiency shows','Rare MS4A1 defects have helped researchers understand how antibody responses can be impaired even when B cells are present. These unusual observations are informative about biology but cannot define the experience of all patients with antibody deficiency.'],
 ['An inherited defect and a medicine are different stories','Anti-CD20 medicines target cells expressing CD20 for particular clinical purposes. Receiving such a medicine is not the same as being born with an MS4A1 defect. The indications, timing and immune effects must be considered separately. A shared molecule name does not make the situations interchangeable.'],
 ['What remains uncertain','The complete relationship between CD20, signalling and individual clinical outcomes is still being studied. Genetic interpretation requires evidence about the particular variant. Rare cases provide clues, not reliable estimates of an individual person’s future.']]],
 ['tnfrsf13b-taci','TNFRSF13B/TACI: helping B cells mature and stay regulated','TACI connects BAFF and APRIL signals with antibody responses.',[
 ['Survival is not the only task','TACI is a receptor on B cells that responds to BAFF and APRIL. Its roles include supporting aspects of antibody differentiation and class switching. A B cell needs signals that coordinate maturation, not simply an instruction to multiply.'],
 ['Growth and restraint must be balanced','TACI biology also involves regulation of the B-cell compartment. This helps explain why an antibody-deficiency presentation can overlap with immune dysregulation. The pathway cannot be reduced to a single on/off button.'],
 ['A variant is not always the answer','Some TACI variants are found in people without disease and may act as susceptibility factors rather than a sufficient explanation by themselves. Finding a variant should therefore not automatically end the search for other causes. Its effect and inheritance need careful interpretation.'],
 ['What research contributes','Studies of signalling and patient genetics connect TACI with antibody responses and variable disease expression. They also show why risk associations and proven disease-causing defects must be separated. A laboratory pathway is not, by itself, a reason to select a treatment.']]],
 ['tnfrsf13c-baffr','TNFRSF13C/BAFF-R: helping young B cells survive','BAFF-R supports an important stage in the maturation of B cells.',[
 ['A selective survival signal','New B cells do not all remain in the circulation. BAFF binding to BAFF-R helps support the survival and maturation of peripheral B cells. This is part of a controlled system, not a goal of keeping every B cell alive indefinitely.'],
 ['Where the receptor fits','BAFF-R and TACI share a connection to BAFF but do not have identical roles. The receptor receiving a signal and the developmental stage of the cell influence what happens next. This is why similarly named pathways cannot simply be treated as the same mechanism.'],
 ['When function is reduced','Rare inherited BAFF-R deficiency can affect B-cell populations and antibody production. The presentation may resemble a broader antibody-deficiency diagnosis before the specific cause is established. Variation between reported patients makes individual prediction difficult.'],
 ['From a report to an explanation','A result needs to be assessed with the variant, inheritance and immune findings. Research has established the importance of BAFF-R in B-cell biology, while the limited number of affected people leaves questions about the full clinical spectrum.']]],
 ['icos','ICOS: helping T cells support B-cell training','ICOS contributes to the helper-cell partnership needed for effective antibody memory.',[
 ['Why B cells need a partner','In germinal centres, B cells receive support from follicular helper T cells. This partnership helps coordinate selection, antibody class switching and differentiation. Recognition of an antigen is only part of the process.'],
 ['A co-stimulatory signal','ICOS is expressed on activated T cells and interacts with its ligand on other cells. It supports the helper-cell response. It is not an antibody and does not itself recognise the pathogen in the way a B-cell receptor does.'],
 ['When the partnership is disrupted','Inherited ICOS deficiency can impair antibody production and memory responses. A defect on the T-cell side can therefore appear clinically as an antibody problem. That is an important reason to consider cooperation between cell types rather than only counting B cells.'],
 ['What a molecular diagnosis adds','A confirmed diagnosis can clarify the pathway and support specialist counselling. Variants still need evidence, and rare disorders can vary between individuals. Mechanistic knowledge does not automatically specify a universally suitable treatment.']]],
 ['il21-il21r','IL21/IL21R: a message that supports B-cell differentiation','A cytokine and its receptor link helper-cell signals with antibody production.',[
 ['The message and the receiver','IL-21 is a signalling protein produced by certain T cells, including follicular helper T cells. IL-21R is part of the receptor system that receives the message. A defect in the signal and a defect in its receiver are related but distinct molecular problems.'],
 ['Why the message matters','Together with other signals, IL-21 supports B-cell differentiation and antibody responses. Its effects depend on the surrounding signals and the type of cell. The graduation-message analogy is useful, but it is not the only instruction a B cell needs.'],
 ['More than an antibody measurement','Defects in this pathway can cause broader immune problems as well as impaired antibody production. IL-21 and IL-21R deficiencies should not be assumed to have identical clinical patterns. Their interpretation requires specialist assessment beyond a single immunoglobulin value.'],
 ['What studies establish and leave open','Rare patients and functional experiments help connect the pathway with human immune defence. Limited numbers leave uncertainty about the full spectrum. Genetic and functional evidence are needed before attributing a person’s disease to a variant.']]],
 ['nfkb1','NFKB1: turning immune signals into cellular action','NFKB1 contributes to a transcription-factor system used by several immune cells.',[
 ['From the surface to the instructions','NF-κB proteins help regulate gene activity after a cell receives signals. NFKB1 encodes a precursor called p105 and the p50 component. This is an internal regulatory system, not a single surface receptor.'],
 ['Why B cells depend on it','B-cell activation and differentiation depend on coordinated gene programmes. Impaired NFKB1 function can disturb antibody responses, helping explain why an internal signalling defect can first appear as recurrent infection and low immunoglobulins.'],
 ['Why inflammation can also occur','The pathway contributes to regulation in several immune-cell types. Its disruption can be associated with immune dysregulation as well as infection susceptibility. The balance of manifestations differs, and not everyone develops the same complications.'],
 ['One copy can matter, but expression varies','Some disease-causing NFKB1 defects act through reduced gene dosage. A person carrying such a variant may develop disease later or have a different presentation from a relative. Neither a shared variant nor a symptom-free relative gives a complete prediction.'],
 ['What research is clarifying','Patient cohorts and functional studies investigate how variants alter protein function and why disease expression varies. A confirmed defect can refine the diagnosis, but a variant of uncertain significance is not equivalent to that confirmation.']]],
 ['stat3-gof','STAT3 gain of function: when a regulatory signal becomes excessive','Excess activity in an immune pathway can coexist with impaired protection.',[
 ['A gene can work too strongly','STAT3 helps transmit signals to gene-regulatory programmes. Gain of function means a variant increases or alters activity in a disease-relevant way. It is different from STAT3 loss of function; naming the gene alone is not enough to describe the condition.'],
 ['Why overactivity can cause immune deficiency','An effective immune system depends on balanced development and regulation, not maximum activity. Excessive signalling can disturb that balance, producing autoimmunity or inflammation alongside impaired defence. More signal does not necessarily mean better protection.'],
 ['A varied clinical picture','STAT3 gain-of-function disease can involve multiple organs, growth and immune regulation. Some people have antibody deficiency, but it is a more specific disorder and should not be presented as a cause of every CVID diagnosis.'],
 ['Evidence before interpretation','The exact variant and evidence for its functional effect are essential. Research on pathway-directed approaches belongs to the defined disorder and its clinical context; it cannot automatically be applied to all people with low antibodies.']]],
 ['stat1-gof','STAT1 gain of function: when persistent signalling disrupts immune balance','The strength of one response does not describe the whole immune system.',[
 ['An important signalling pathway','STAT1 participates in responses to interferons. Gain-of-function variants can alter the strength or persistence of signalling. A continuously amplified signal can disturb other immune functions rather than providing universal protection.'],
 ['Why Candida is an important clue','Persistent or recurrent mucocutaneous Candida infection is a characteristic feature of many reported cases. It is not enough on its own to diagnose STAT1 gain-of-function disease: many other conditions can cause fungal infection.'],
 ['A wider immune pattern','Other infections, autoimmunity and variable antibody abnormalities can occur. The condition is therefore not simply a form of low IgG. Clinical assessment brings together the pattern over time rather than assigning a diagnosis from one symptom.'],
 ['What molecular studies add','Functional investigation can distinguish a disease-causing increase in activity from an uninterpreted variant. Studies of targeted treatment examine a specific pathway and patient group; a result cannot be generalised to all CVID or used to choose medicine without specialist care.']]],
 ['pik3r1','PIK3R1: regulating the immune cell’s accelerator','A regulatory component helps keep PI3K signalling appropriately controlled.',[
 ['Signalling needs a regulator','PIK3R1 encodes regulatory components of the PI3K system. This pathway helps cells respond to growth and activation signals. The accelerator analogy explains the need for balance, but different variants can have different biological effects.'],
 ['Why excessive signalling can impair immunity','Certain variants cause activated PI3K-delta syndrome type 2, or APDS2. Overactive signalling can disrupt lymphocyte maturation and function. It can therefore produce infection susceptibility despite excessive activity in one part of the system.'],
 ['More than one clinical label','Antibody deficiency may occur alongside lymphoid enlargement and other immune problems. A confirmed APDS2 diagnosis is more specific than a general antibody-deficiency label. Not every PIK3R1 variant causes APDS2, and the gene is also associated with other phenotypes.'],
 ['Research follows the defined mechanism','Pathway-directed research illustrates why a precise molecular diagnosis may matter. Whether a particular approach is appropriate depends on the established diagnosis and clinical assessment, not merely on a gene name appearing in a report.']]]
];
for (const [slug,title,excerpt,sections] of genes) records[slug]=[title,excerpt,sections];
const englishArticles=chineseArticles.map(original=>{
 const [title,excerpt,sections]=records[original.slug];
 const sourceText=x=>x.replace('IEI 实践参数。','practice parameter for IEI.').replace(/ICON：CVID 国际共识[.。]/,'International Consensus Document (ICON): Common Variable Immunodeficiency Disorders.').replace('IEI 临床诊断工作定义。','working definitions for clinical diagnosis of IEI.');
 return {...original,title,excerpt,blocks:[{type:'paragraph',text:excerpt},...sections.flatMap(([heading,text])=>[{type:'heading',text:heading},{type:'paragraph',text}])],sources:original.sources.filter(x=>!/^\d{1,2}:\d{2}$/.test(x.trim())).map(sourceText)};
});

Object.assign(exports, {englishArticles});
},
"education/src/content-zh.js": function(require, exports) {
// Generated from the user-provided Chinese manuscript.
const chineseArticles = [
  {
    "slug": "infection",
    "category": "basics",
    "title": "先从一次感染说起",
    "excerpt": "一次普通的呼吸道感染，并不是“病毒进来—身体把它赶走”这么简单。它更像一场分层协作：先由门口的屏障和巡逻队争取时间，再由免疫系统辨认入侵者、制造有针对性的抗体，最后把经验保存下来。CVID 的核心问题，常常就出现在这条“制造并保存有效抗体”的链路上；但不同人的异常位置和程度并不一样。",
    "blocks": [
      {
        "type": "paragraph",
        "text": "一次普通的呼吸道感染，并不是“病毒进来—身体把它赶走”这么简单。它更像一场分层协作：先由门口的屏障和巡逻队争取时间，再由免疫系统辨认入侵者、制造有针对性的抗体，最后把经验保存下来。CVID 的核心问题，常常就出现在这条“制造并保存有效抗体”的链路上；但不同人的异常位置和程度并不一样。"
      },
      {
        "type": "heading",
        "text": "病原体先来到门口"
      },
      {
        "type": "paragraph",
        "text": "想象一个冬天的早晨。有人在拥挤的地铁上吸入带有病毒的飞沫。病毒最先落在鼻腔、咽喉或气道表面。"
      },
      {
        "type": "paragraph",
        "text": "这里并不是毫无防备的入口。黏液会黏住一些病原体，纤毛会把它们一点点往外推；上皮细胞之间紧密相连，像一道排列整齐的墙。分泌在黏膜表面的 IgA 抗体，也会尽量阻止病原体黏附和进入细胞。"
      },
      {
        "type": "paragraph",
        "text": "如果病原体突破了这层防线，中性粒细胞和巨噬细胞会先赶到。它们不需要知道这到底是哪一种病毒或细菌，只要发现可疑目标，就会吞噬、包围并发出求援信号。"
      },
      {
        "type": "paragraph",
        "text": "但这些早到的“巡逻队”只能争取时间。身体若想下一次更快、更准确地应对同一位入侵者，就需要把它真正记住。"
      },
      {
        "type": "heading",
        "text": "B 细胞接到任务"
      },
      {
        "type": "paragraph",
        "text": "在附近的淋巴结里，B 细胞正在等待。"
      },
      {
        "type": "paragraph",
        "text": "每个 B 细胞表面都带着独特的“识别器”。有的擅长识别一种细菌表面结构，有的擅长识别病毒的一小段蛋白。多数 B 细胞与这次感染无关，只有少数恰好能抓住这个病原体的 B 细胞，会被真正唤醒。"
      },
      {
        "type": "paragraph",
        "text": "树突细胞和 CD4 T 细胞在这里帮助完成确认：它们把感染现场带来的信息告诉免疫系统，并为合适的 B 细胞提供继续工作的信号。对于 B 细胞来说，这像是得到了一句重要许可：“这个目标是真的，值得投入资源。”"
      },
      {
        "type": "paragraph",
        "text": "于是，B 细胞开始分成两队。"
      },
      {
        "type": "heading",
        "text": "第一队：先制造一张大网"
      },
      {
        "type": "paragraph",
        "text": "有些 B 细胞很快变成浆细胞，开始制造 IgM。"
      },
      {
        "type": "paragraph",
        "text": "IgM 是感染早期常见的抗体。它不像一把精密的钥匙，更像一张有很多抓手的大网：能把病原体聚在一起，也能让吞噬细胞更容易发现目标。它帮助身体先把感染围住。"
      },
      {
        "type": "paragraph",
        "text": "可是，一张大网还不够。面对下一次同样的感染，身体需要更贴合病原体、更持久的保护。"
      },
      {
        "type": "heading",
        "text": "第二队：进入抗体训练营"
      },
      {
        "type": "paragraph",
        "text": "另一部分 B 细胞会进入淋巴结中的生发中心。"
      },
      {
        "type": "paragraph",
        "text": "生发中心像一个短暂开设的训练营。B 细胞在这里反复练习：谁制造的抗体更能牢牢抓住病原体，谁就更可能留下；抓不准、拿不到协作信号，或可能带来风险的 B 细胞，大多会离开训练营。"
      },
      {
        "type": "paragraph",
        "text": "经过筛选，抗体会变得更“认得准”病原体。这一过程称为亲和力成熟。B 细胞还会学习更换抗体类别，从较早出现的 IgM，转向更适合不同场景的 IgG 或 IgA。"
      },
      {
        "type": "paragraph",
        "text": "IgG主要在血液和组织液中巡逻。它可以中和病毒或毒素，也能给病原体贴上标签，让吞噬细胞更容易清除它。"
      },
      {
        "type": "paragraph",
        "text": "IgA主要守在呼吸道和肠道等黏膜表面，尽量把病原体拦在人体组织之外。"
      },
      {
        "type": "paragraph",
        "text": "IgM则在感染刚开始时，帮助迅速围堵。"
      },
      {
        "type": "paragraph",
        "text": "这不是三种互相竞争的抗体，而是一支分工不同的队伍。"
      },
      {
        "type": "heading",
        "text": "感染过去后，身体会留下什么"
      },
      {
        "type": "paragraph",
        "text": "一场感染结束后，身体不会把所有参与的 B 细胞都撤走。"
      },
      {
        "type": "paragraph",
        "text": "一部分成为记忆 B 细胞。它们安静地保留对这位入侵者的识别经验。下次再遇到类似病原体，它们可以更快醒来。"
      },
      {
        "type": "paragraph",
        "text": "另一部分成为长寿命浆细胞。它们像长期运行的小型工厂，在骨髓等地方持续制造抗体。"
      },
      {
        "type": "paragraph",
        "text": "这就是为什么许多人第二次遇到同一种病原体时，身体通常能更快、更有效地作出反应。免疫系统不是只打赢一场仗；它还在为下一场仗存档。"
      },
      {
        "type": "heading",
        "text": "CVID：问题可能发生在这条路的不同位置"
      },
      {
        "type": "paragraph",
        "text": "对许多 CVID 患者来说，困难并不在于身体完全没有 B 细胞。更常见的是，B 细胞走不到这段故事的最后。"
      },
      {
        "type": "paragraph",
        "text": "有些 B 细胞难以顺利进入或完成生发中心反应；有些难以转变成记忆 B 细胞；有些难以成为能长期制造抗体的浆细胞。结果是，身体可能做不出足量的 IgG、IgA，或抗体虽然出现，却不够持久、不够有效。"
      },
      {
        "type": "paragraph",
        "text": "于是，每一次感染都像一次没有好好存档的经历。身体能暂时应对，却没有留下足够可靠的记忆和防护。"
      },
      {
        "type": "paragraph",
        "text": "这也解释了为什么 CVID 常以反复鼻窦炎、支气管炎或肺炎被发现：呼吸道每天都在接触外界，而本应守在血液、组织和黏膜中的抗体保护，并没有完全到位。"
      },
      {
        "type": "heading",
        "text": "这不是一个人的错，也不是同一种错误"
      },
      {
        "type": "paragraph",
        "text": "CVID 不代表患者“不够注意卫生”，也不代表每次感染都能靠意志避免。它反映的是免疫系统里一条复杂的抗体生成和记忆链路出了问题。"
      },
      {
        "type": "paragraph",
        "text": "研究已经发现，一部分患者的异常与 B 细胞表面的分子、细胞内部信号或免疫调节机制有关；也有不少患者还没有找到一个明确的单一原因。共同点是抗体保护不足，但每个人走到这个结果的路径可以不同。"
      },
      {
        "type": "paragraph",
        "text": "这也是 CVID 被称为“普通变异型”免疫缺陷的原因之一：它有共同的核心，却没有每个人都完全相同的故事。"
      }
    ],
    "sources": [
      "Bonilla FA, et al. International Consensus Document (ICON): Common Variable Immunodeficiency Disorders. Journal of Allergy and Clinical Immunology. 2016.",
      "ESID. Registry Working Definitions for Clinical Diagnosis of Inborn Errors of Immunity.",
      "Tangye SG, et al. Human inborn errors of immunity: 2024 update from the IUIS Expert Committee. Journal of Human Immunity. 2025.",
      "Cossarizza A, et al. B Cell Activation and Response Regulation During Viral Infections. Frontiers in Immunology. 2020."
    ]
  },
  {
    "slug": "multi-organ",
    "category": "complications",
    "title": "为什么 CVID 会影响多个器官？",
    "excerpt": "很多人最初认识 CVID，是从反复鼻窦炎、支气管炎或肺炎开始的。于是很自然会问：既然是抗体问题，为什么后来还会有肠道不适、血小板减少、脾大、淋巴结增大，甚至肺部或肝脏的问题？",
    "blocks": [
      {
        "type": "paragraph",
        "text": "很多人最初认识 CVID，是从反复鼻窦炎、支气管炎或肺炎开始的。于是很自然会问：既然是抗体问题，为什么后来还会有肠道不适、血小板减少、脾大、淋巴结增大，甚至肺部或肝脏的问题？"
      },
      {
        "type": "paragraph",
        "text": "答案并不是 CVID “从呼吸道蔓延到了全身”。而是免疫系统本来就在全身工作。当它既不够会防御感染、又不够会在适当时候停下来时，影响也可能出现在许多器官。"
      },
      {
        "type": "heading",
        "text": "免疫系统不只负责打仗，也负责收队"
      },
      {
        "type": "paragraph",
        "text": "我们常把免疫系统想成一支军队：发现病原体，发动攻击，把它清除。"
      },
      {
        "type": "paragraph",
        "text": "但一支只会进攻、不会收队的军队同样危险。健康的免疫系统还要做到两件事："
      },
      {
        "type": "paragraph",
        "text": "第一，分清真正的病原体和身体自己的组织。\n第二，在感染结束后及时降低反应，不让炎症一直持续。"
      },
      {
        "type": "paragraph",
        "text": "对一些 CVID 患者来说，抗体不足使感染防御变弱；同时，免疫细胞的调节也可能不够稳定。于是身体可能一边更难彻底清除感染，一边又出现不必要的炎症或自身免疫反应。"
      },
      {
        "type": "paragraph",
        "text": "这就是 CVID 为什么不只是“容易感冒”。"
      },
      {
        "type": "heading",
        "text": "肺：最先感受到反复感染的地方"
      },
      {
        "type": "paragraph",
        "text": "肺每天都要接触外界空气，所以特别容易暴露出抗体保护不足的问题。"
      },
      {
        "type": "paragraph",
        "text": "如果肺炎、支气管炎反复发生，支气管的管壁可能一次次发炎、修复，最后变得松弛、变宽。这样的变化叫作支气管扩张。扩张后的支气管更不容易把痰排干净，病原体也更容易停留，于是又增加新的感染机会。"
      },
      {
        "type": "paragraph",
        "text": "这像一条被反复踩坏的小路：路面越不平，之后越容易积水。"
      },
      {
        "type": "paragraph",
        "text": "但 CVID 的肺部问题并不总是感染留下的痕迹。有些患者的肺泡周围会有异常免疫细胞聚集，形成一种以炎症为主的肺部表现。GLILD 就属于这一类。它的名字很长，但可以简单理解为：免疫细胞在肺部停留得太久、太多，造成了并不完全由感染解释的炎症。"
      },
      {
        "type": "paragraph",
        "text": "所以，CVID 患者的肺部问题可能来自两条不同的路：一条是反复感染造成的损伤；另一条是免疫系统本身的持续炎症。有时两条路也会交织在一起。"
      },
      {
        "type": "heading",
        "text": "肠道：一条特别忙的边界线"
      },
      {
        "type": "paragraph",
        "text": "肠道不只是消化食物的地方，也是人体与外界接触面积很大的边界。"
      },
      {
        "type": "paragraph",
        "text": "每天，食物、细菌、病毒和大量正常共生微生物都会经过这里。免疫系统必须有分寸：不能把每一口食物、每一种正常肠道细菌都当作敌人；但真正的病原体出现时，又必须及时应对。"
      },
      {
        "type": "paragraph",
        "text": "CVID 中，肠道可能因为感染反复发生问题，也可能因为免疫调节不够稳定而长期发炎。患者可能经历慢性腹泻、腹痛、吸收不良或体重变化。有时检查结果会看起来像乳糜泻或炎症性肠病，但背后的免疫原因不一定相同。"
      },
      {
        "type": "paragraph",
        "text": "研究者也在关注肠道微生物组——也就是生活在肠道里的微生物群体。部分研究发现，CVID 患者的菌群组成可能与健康人不同。但目前还不能说“某一种细菌导致了 CVID 肠病”；菌群变化可能是原因，也可能是长期炎症、感染、饮食或抗生素使用后的结果。"
      },
      {
        "type": "heading",
        "text": "血液：为什么会出现血小板或红细胞减少"
      },
      {
        "type": "paragraph",
        "text": "有些人最早发现的异常，甚至不是感染，而是血小板减少、贫血或白细胞减少。"
      },
      {
        "type": "paragraph",
        "text": "这通常不是因为骨髓“停止制造血细胞”，而可能是免疫系统把自己的血细胞错当成了目标。正常情况下，B 细胞和 T 细胞在成长过程中会接受很多次筛选，避免产生攻击自身的反应。"
      },
      {
        "type": "paragraph",
        "text": "但如果这套筛选和刹车系统不够稳定，就可能出现自身免疫性血细胞减少。"
      },
      {
        "type": "paragraph",
        "text": "这件事乍听起来很矛盾：为什么一个抗体不足的人，反而会有“攻击自己”的免疫反应？其实并不矛盾。CVID 不是免疫系统完全无力，而是某些功能不足、某些反应又失去平衡。"
      },
      {
        "type": "heading",
        "text": "脾脏和淋巴结：免疫系统太忙时，办公室也会变大"
      },
      {
        "type": "paragraph",
        "text": "脾脏和淋巴结是免疫细胞平时开会、训练和增殖的地方。"
      },
      {
        "type": "paragraph",
        "text": "当身体反复遇到感染，或免疫细胞长期处于活跃状态时，淋巴结和脾脏可能增大。这并不自动表示癌症。它有时只是说明免疫系统在这些地方停留得太久、太忙。"
      },
      {
        "type": "paragraph",
        "text": "不过，CVID 患者确实比一般人更需要认真评估持续或进行性变化的淋巴结、脾脏和某些全身症状。原因不是要制造恐慌，而是因为长期免疫失调和淋巴细胞异常活化，可能带来较高的淋巴系统疾病风险。"
      },
      {
        "type": "paragraph",
        "text": "“需要评估”不等于“已经发生淋巴瘤”；两者之间不能画等号。"
      },
      {
        "type": "heading",
        "text": "肝脏：有时是被免疫失衡牵连"
      },
      {
        "type": "paragraph",
        "text": "肝脏每天接收大量来自肠道的血流，也参与处理炎症信号和免疫细胞。"
      },
      {
        "type": "paragraph",
        "text": "在部分 CVID 患者中，肝脏可能出现炎症、免疫细胞浸润或血流结构改变。有些人没有明显症状，是在常规血液检查或影像随访中发现线索。"
      },
      {
        "type": "paragraph",
        "text": "这提醒我们：CVID 的随访不应只盯着感染次数。因为有些问题不会立刻带来明显不适，但越早发现变化，越容易和专科团队一起判断它真正意味着什么。"
      },
      {
        "type": "heading",
        "text": "为什么免疫球蛋白能帮上一部分忙，却不是全部答案"
      },
      {
        "type": "paragraph",
        "text": "免疫球蛋白替代治疗补充的是现成的 IgG 抗体。它能帮助患者更好地应对一部分常见感染，特别是细菌性呼吸道感染。"
      },
      {
        "type": "paragraph",
        "text": "但它不能回到免疫系统内部，把异常的 B 细胞成熟过程重新走一遍；也不能自动让过度活跃的免疫细胞停止工作。"
      },
      {
        "type": "paragraph",
        "text": "所以，补充免疫球蛋白对于感染防护非常重要，但如果某位患者的主要问题是自身免疫、肠道炎症或 GLILD 一类的肺部炎症，仍可能需要围绕这些问题进行单独评估。这不是免疫球蛋白“没有用”，而是它解决的是抗体不足这一部分，而不是所有免疫失衡。"
      },
      {
        "type": "heading",
        "text": "每个人的组合都不同"
      },
      {
        "type": "paragraph",
        "text": "并不是每位 CVID 患者都会出现多器官问题。有人一生主要面对感染；有人在感染之外还会有自身免疫、炎症或淋巴组织增生。"
      },
      {
        "type": "paragraph",
        "text": "研究者已经知道，这种差异与 B 细胞成熟、免疫调节、遗传背景、感染经历和器官原有损伤有关。但对于多数患者，仍无法用一项化验准确预测未来会发生什么。"
      },
      {
        "type": "paragraph",
        "text": "理解这一点或许能减少一个常见误解：CVID 并不是一张固定的并发症清单。它更像一套免疫系统失衡可能留下的不同痕迹；每个人留下的痕迹都不一样。"
      }
    ],
    "sources": [
      "Bonilla FA, et al. International Consensus Document (ICON): Common Variable Immunodeficiency Disorders. Journal of Allergy and Clinical Immunology. 2016.",
      "Ho HE, Cunningham-Rundles C. Non-infectious complications of common variable immunodeficiency. Frontiers in Immunology. 2020.",
      "van Stigt AC, et al. Diagnostic testing for interstitial lung disease in common variable immunodeficiency: a systematic review. Frontiers in Immunology. 2023.",
      "Immune Deficiency Foundation. Common Variable Immune Deficiency."
    ]
  },
  {
    "slug": "genetics",
    "category": "genetics",
    "title": "更具体的单基因免疫缺陷与遗传线索",
    "excerpt": "有些人在被诊断为 CVID 后，会经历一个新的问题：“为什么偏偏是我？”\n还有一些家庭会发现，兄弟姐妹、父母、子女或亲属中，似乎也有人反复感染、免疫球蛋白偏低、自身免疫，或有说不清的肠道、肺部问题。",
    "blocks": [
      {
        "type": "paragraph",
        "text": "有些人在被诊断为 CVID 后，会经历一个新的问题：“为什么偏偏是我？”\n还有一些家庭会发现，兄弟姐妹、父母、子女或亲属中，似乎也有人反复感染、免疫球蛋白偏低、自身免疫，或有说不清的肠道、肺部问题。"
      },
      {
        "type": "paragraph",
        "text": "这时，医生有时会建议遗传检测。它不是为了给疾病增加一个更复杂的名字，而是想弄清：这个人的 CVID 表现，背后是否藏着一条更具体的免疫系统线索。"
      },
      {
        "type": "heading",
        "text": "CVID 像一把伞"
      },
      {
        "type": "paragraph",
        "text": "CVID 是一个很重要的诊断名称，但它并不意味着所有患者患的是同一种、由同一个基因造成的疾病。"
      },
      {
        "type": "paragraph",
        "text": "可以把它想成一把大伞。伞下的人有一个共同点：身体难以做出足量、有效、持久的抗体。但有人是 B 细胞收到信号的方式出了问题，有人是 B 细胞在成熟过程中停住了，有人则是免疫系统的“刹车”不够稳定。"
      },
      {
        "type": "paragraph",
        "text": "最后，他们都可能出现低 IgG、抗体反应不佳和反复感染，于是看起来像同一种疾病。可回头看时，走到这把伞下的路并不相同。"
      },
      {
        "type": "heading",
        "text": "当 CVID 有了更具体的名字"
      },
      {
        "type": "paragraph",
        "text": "随着遗传研究发展，医生发现有些人最初表现得像 CVID，后来却能找到更具体的单基因免疫疾病。"
      },
      {
        "type": "paragraph",
        "text": "例如："
      },
      {
        "type": "paragraph",
        "text": "CTLA4 或 LRBA相关疾病，常让人同时关注自身免疫、肠病、脾大、淋巴结增大或肺部炎症；"
      },
      {
        "type": "paragraph",
        "text": "PIK3CD、PIK3R1相关疾病，可能伴随异常淋巴细胞增生、病毒感染或免疫细胞过度活化；"
      },
      {
        "type": "paragraph",
        "text": "NFKB1、NFKB2、IKZF1等相关疾病，可能影响 B 细胞成熟、抗体形成，或带来更广泛的免疫表现；"
      },
      {
        "type": "paragraph",
        "text": "CD19、CD21、CD81、TACI、BAFF-R、ICOS、IL21/IL21R等分子的异常，则帮助研究者理解 B 细胞为什么难以完成抗体记忆。"
      },
      {
        "type": "paragraph",
        "text": "这些疾病常被称作 更具体的单基因免疫缺陷。它们的临床表现与 CVID 相似，却往往能找到更明确的遗传和生物学解释。"
      },
      {
        "type": "heading",
        "text": "基因不是唯一的答案"
      },
      {
        "type": "paragraph",
        "text": "听到“遗传”时，很多人会立刻想到：是不是一定遗传自父母？会不会传给孩子？"
      },
      {
        "type": "paragraph",
        "text": "实际情况比这复杂。"
      },
      {
        "type": "paragraph",
        "text": "有些此类疾病确实由一个基因的致病变异主要造成，称为单基因疾病。有些是常染色体显性遗传：携带变异的父母，每次生育时，子女通常有 50% 的概率继承这一变异。也有些是常染色体隐性遗传：父母可能没有明显症状，却各自携带一份变异，孩子同时继承两份后才可能发病。"
      },
      {
        "type": "paragraph",
        "text": "但还有不少 CVID 患者，并没有找到一个单独负责的基因。研究者认为，多个遗传因素叠加、尚未认识的基因变化，以及感染经历和环境因素，都可能参与。"
      },
      {
        "type": "paragraph",
        "text": "因此，基因检测没有找到明确答案，并不代表患者“没有病因”，更不表示病情不真实。它只是说明，目前的科学还没能把这条路完整画出来。"
      },
      {
        "type": "heading",
        "text": "什么样的情况会让医生想到遗传线索"
      },
      {
        "type": "paragraph",
        "text": "遗传检测不一定适合或必须用于每位 CVID 患者。但以下情况常让医生更愿意寻找具体线索："
      },
      {
        "type": "paragraph",
        "text": "很早就出现反复感染或低免疫球蛋白；"
      },
      {
        "type": "paragraph",
        "text": "家族中有多人出现类似问题；"
      },
      {
        "type": "paragraph",
        "text": "除感染外，还有明显的自身免疫、肠病、脾大、淋巴结增大、肺部炎症或肿瘤相关线索；"
      },
      {
        "type": "paragraph",
        "text": "免疫表现看起来不像单纯抗体不足，而像“抗体不足加免疫失调”；"
      },
      {
        "type": "paragraph",
        "text": "检测结果可能帮助判断家族成员是否需要进一步评估。"
      },
      {
        "type": "paragraph",
        "text": "这些只是提示，不是规则。没有家族史，也可能有单基因疾病；有家族中的类似症状，也不一定一定能找到同一个基因答案。"
      },
      {
        "type": "heading",
        "text": "一份遗传报告，为什么不能只看结论"
      },
      {
        "type": "paragraph",
        "text": "遗传报告常见三个词："
      },
      {
        "type": "paragraph",
        "text": "致病（pathogenic）：现有证据支持该变异会导致相关疾病；"
      },
      {
        "type": "paragraph",
        "text": "可能致病（likely pathogenic）：证据很强，但还差最后一步确认；"
      },
      {
        "type": "paragraph",
        "text": "意义未明变异（VUS）：目前证据不足，无法判断它是否与疾病有关。"
      },
      {
        "type": "paragraph",
        "text": "VUS 很容易让人焦虑，因为它看起来像“找到了一点问题”。但它真正的意思是：现在还不知道。"
      },
      {
        "type": "paragraph",
        "text": "每个人的基因组里都有大量与别人不同的变异，大多数没有害处。医生和遗传团队需要把变异放回真实的人身上看：它是否影响蛋白功能？是否与家族成员的症状一起出现？是否能解释患者的免疫检查和临床表现？"
      },
      {
        "type": "paragraph",
        "text": "只有当这些线索彼此支持时，变异才可能从一个字母变化，变成真正有意义的医学答案。"
      },
      {
        "type": "heading",
        "text": "同一个变异，不一定有同一个故事"
      },
      {
        "type": "paragraph",
        "text": "有些家庭最难理解的是：为什么父母和孩子带着同一个变异，表现却完全不同？"
      },
      {
        "type": "paragraph",
        "text": "这涉及两个概念。"
      },
      {
        "type": "paragraph",
        "text": "外显率指的是：携带某个致病变异的人，并不一定都会出现能被识别的疾病。\n可变表达指的是：即使都出现表现，轻重和形式也可能不同。"
      },
      {
        "type": "paragraph",
        "text": "例如，有人可能主要是甲状腺自身免疫，有人却出现低丙种球蛋白血症、肠病和肺部炎症。CTLA4 相关疾病就常见这种情况。"
      },
      {
        "type": "paragraph",
        "text": "所以，遗传结果能提供重要线索，但它不是命运时间表。它不能准确写出某人会在什么年龄出现什么问题，也不能替代个体化随访。"
      },
      {
        "type": "heading",
        "text": "找到基因后，真正改变的是什么"
      },
      {
        "type": "paragraph",
        "text": "更具体的遗传诊断最重要的价值，不是多记住一个英文缩写。"
      },
      {
        "type": "paragraph",
        "text": "它可能帮助团队更有针对性地关注某些器官问题，理解为什么这个人会同时有感染和自身免疫，安排家族遗传咨询，或判断是否有相关研究和机制导向治疗方向值得讨论。"
      },
      {
        "type": "paragraph",
        "text": "但它也有边界：找到一个致病基因，不等于已经找到所有症状的原因；找不到基因，也不等于没有方向。"
      },
      {
        "type": "paragraph",
        "text": "对很多家庭来说，遗传检测提供的不是一个完美结局，而是一张更清楚的地图。"
      }
    ],
    "sources": [
      "Tangye SG, et al. Human inborn errors of immunity: 2024 update from the IUIS Expert Committee. Journal of Human Immunity. 2025.",
      "Cunningham-Rundles C, Casanova JL, Boisson B. Genetics and clinical phenotypes in common variable immunodeficiency. Frontiers in Genetics. 2024.",
      "van Schouwenburg PA, et al. The role of genomics in common variable immunodeficiency disorders. Clinical and Experimental Immunology. 2017.",
      "Schwab C, et al. Phenotype, penetrance, and treatment of 133 CTLA-4-insufficient subjects. Journal of Allergy and Clinical Immunology. 2018.",
      "2:36"
    ]
  },
  {
    "slug": "research-progress",
    "category": "research",
    "title": "CVID 目前的科研进展",
    "excerpt": "如果十年前问“CVID 是什么”，答案常常是：一种抗体不足的免疫缺陷。",
    "blocks": [
      {
        "type": "paragraph",
        "text": "如果十年前问“CVID 是什么”，答案常常是：一种抗体不足的免疫缺陷。"
      },
      {
        "type": "paragraph",
        "text": "今天，这句话依然没有错，但已经不够完整。研究者逐渐发现，CVID 更像一组不同原因、不同走向的疾病：有的人主要难以对抗感染；有的人还会出现自身免疫、肠道炎症、肺部问题或淋巴组织增生。"
      },
      {
        "type": "paragraph",
        "text": "科研的目标并不是把疾病说得越来越复杂，而是想回答三个与患者最相关的问题："
      },
      {
        "type": "paragraph",
        "text": "为什么同样是 CVID，每个人的经历不同？"
      },
      {
        "type": "paragraph",
        "text": "哪些人更需要留意肺、肠道、血液或其他器官？"
      },
      {
        "type": "paragraph",
        "text": "能不能从“统一补抗体”逐步走向更适合不同机制的治疗和监测？"
      },
      {
        "type": "heading",
        "text": "研究者先回到 B 细胞"
      },
      {
        "type": "paragraph",
        "text": "CVID 研究最重要的进展之一，是更清楚地看见了 B 细胞并不是简单地“有”或“没有”。"
      },
      {
        "type": "paragraph",
        "text": "许多患者的 B 细胞数量并不特别少，但其中一些很难完成最后几步：无法顺利成为类别转换记忆 B 细胞，或成为能够长期制造抗体的浆细胞。"
      },
      {
        "type": "paragraph",
        "text": "这就像一间工厂还有工人，却难以生产出质量稳定、能长期供应的产品。"
      },
      {
        "type": "paragraph",
        "text": "研究人员因此会观察不同类型的 B 细胞。比如，有些患者的类别转换记忆 B 细胞较少；有些患者的 CD21^low^ B 细胞较多。这些变化与较复杂的临床表现有关，包括自身免疫、脾大或肺部炎症。"
      },
      {
        "type": "paragraph",
        "text": "但这里要特别小心：这不表示某一种 B 细胞检查可以预测一个人的未来。它更像一张地图上的地标，能帮助医生和研究者认识不同的病人群体，却不能独自决定某个人将来一定发生什么。"
      },
      {
        "type": "heading",
        "text": "一个重要的新认识：免疫不足和免疫过强可以同时存在"
      },
      {
        "type": "paragraph",
        "text": "过去，人们容易把免疫缺陷理解成“免疫系统太弱”。但 CVID 研究告诉我们，事情并不总是这样。"
      },
      {
        "type": "paragraph",
        "text": "部分患者的免疫系统在对付病原体时不够有效，却在别的地方太活跃。例如，它可能攻击自己的血小板或红细胞，持续刺激肠道，或让淋巴细胞在肺、脾脏和淋巴结中聚集得太久。"
      },
      {
        "type": "paragraph",
        "text": "研究者特别关注一些帮助免疫系统“踩刹车”的分子，例如 CTLA-4 和 LRBA；也关注影响细胞信号强度的 PI3K、NF-κB、STAT3 等通路。"
      },
      {
        "type": "paragraph",
        "text": "这些研究最有价值的地方，是解释了一个很多患者都会问的问题：\n“为什么我既容易感染，又会有炎症或自身免疫？”"
      },
      {
        "type": "paragraph",
        "text": "答案是：免疫系统不是一个开关。它有许多不同的线路；有的线路太弱，有的线路又没有及时停下。"
      },
      {
        "type": "heading",
        "text": "肺部研究：不只是反复肺炎"
      },
      {
        "type": "paragraph",
        "text": "研究者现在会特别区分两类肺部问题。"
      },
      {
        "type": "paragraph",
        "text": "第一类是反复感染留下的结构性损伤，例如支气管扩张。\n第二类是以免疫炎症为主的肺部问题，例如 GLILD。"
      },
      {
        "type": "paragraph",
        "text": "GLILD 可以理解为免疫细胞在肺内异常聚集、持续活动造成的肺部炎症。它并不等同于感染，也不能只凭一次 CT 就下结论。研究团队通常需要把症状、肺功能、影像、感染排除情况，以及必要时的组织检查放在一起判断。"
      },
      {
        "type": "paragraph",
        "text": "目前较可靠的结论是：肺部问题越早被识别，越有机会在造成更多结构改变前得到评估和管理。仍不确定的是，哪些血液或影像指标最能预测谁会进展，以及哪种干预最适合不同类型的肺部炎症。"
      },
      {
        "type": "heading",
        "text": "肠道研究：正常菌群为什么也值得研究"
      },
      {
        "type": "paragraph",
        "text": "每个人肠道里都住着大量微生物。它们并不全是坏东西；许多微生物本来就是正常生活的一部分。"
      },
      {
        "type": "paragraph",
        "text": "CVID 研究发现，部分有肠道症状的患者，其菌群组成和肠道免疫环境与健康人不同。研究者想知道：是不是黏膜抗体不足、肠道屏障受损和菌群变化互相影响，最后让肠道更容易长期发炎？"
      },
      {
        "type": "paragraph",
        "text": "这条思路很有吸引力，但目前仍处于探索阶段。研究样本通常不大，而且饮食、抗生素、感染、地区和药物都会影响菌群。"
      },
      {
        "type": "paragraph",
        "text": "因此，“微生物组”目前是帮助理解疾病的一扇窗，还不是可以为每位患者开出同样方案的答案。"
      },
      {
        "type": "heading",
        "text": "遗传研究：有些患者找到了更具体的疾病名字"
      },
      {
        "type": "paragraph",
        "text": "随着基因检测进步，研究者已经确认许多单基因免疫疾病可以表现得像 CVID。"
      },
      {
        "type": "paragraph",
        "text": "有些基因与 B 细胞成熟有关，例如 CD19、CD21、CD81、TACI、BAFF-R、ICOS 和 IL21R；有些与免疫调节或细胞信号有关，例如 CTLA4、LRBA、NFKB1、NFKB2、PIK3CD、STAT3 GOF。"
      },
      {
        "type": "paragraph",
        "text": "这并不表示所有 CVID 都由一个基因决定。实际上，多数患者还没有明确的单基因答案。"
      },
      {
        "type": "paragraph",
        "text": "但这些发现像一盏盏灯：它们让研究者看见，抗体不足可以从很多不同的免疫路径发生。对部分患者来说，更具体的遗传诊断也可能影响监测重点、家族咨询和研究方向。"
      },
      {
        "type": "heading",
        "text": "新技术正在看什么"
      },
      {
        "type": "paragraph",
        "text": "过去，研究人员常把一管血里的许多细胞混在一起测量，得到一个“平均结果”。"
      },
      {
        "type": "paragraph",
        "text": "现在，单细胞测序可以把 B 细胞、T 细胞以及更细的小群体分开看；多组学研究则尝试把基因、细胞活动、蛋白质和代谢信息放在一起分析；空间生物学还能观察肺或肠道组织里，哪些细胞彼此靠近、互相发送信号。"
      },
      {
        "type": "paragraph",
        "text": "这些技术很擅长发现新线索。例如，研究者可以看到某一群 B 细胞是否停在不成熟阶段，或某一类 T 细胞是否长期处于过度活化状态。"
      },
      {
        "type": "paragraph",
        "text": "不过，这些新技术还不是每位患者的常规检查。很多发现来自小样本研究，需要在更多不同地区、不同年龄的患者中反复验证。"
      },
      {
        "type": "heading",
        "text": "研究是否会带来更精准的治疗？"
      },
      {
        "type": "paragraph",
        "text": "这是大家最关心的问题之一。"
      },
      {
        "type": "paragraph",
        "text": "现在最明确的基础治疗，仍然是补充免疫球蛋白来减少部分感染。研究正在尝试做得更进一步：如果一个人的免疫失衡与某条特定通路有关，能否更有针对性地调节这条通路？"
      },
      {
        "type": "paragraph",
        "text": "例如，CTLA-4 相关免疫失调、PI3Kδ 过度活化等疾病，已经推动了机制导向治疗的研究。"
      },
      {
        "type": "paragraph",
        "text": "但“有机制上的道理”不等于“已经适合所有患者”。有些结果来自细胞实验，有些来自病例报告或小型患者队列；真正能确认长期安全性和效果的，仍需要更大的临床研究。"
      },
      {
        "type": "paragraph",
        "text": "对患者来说，最重要的不是记住每一种新药，而是知道研究正在努力让“同一种 CVID”不再只有同一种解释。"
      },
      {
        "type": "heading",
        "text": "患者登记：看见一代人的疾病轨迹"
      },
      {
        "type": "paragraph",
        "text": "CVID 很少见，单个医院看到的患者有限。患者登记和长期队列研究因此特别重要。"
      },
      {
        "type": "paragraph",
        "text": "研究者通过多年记录感染、肺部影像、肠道表现、自身免疫、血液检查、遗传结果和治疗情况，才能慢慢看见哪些问题常常一起发生，哪些因素可能提示更高风险。"
      },
      {
        "type": "paragraph",
        "text": "这类研究不像一项新药试验那样吸引眼球，却是未来实现更准确分型和长期风险预测的基础。"
      },
      {
        "type": "heading",
        "text": "目前已经知道什么"
      },
      {
        "type": "paragraph",
        "text": "CVID 不只是抗体低；部分患者还存在免疫失调。"
      },
      {
        "type": "paragraph",
        "text": "B 细胞成熟和浆细胞形成异常，是很多患者的重要线索。"
      },
      {
        "type": "paragraph",
        "text": "自身免疫、肠病、肺部炎症和淋巴组织增生，确实是 CVID 的一部分临床图景。"
      },
      {
        "type": "paragraph",
        "text": "一部分患者可找到更具体的单基因病因。"
      },
      {
        "type": "paragraph",
        "text": "免疫球蛋白替代可减少部分感染，但不能自动解决所有炎症和自身免疫问题。"
      },
      {
        "type": "heading",
        "text": "还在寻找什么"
      },
      {
        "type": "paragraph",
        "text": "哪些检查最能预测肺病、肠病或自身免疫风险？"
      },
      {
        "type": "paragraph",
        "text": "为什么相似的免疫检查结果，会带来不同的人生经历？"
      },
      {
        "type": "paragraph",
        "text": "哪些患者适合哪一种机制导向治疗？"
      },
      {
        "type": "paragraph",
        "text": "肠道微生物组、炎症信号和遗传背景各自扮演什么角色？"
      },
      {
        "type": "paragraph",
        "text": "如何让早期研究发现真正变成安全、可靠的临床工具？"
      }
    ],
    "sources": [
      "Bonilla FA, et al. International Consensus Document (ICON): Common Variable Immunodeficiency Disorders. Journal of Allergy and Clinical Immunology. 2016.",
      "Ho HE, Cunningham-Rundles C. Non-infectious complications of common variable immunodeficiency. Frontiers in Immunology. 2020.",
      "Tangye SG, et al. Human inborn errors of immunity: 2024 update from the IUIS Expert Committee. Journal of Human Immunity. 2025.",
      "Cunningham-Rundles C, Casanova JL, Boisson B. Genetics and clinical phenotypes in CVID. Frontiers in Genetics. 2024.",
      "van Stigt AC, et al. Diagnostic testing for interstitial lung disease in CVID: a systematic review. Frontiers in Immunology. 2023."
    ]
  },
  {
    "slug": "cd19",
    "category": "gene",
    "title": "CD19：帮助 B 细胞听清“开始制造抗体”的信号",
    "excerpt": "B 细胞每天都会遇到很多信息：有些来自食物，有些来自正常存在于身体里的微生物，有些才是真正的感染。",
    "blocks": [
      {
        "type": "paragraph",
        "text": "B 细胞每天都会遇到很多信息：有些来自食物，有些来自正常存在于身体里的微生物，有些才是真正的感染。"
      },
      {
        "type": "paragraph",
        "text": "它不能每听见一点动静就全力出动。否则，免疫系统会太容易疲惫，也可能误伤自己。可如果它对真正的危险反应得太慢，病原体又会趁机进入。"
      },
      {
        "type": "paragraph",
        "text": "CD19 的工作，就是帮助 B 细胞分辨那些值得认真回应的信号。"
      },
      {
        "type": "heading",
        "text": "B 细胞身边的“扩音器”"
      },
      {
        "type": "paragraph",
        "text": "B 细胞表面有一种主要的识别装置，可以抓住病原体身上的特征。可抓住目标只是第一步。"
      },
      {
        "type": "paragraph",
        "text": "接下来，B 细胞要决定：这是不是一次真正的感染？我是否应该进入淋巴结里的训练营，制造更多抗体，并为下一次感染留下记忆？"
      },
      {
        "type": "paragraph",
        "text": "CD19 就像装在 B 细胞上的小型扩音器。它和 CD21、CD81 等伙伴一起工作，让 B 细胞收到的感染信号更清楚、更有分量。"
      },
      {
        "type": "paragraph",
        "text": "它不直接制造抗体，也不直接杀死病原体。它做的是另一件很重要的事：帮助 B 细胞相信，“这一次该认真开始了。”"
      },
      {
        "type": "heading",
        "text": "从听见信号，到留下记忆"
      },
      {
        "type": "paragraph",
        "text": "当 CD19 帮助 B 细胞听清信号后，B 细胞就更容易进入后续的训练。"
      },
      {
        "type": "paragraph",
        "text": "有些 B 细胞会先制造 IgM，帮助身体尽快围住感染；另一些则在生发中心里继续学习，慢慢形成更适合长期保护的 IgG 或 IgA。最后，一部分成为记忆 B 细胞，一部分成为浆细胞。"
      },
      {
        "type": "paragraph",
        "text": "记忆 B 细胞负责记住病原体。浆细胞则像抗体工厂，持续提供保护。"
      },
      {
        "type": "paragraph",
        "text": "CD19 虽然只是 B 细胞表面的一个分子，却站在这条路的前面。它影响的是：B 细胞能不能把“见过病原体”顺利变成“真正开始建立抗体记忆”。"
      },
      {
        "type": "heading",
        "text": "如果 CD19 工作不足"
      },
      {
        "type": "paragraph",
        "text": "如果 CD19 的功能明显受影响，B 细胞接收到的感染信号就可能不够清楚。"
      },
      {
        "type": "paragraph",
        "text": "它们不是完全不知道病原体来了，而是可能没有获得足够强的推动力，去完成后面的抗体训练和记忆建立。于是，身体里的 B 细胞有时仍然存在，但高质量、持久的抗体保护不够。"
      },
      {
        "type": "paragraph",
        "text": "这可能带来："
      },
      {
        "type": "paragraph",
        "text": "IgG 或 IgA 偏低；"
      },
      {
        "type": "paragraph",
        "text": "对疫苗或既往感染的抗体反应不够可靠；"
      },
      {
        "type": "paragraph",
        "text": "记忆 B 细胞较少；"
      },
      {
        "type": "paragraph",
        "text": "鼻窦炎、支气管炎或肺炎等呼吸道感染反复发生。"
      },
      {
        "type": "paragraph",
        "text": "这也解释了一个重要事实：B 细胞数量正常，不代表抗体功能一定正常。"
      },
      {
        "type": "heading",
        "text": "CD19 和 CVID 的关系"
      },
      {
        "type": "paragraph",
        "text": "CVID 的核心是抗体不足。对许多患者来说，医生首先看到的是低免疫球蛋白、疫苗抗体反应不佳和反复感染。"
      },
      {
        "type": "paragraph",
        "text": "CD19 功能缺失是少数能够解释这一现象的明确原因之一。它说明，CVID 有时不是 B 细胞完全缺席，而是 B 细胞在接收和放大感染信号时出现了问题。"
      },
      {
        "type": "paragraph",
        "text": "不过，绝大多数 CVID 患者并没有 CD19 缺陷。CD19 的意义更像一扇窗：通过它，研究者看见了 B 细胞早期信号为什么对抗体记忆如此重要。"
      },
      {
        "type": "heading",
        "text": "研究已经知道什么"
      },
      {
        "type": "paragraph",
        "text": "较可靠的研究发现，CD19 是 B 细胞信号协作小组的重要成员。CD19 功能缺失可导致以抗体不足和反复感染为主的遗传性免疫疾病；患者的 B 细胞可能仍在，但抗体反应和记忆形成受到影响。 IUIS 2024 分类"
      },
      {
        "type": "paragraph",
        "text": "目前已经报道的 CD19 缺陷患者很少，所以研究者对不同变异造成的差异、长期器官影响和个体病程，仍然没有完整答案。"
      }
    ],
    "sources": [
      "Tangye SG, et al. The 2024 update of IUIS phenotypic classification of human inborn errors of immunity.",
      "Wentink MWJ, et al. Deficiencies in the CD19 complex. Clinical and Experimental Immunology. 2018.",
      "Bogaert DJA, et al. Genes associated with common variable immunodeficiency. Journal of Medical Genetics. 2016."
    ]
  },
  {
    "slug": "cd81",
    "category": "gene",
    "title": "CD81：让 B 细胞的“信号接收台”正常运转",
    "excerpt": "CD81 是 B 细胞表面的一个小分子。单独看它，它不像抗体那样容易理解，也不像 CTLA-4 那样像一脚明显的刹车；但它承担着一件很基础的工作：帮助 B 细胞把重要的信号接收台搭稳。",
    "blocks": [
      {
        "type": "paragraph",
        "text": "CD81 是 B 细胞表面的一个小分子。单独看它，它不像抗体那样容易理解，也不像 CTLA-4 那样像一脚明显的刹车；但它承担着一件很基础的工作：帮助 B 细胞把重要的信号接收台搭稳。"
      },
      {
        "type": "paragraph",
        "text": "如果把 B 细胞想成一间负责制造抗体的工厂，CD81 不是工厂里的生产线，也不是最终送出的抗体。它更像把通讯设备固定在墙上的安装员。通讯设备没装好，工厂仍在，工人也仍在，却更难听清外面传来的任务。"
      },
      {
        "type": "heading",
        "text": "B 细胞为什么需要一张稳定的“接收台”"
      },
      {
        "type": "paragraph",
        "text": "一次感染发生后，B 细胞会遇到病原体留下的抗原。它先用自己的识别器抓住目标，但这还不够。"
      },
      {
        "type": "paragraph",
        "text": "B 细胞必须进一步判断：“这是不是真的值得我投入？”“我是否应该进入生发中心训练，最后制造抗体并留下记忆？”"
      },
      {
        "type": "paragraph",
        "text": "这时，B 细胞表面的一组分子会一起工作。CD19 是其中帮助放大信号的重要成员；CD21 帮助读取病原体被免疫系统标记后的线索；CD81 则帮助 CD19 稳定地出现在 B 细胞表面。"
      },
      {
        "type": "paragraph",
        "text": "这三个分子可以想成一张协作桌："
      },
      {
        "type": "paragraph",
        "text": "CD21 帮忙看见线索；"
      },
      {
        "type": "paragraph",
        "text": "CD19 帮忙把声音放大；"
      },
      {
        "type": "paragraph",
        "text": "CD81 确保 CD19 能留在正确位置、正常工作。"
      },
      {
        "type": "paragraph",
        "text": "没有 CD81，CD19 可能无法顺利留在 B 细胞表面。于是 B 细胞收到的感染信号会变得模糊。"
      },
      {
        "type": "heading",
        "text": "当 CD81 不能正常工作"
      },
      {
        "type": "paragraph",
        "text": "CD81 功能明显不足时，B 细胞并不会全部消失。患者血液中仍可能检测到 B 细胞。"
      },
      {
        "type": "paragraph",
        "text": "但这些 B 细胞更像是通讯不良的工人：它们可能知道外面有感染，却难以获得足够清晰、有力的启动信号。因此，后续形成高质量抗体记忆的过程可能受到影响。"
      },
      {
        "type": "paragraph",
        "text": "有些 B 细胞难以顺利进入或完成生发中心训练；有些难以成为类别转换记忆 B 细胞；有些则难以形成稳定、长期制造抗体的浆细胞。"
      },
      {
        "type": "paragraph",
        "text": "最后，患者可能出现："
      },
      {
        "type": "paragraph",
        "text": "IgG 偏低；"
      },
      {
        "type": "paragraph",
        "text": "IgA 或 IgM 偏低，也可能仍在正常范围；"
      },
      {
        "type": "paragraph",
        "text": "对疫苗或既往感染形成的抗体反应不足；"
      },
      {
        "type": "paragraph",
        "text": "鼻窦炎、支气管炎、肺炎等呼吸道感染反复发生。"
      },
      {
        "type": "paragraph",
        "text": "这再次说明，B 细胞的数量和 B 细胞的功能并不是一回事。"
      },
      {
        "type": "heading",
        "text": "为什么 CD81 缺陷看起来像 CD19 缺陷"
      },
      {
        "type": "paragraph",
        "text": "CD81 和 CD19 的关系很紧密。"
      },
      {
        "type": "paragraph",
        "text": "当 CD19 本身发生功能缺失时，B 细胞难以放大感染信号；当 CD81 功能缺失时，CD19 可能难以正常表达在细胞表面。两种情况的起点不同，结果却可能相似：B 细胞收不到足够清楚的“开始建立抗体保护”的信号。"
      },
      {
        "type": "paragraph",
        "text": "因此，CD81 缺陷有时被形容为“在细胞层面模仿 CD19 缺陷”。这不是说两种疾病完全一样，而是说它们会在同一条 B 细胞信号链路上造成障碍。"
      },
      {
        "type": "heading",
        "text": "它与 CVID 有什么关系"
      },
      {
        "type": "paragraph",
        "text": "CVID 是一个以抗体不足和抗体功能不佳为核心的临床诊断。CD81 缺陷患者可能出现低免疫球蛋白、抗体记忆不足和反复感染，因此外表看起来像 CVID。"
      },
      {
        "type": "paragraph",
        "text": "但如果检测发现 CD81 的明确致病变异，诊断就能从“抗体为什么不足还不清楚”，进一步走向“B 细胞信号接收台出了什么问题”。"
      },
      {
        "type": "paragraph",
        "text": "这类更具体的解释，意义不是把患者从 CVID 中“分出去”，而是帮助理解其抗体缺陷背后具体的生物学原因。"
      },
      {
        "type": "heading",
        "text": "遗传线索怎样理解"
      },
      {
        "type": "paragraph",
        "text": "目前确认的 CD81 缺陷通常是常染色体隐性遗传。"
      },
      {
        "type": "paragraph",
        "text": "这意味着患者往往从父母各继承一份功能明显受影响的 CD81 变异。父母各自只有一份变异时，多数仍有另一份正常基因，因此未必会出现典型症状。"
      },
      {
        "type": "paragraph",
        "text": "遗传报告里出现 CD81 变异，不自动等于确诊。团队还需要看："
      },
      {
        "type": "paragraph",
        "text": "两份 CD81 基因是否都受到影响；"
      },
      {
        "type": "paragraph",
        "text": "B 细胞表面的 CD19 是否确实减少或缺失；"
      },
      {
        "type": "paragraph",
        "text": "患者的免疫球蛋白、疫苗抗体反应和 B 细胞记忆是否符合；"
      },
      {
        "type": "paragraph",
        "text": "变异是否被归类为致病或可能致病。"
      },
      {
        "type": "paragraph",
        "text": "如果是意义未明变异（VUS），它只能说明“需要继续了解”，不能单独解释疾病或预测家属的风险。"
      },
      {
        "type": "heading",
        "text": "目前研究已经知道什么"
      },
      {
        "type": "paragraph",
        "text": "较可靠的细胞研究和已报道病例支持：CD81 是 CD19 信号复合体的重要成员；缺失 CD81 会影响 CD19 在 B 细胞表面的表达，并造成以抗体不足为主的免疫缺陷。IUIS 2024 分类也将 CD81 缺陷列入以抗体缺陷为主的 IEI。 IUIS 2024 分类"
      },
      {
        "type": "paragraph",
        "text": "但 CD81 缺陷极为罕见。我们对长期肺部风险、感染严重程度、不同变异之间的差异，以及是否存在稳定的器官风险模式，仍然了解有限。现有结论主要来自少数患者和细胞实验，需要更多家系和长期随访来补全。"
      }
    ],
    "sources": [
      "Tangye SG, et al. Human inborn errors of immunity: 2024 update from the IUIS Expert Committee. Journal of Human Immunity. 2025.",
      "Wentink MWJ, et al. Deficiencies in the CD19 complex. Clinical and Experimental Immunology. 2018.",
      "Bogaert DJA, et al. Genes associated with common variable immunodeficiency. Journal of Medical Genetics. 2016."
    ]
  },
  {
    "slug": "cr2-cd21",
    "category": "gene",
    "title": "CR2/CD21：帮助 B 细胞认出“已经被标记的敌人”",
    "excerpt": "一次感染开始后，免疫系统并不是只有一种方法发现病原体。",
    "blocks": [
      {
        "type": "paragraph",
        "text": "一次感染开始后，免疫系统并不是只有一种方法发现病原体。"
      },
      {
        "type": "paragraph",
        "text": "B 细胞有自己的识别器，能直接抓住病原体的一部分；补体系统则会在一些病原体表面留下标记，像贴上一张“这个目标值得注意”的荧光贴纸。CD21 的工作，就是帮助 B 细胞读懂这张贴纸。"
      },
      {
        "type": "paragraph",
        "text": "它让 B 细胞不仅能看见病原体，还能知道：免疫系统已经注意到它了，现在值得认真启动抗体反应。"
      },
      {
        "type": "heading",
        "text": "病原体身上的“荧光贴纸”"
      },
      {
        "type": "paragraph",
        "text": "补体是血液和组织液中的一组蛋白质。它们像一支很早到场的协作队伍，能附着在病原体表面，帮助免疫系统识别和清除目标。"
      },
      {
        "type": "paragraph",
        "text": "其中一种标记叫 C3d。病原体被 C3d 标记后，就像背上了一块小小的荧光牌。"
      },
      {
        "type": "paragraph",
        "text": "CD21 是 B 细胞表面能读取这块牌子的分子。它也叫 CR2，即“补体受体 2”。当 B 细胞一边用自己的识别器抓住病原体，一边又通过 CD21 看见 C3d 标记时，收到的信息会更完整。"
      },
      {
        "type": "paragraph",
        "text": "这就像走夜路时，不只是看见远处有人，还看见对方戴着反光背心。B 细胞更容易确认：这是一个需要认真处理的目标。"
      },
      {
        "type": "heading",
        "text": "CD21 不只在 B 细胞身边工作"
      },
      {
        "type": "paragraph",
        "text": "CD21 不只存在于成熟 B 细胞表面，也存在于淋巴结和脾脏中的滤泡树突细胞上。"
      },
      {
        "type": "paragraph",
        "text": "这里的“树突细胞”不是前面感染故事中负责传递抗原的那类细胞。滤泡树突细胞更像淋巴结里的展览管理员：它们把病原体线索保留在表面，让正在训练的 B 细胞反复查看。"
      },
      {
        "type": "paragraph",
        "text": "在生发中心里，B 细胞需要一次又一次比较：我做出的抗体，能不能更好地抓住这个目标？CD21 帮助保留这些被标记的抗原线索，因此也可能影响 B 细胞训练和抗体记忆的质量。"
      },
      {
        "type": "heading",
        "text": "CD21 与 CD19、CD81 是一组伙伴"
      },
      {
        "type": "paragraph",
        "text": "CD21 很少单独工作。"
      },
      {
        "type": "paragraph",
        "text": "它和 CD19、CD81 同处于 B 细胞表面的协作小组中："
      },
      {
        "type": "paragraph",
        "text": "CD21 帮忙读懂病原体被补体标记后的线索；"
      },
      {
        "type": "paragraph",
        "text": "CD19 帮助放大 B 细胞收到的信号；"
      },
      {
        "type": "paragraph",
        "text": "CD81 帮助 CD19 稳定地待在细胞表面。"
      },
      {
        "type": "paragraph",
        "text": "三者像一张小小的接收台。CD21 负责看见“荧光贴纸”，CD19 负责让信号更响，CD81 确保设备装得稳。"
      },
      {
        "type": "paragraph",
        "text": "这也是为什么 CD21、CD19 和 CD81 的缺陷都可能带来抗体不足，却又不是同一种疾病。"
      },
      {
        "type": "heading",
        "text": "如果 CD21 功能不足"
      },
      {
        "type": "paragraph",
        "text": "如果 CD21 明显缺失或功能受损，B 细胞不一定完全无法工作。"
      },
      {
        "type": "paragraph",
        "text": "它们仍能识别部分病原体，也仍可能对某些疫苗产生抗体。但当免疫系统需要利用补体标记来增强反应时，B 细胞会少掉一条重要线索。"
      },
      {
        "type": "paragraph",
        "text": "已报道的 CD21 缺陷患者可有："
      },
      {
        "type": "paragraph",
        "text": "IgG 偏低；"
      },
      {
        "type": "paragraph",
        "text": "类别转换记忆 B 细胞减少；"
      },
      {
        "type": "paragraph",
        "text": "对肺炎球菌疫苗等部分抗原的抗体反应不足；"
      },
      {
        "type": "paragraph",
        "text": "反复鼻窦炎、支气管炎或肺炎等呼吸道感染。"
      },
      {
        "type": "paragraph",
        "text": "这并不表示 CD21 缺陷患者一定无法产生所有抗体。事实上，早期人类研究中，有患者对部分蛋白类疫苗仍能产生反应，却对肺炎球菌多糖疫苗的反应较弱。这个发现很重要：它说明 CD21 影响的是免疫反应中的某些环节，而不是把整套抗体系统完全关闭。 CD21 缺陷的首例人类研究"
      },
      {
        "type": "heading",
        "text": "为什么它可能表现得像 CVID"
      },
      {
        "type": "paragraph",
        "text": "从患者经历来看，CD21 缺陷和 CVID 都可能表现为低免疫球蛋白、疫苗抗体反应不足和反复呼吸道感染。"
      },
      {
        "type": "paragraph",
        "text": "但 CD21 缺陷让我们更具体地看见了问题的一部分：B 细胞可能没有很好地利用补体留下的线索，也可能难以在生发中心里有效地建立记忆。"
      },
      {
        "type": "paragraph",
        "text": "因此，CD21 缺陷可以为 CVID 提供一种更具体的生物学解释。它说明 CVID 并不总是“B 细胞没有做抗体”，有时是 B 细胞在收集、理解和保存感染信息的过程中少了一位重要伙伴。"
      },
      {
        "type": "heading",
        "text": "遗传线索怎样理解"
      },
      {
        "type": "paragraph",
        "text": "目前确认的 CD21 缺陷通常为常染色体隐性遗传。"
      },
      {
        "type": "paragraph",
        "text": "患者往往从父母各继承一份功能明显受影响的 CR2 基因变异。父母各自只有一份变异时，通常仍有另一份能工作的基因，因此未必有典型抗体缺陷。"
      },
      {
        "type": "paragraph",
        "text": "不过，遗传报告出现 CR2/CD21 变异，并不自动等于确诊。团队仍需要结合："
      },
      {
        "type": "paragraph",
        "text": "是否两份基因都受到明显影响；"
      },
      {
        "type": "paragraph",
        "text": "B 细胞表面 CD21 是否确实缺失或显著减少；"
      },
      {
        "type": "paragraph",
        "text": "IgG、疫苗抗体反应和记忆 B 细胞是否符合；"
      },
      {
        "type": "paragraph",
        "text": "变异是否已有可靠的致病证据。"
      },
      {
        "type": "paragraph",
        "text": "意义未明变异（VUS）只能表示“目前还不能确定”，不能独自解释患者的疾病，也不能单独用于推断家属风险。"
      },
      {
        "type": "heading",
        "text": "目前研究已经知道什么"
      },
      {
        "type": "paragraph",
        "text": "较可靠的研究支持，CD21 是 B 细胞协作信号系统的一部分，能识别补体标记的抗原，并参与抗体反应和免疫记忆形成。IUIS 2024 分类将 CD21 缺陷列入以抗体缺陷为主的 IEI；其中列出的代表性表现包括低 IgG、肺炎球菌抗体反应受损和反复感染。 IUIS 2024 分类"
      },
      {
        "type": "paragraph",
        "text": "但这一疾病极为罕见。关于 CD21 缺陷是否会增加某些自身免疫、病毒感染或长期肺部问题的风险，现有资料仍然不足。实验室研究也提示，CD21 在不同细胞和不同阶段的作用可能比最初理解的更复杂，仍需要更多患者资料和机制研究。 CD21 功能再讨论"
      }
    ],
    "sources": [
      "Thiel J, et al. Genetic CD21 deficiency is associated with hypogammaglobulinemia. Journal of Allergy and Clinical Immunology. 2012.",
      "Tangye SG, et al. Human inborn errors of immunity: 2024 update from the IUIS Expert Committee. Journal of Human Immunity. 2025.",
      "Simon N, et al. Revisiting the coreceptor function of CR2/CD21. Frontiers in Immunology. 2021."
    ]
  },
  {
    "slug": "ms4a1-cd20",
    "category": "gene",
    "title": "MS4A1/CD20：B 细胞启动时，为什么需要这一阵“钙信号”？",
    "excerpt": "B 细胞平时看起来很安静。它们在血液、淋巴结和脾脏中巡逻，等待自己认识的病原体出现。",
    "blocks": [
      {
        "type": "paragraph",
        "text": "B 细胞平时看起来很安静。它们在血液、淋巴结和脾脏中巡逻，等待自己认识的病原体出现。"
      },
      {
        "type": "paragraph",
        "text": "可一旦真的遇到感染，B 细胞需要在很短时间内从“安静等待”切换到“开始行动”。它要接收信号、调整内部结构、进入训练、形成记忆，最后才能制造足够有效的抗体。"
      },
      {
        "type": "paragraph",
        "text": "CD20 就参与了这个启动过程。"
      },
      {
        "type": "paragraph",
        "text": "它不是用来抓住病原体的手，也不是直接制造抗体的工厂。它更像 B 细胞按下启动键后，帮助细胞内部亮起的一套电路。"
      },
      {
        "type": "heading",
        "text": "B 细胞启动时，内部会发生什么"
      },
      {
        "type": "paragraph",
        "text": "当 B 细胞识别到病原体时，表面的识别器会把消息传到细胞内部。"
      },
      {
        "type": "paragraph",
        "text": "接下来，细胞内部会发生一连串变化。其中一个重要步骤是钙离子的流动。钙并不只是骨骼和牙齿里的成分；在免疫细胞中，它也像一种短暂的内部信号。钙信号出现后，B 细胞才更容易开始增殖、表达新的基因、与其他细胞协作，并进入后续的抗体训练。"
      },
      {
        "type": "paragraph",
        "text": "CD20 与这套钙信号有关。"
      },
      {
        "type": "paragraph",
        "text": "可以把 B 细胞想成一间夜间关闭的工厂。病原体的信息来到门口后，B 细胞识别器先拉响门铃；CD20 帮助厂房里的灯一盏盏亮起来。灯亮了，工人才能找到自己的位置，生产线才能启动。"
      },
      {
        "type": "heading",
        "text": "CD20 和 B 细胞受体如何合作"
      },
      {
        "type": "paragraph",
        "text": "CD20 主要出现在成熟 B 细胞表面。"
      },
      {
        "type": "paragraph",
        "text": "它和 B 细胞识别器之间并不是永远固定不动的关系。平时，它们靠得比较近；当 B 细胞真正接收到抗原信号后，周围的分子需要重新排布，形成一个能把信息传入细胞的工作区域。"
      },
      {
        "type": "paragraph",
        "text": "研究显示，CD20 参与这一过程，并与 B 细胞内部钙信号有关。若这一环节不顺利，B 细胞虽然看见病原体，却可能无法完成最有效的启动。"
      },
      {
        "type": "paragraph",
        "text": "这与 CD19、CD21、CD81 的故事有一点不同。那一组分子更像帮助 B 细胞接收和放大外界信息；CD20 更接近 B 细胞真正开始行动时的内部开关。"
      },
      {
        "type": "heading",
        "text": "如果 CD20 功能不足"
      },
      {
        "type": "paragraph",
        "text": "CD20 功能缺失时，B 细胞通常不会完全消失。"
      },
      {
        "type": "paragraph",
        "text": "它们仍可在血液中被检测到，也能从骨髓发育出来。但它们在面对某些抗原时，可能难以形成足够强、足够持久的抗体反应。"
      },
      {
        "type": "paragraph",
        "text": "已报道患者可出现："
      },
      {
        "type": "paragraph",
        "text": "反复鼻窦炎、支气管炎或肺炎；"
      },
      {
        "type": "paragraph",
        "text": "IgG 偏低；"
      },
      {
        "type": "paragraph",
        "text": "IgM 和 IgA 有时仍在正常范围，甚至偏高；"
      },
      {
        "type": "paragraph",
        "text": "类别转换记忆 B 细胞减少；"
      },
      {
        "type": "paragraph",
        "text": "对某些需要 B 细胞独立完成的抗原，抗体反应较弱。"
      },
      {
        "type": "paragraph",
        "text": "早期人类研究提示，CD20 缺陷尤其会影响一类不太依赖 T 细胞协助的抗体反应。这类反应对某些细菌表面的重复结构很重要。它也帮助解释，为什么患者并不是对所有病原体都毫无反应，却仍会特别容易反复出现呼吸道细菌感染。 CD20 缺陷的人类研究"
      },
      {
        "type": "heading",
        "text": "为什么 CD20 缺陷会表现得像 CVID"
      },
      {
        "type": "paragraph",
        "text": "CVID 的共同表现是抗体不足和抗体保护不可靠。"
      },
      {
        "type": "paragraph",
        "text": "CD20 缺陷患者可能有低 IgG、记忆 B 细胞不足和反复感染，因此从临床表现看，很像 CVID。但 CD20 缺陷提供了一个更具体的解释：问题可能发生在 B 细胞接收到感染信号、准备启动抗体反应的早期阶段。"
      },
      {
        "type": "paragraph",
        "text": "这也正是寻找更具体遗传病因的意义所在。它让我们看见，抗体不足并不总是“最后工厂没有生产”；有时，问题更早就发生在 B 细胞没有顺利启动。"
      },
      {
        "type": "heading",
        "text": "CD20 与抗 CD20 药物：两个不同的故事"
      },
      {
        "type": "paragraph",
        "text": "CD20 这个名字有时会让患者想到利妥昔单抗等“抗 CD20”药物。"
      },
      {
        "type": "paragraph",
        "text": "这些药物会识别表达 CD20 的 B 细胞，因此可用于某些 B 细胞淋巴瘤、自身免疫疾病或免疫失调状态。它们造成的是治疗相关的、后天获得的 B 细胞变化。"
      },
      {
        "type": "paragraph",
        "text": "遗传性 CD20 缺陷则完全不同。它是由 MS4A1 基因的变异导致 B 细胞天生缺少或无法正常使用 CD20。"
      },
      {
        "type": "paragraph",
        "text": "两者都与 CD20 有关，却不能相互等同。对于有抗 CD20 药物使用史的人，低免疫球蛋白和感染风险也需要从继发性免疫缺陷的角度单独评估。"
      },
      {
        "type": "heading",
        "text": "遗传线索怎样理解"
      },
      {
        "type": "paragraph",
        "text": "CD20 缺陷通常为常染色体隐性遗传。"
      },
      {
        "type": "paragraph",
        "text": "患者往往从父母各继承一份功能明显受影响的 MS4A1 基因变异；父母各自只携带一份变异时，通常不会出现典型的抗体缺陷。"
      },
      {
        "type": "paragraph",
        "text": "遗传报告中出现 MS4A1/CD20 变异时，团队需要结合："
      },
      {
        "type": "paragraph",
        "text": "是否两份基因都受到影响；"
      },
      {
        "type": "paragraph",
        "text": "B 细胞表面 CD20 是否确实缺失；"
      },
      {
        "type": "paragraph",
        "text": "IgG、IgA、IgM 和疫苗抗体反应；"
      },
      {
        "type": "paragraph",
        "text": "记忆 B 细胞和浆细胞相关检查；"
      },
      {
        "type": "paragraph",
        "text": "变异是否属于致病或可能致病。"
      },
      {
        "type": "paragraph",
        "text": "意义未明变异不能单独用来确诊 CD20 缺陷。"
      },
      {
        "type": "heading",
        "text": "目前研究已经知道什么"
      },
      {
        "type": "paragraph",
        "text": "较可靠的结论是：CD20 与 B 细胞受体启动后的钙信号和抗体反应有关；CD20 缺陷可造成以低 IgG 和反复感染为主的遗传性抗体缺陷。IUIS 2024 分类将其列为以抗体缺陷为主的 IEI。 IUIS 2024 分类"
      },
      {
        "type": "paragraph",
        "text": "还有研究发现，在部分没有 MS4A1 基因缺陷的 CVID 患者中，CD20 与 B 细胞受体之间的信号重组也可能不够顺利。这提示 CD20 相关机制可能比罕见的遗传性 CD20 缺陷更广泛；但这并不等于所有 CVID 都是 CD20 问题。 CVID 中的 CD20/B 细胞信号研究"
      },
      {
        "type": "heading",
        "text": "仍不确定的问题"
      },
      {
        "type": "paragraph",
        "text": "CD20 缺陷极罕见，已知患者人数有限。"
      },
      {
        "type": "paragraph",
        "text": "目前还不清楚，不同 MS4A1 变异是否会带来不同的长期感染风险；为什么有些患者 IgM 和 IgA 相对保留；以及哪些检查最能预测患者是否会形成长期肺部结构改变。"
      },
      {
        "type": "paragraph",
        "text": "这些问题需要更长时间的患者随访。现阶段，CD20 的研究更适合帮助理解 B 细胞启动的重要性，而不是用一个基因结果预测完整的人生病程。"
      }
    ],
    "sources": [
      "Kuijpers TW, et al. CD20 deficiency in humans results in impaired T cell-independent antibody responses. Journal of Clinical Investigation. 2010.",
      "van de Ven AAJM, et al. Defective calcium signaling and disrupted CD20–B-cell receptor dissociation in CVID. Journal of Allergy and Clinical Immunology. 2012.",
      "Tangye SG, et al. Human inborn errors of immunity: 2024 update from the IUIS Expert Committee. Journal of Human Immunity. 2025."
    ]
  },
  {
    "slug": "tnfrsf13b-taci",
    "category": "gene",
    "title": "TNFRSF13B/TACI：B 细胞怎样学会长大，也学会不走错路",
    "excerpt": "B 细胞的一生，不只是“活下来”这么简单。",
    "blocks": [
      {
        "type": "paragraph",
        "text": "B 细胞的一生，不只是“活下来”这么简单。"
      },
      {
        "type": "paragraph",
        "text": "它需要在适当的时候成长、接受训练、转换成不同类型的抗体；也需要学会一件同样重要的事：不要攻击身体自己。"
      },
      {
        "type": "paragraph",
        "text": "TACI 就参与这两项任务。"
      },
      {
        "type": "paragraph",
        "text": "它位于 B 细胞表面，像一个接收成长信号的接口。一边帮助 B 细胞完成成熟和抗体类别转换，一边参与清理或约束那些可能走错方向的 B 细胞。"
      },
      {
        "type": "paragraph",
        "text": "因此，TACI 的故事特别能解释 CVID 中一个看似矛盾的现象：为什么有些患者既抗体不足，又会出现自身免疫或淋巴组织增生。"
      },
      {
        "type": "heading",
        "text": "B 细胞不只需要“活着”，还需要学会成熟"
      },
      {
        "type": "paragraph",
        "text": "年轻 B 细胞离开骨髓后，会在血液、脾脏和淋巴结中继续成长。"
      },
      {
        "type": "paragraph",
        "text": "在这段过程中，它们会收到两种重要信息："
      },
      {
        "type": "paragraph",
        "text": "“你可以继续活下去。”\n“你应该继续学习，成为能做出成熟抗体的 B 细胞。”"
      },
      {
        "type": "paragraph",
        "text": "BAFF 和 APRIL 是传递这类信息的两种分子。它们并不是抗体，也不是病原体；更像 B 细胞成长环境中送来的营养和训练通知。"
      },
      {
        "type": "paragraph",
        "text": "TACI 是接收 BAFF 和 APRIL 信号的受体之一。它让 B 细胞知道，何时该继续成熟，何时该进行抗体类别转换，何时该变成能够制造 IgG 或 IgA 的细胞。"
      },
      {
        "type": "heading",
        "text": "TACI 不只是成长按钮，也是安全检查员"
      },
      {
        "type": "paragraph",
        "text": "B 细胞在训练中需要不断尝试制造不同的抗体。"
      },
      {
        "type": "paragraph",
        "text": "这是建立高质量保护的必要过程，但也有风险：少数 B 细胞可能制造出会识别人体自身组织的抗体。正常情况下，免疫系统会把这些 B 细胞筛掉、限制住，或不让它们继续扩大。"
      },
      {
        "type": "paragraph",
        "text": "TACI 参与这一套安全机制。"
      },
      {
        "type": "paragraph",
        "text": "可以把它想成 B 细胞训练营里的一位老师。它会鼓励合适的学生继续进步，也会提醒那些可能违反规则的学生停下来。"
      },
      {
        "type": "paragraph",
        "text": "如果 TACI 功能明显不足，可能同时出现两类问题："
      },
      {
        "type": "paragraph",
        "text": "一类是成熟抗体不够，特别是 IgG、IgA 或抗体记忆不足；\n另一类是部分可能攻击自身的 B 细胞没有被充分控制。"
      },
      {
        "type": "paragraph",
        "text": "这也是为什么部分 TACI 相关患者除了反复感染，还可能有自身免疫性血细胞减少、甲状腺自身免疫、脾大、淋巴结增大或其他免疫失调表现。"
      },
      {
        "type": "paragraph",
        "text": "不是每个人都会出现这些问题，但这条机制让它们能够出现在同一个人身上。"
      },
      {
        "type": "heading",
        "text": "TACI 出问题后，患者可能经历什么"
      },
      {
        "type": "paragraph",
        "text": "TNFRSF13B 是编码 TACI 的基因。"
      },
      {
        "type": "paragraph",
        "text": "当 TACI 功能严重受到影响时，患者可能出现："
      },
      {
        "type": "paragraph",
        "text": "反复鼻窦炎、支气管炎或肺炎；"
      },
      {
        "type": "paragraph",
        "text": "IgG、IgA 或 IgM 中一种或多种偏低；"
      },
      {
        "type": "paragraph",
        "text": "疫苗抗体反应不够可靠；"
      },
      {
        "type": "paragraph",
        "text": "类别转换记忆 B 细胞偏少；"
      },
      {
        "type": "paragraph",
        "text": "自身免疫、脾大或淋巴组织增生。"
      },
      {
        "type": "paragraph",
        "text": "但 TACI 相关表现的差异非常大。"
      },
      {
        "type": "paragraph",
        "text": "有些人主要是 IgA 缺乏或反复感染；有些人符合 CVID 表现；也有人带有 TNFRSF13B 变异，却没有明显免疫疾病。正因为如此，TACI 是遗传解读中最容易被误读的基因之一。"
      },
      {
        "type": "heading",
        "text": "为什么“找到 TACI 变异”不一定就是答案"
      },
      {
        "type": "paragraph",
        "text": "有些遗传性免疫疾病中，找到一个明确致病变异，往往就能非常有力地解释疾病。"
      },
      {
        "type": "paragraph",
        "text": "TACI 不完全是这种情况。"
      },
      {
        "type": "paragraph",
        "text": "研究发现，部分健康人也携带一份 TNFRSF13B 变异。换句话说，只有一份 TACI 变异的人，不一定会出现抗体缺陷，也不一定就是 CVID 的唯一原因。"
      },
      {
        "type": "paragraph",
        "text": "这可能有几种解释："
      },
      {
        "type": "paragraph",
        "text": "这份变异本身影响较轻；"
      },
      {
        "type": "paragraph",
        "text": "另一份正常基因仍能承担部分工作；"
      },
      {
        "type": "paragraph",
        "text": "是否发病还受到其他基因、感染经历和环境因素影响；"
      },
      {
        "type": "paragraph",
        "text": "有些患者其实还有另一个更关键的遗传原因。"
      },
      {
        "type": "paragraph",
        "text": "因此，如果报告显示一份 TNFRSF13B 变异，最准确的理解往往不是“已经找到病因”，而是“发现了一条需要放回完整免疫图景中判断的线索”。"
      },
      {
        "type": "paragraph",
        "text": "近年的研究进一步支持这一点：单份 TNFRSF13B 变异在部分患者中可能更像风险修饰因素；若两份基因都出现明确有害变异，因果关系通常更强。 TNFRSF13B 变异再评估"
      },
      {
        "type": "heading",
        "text": "为什么它会表现得像 CVID"
      },
      {
        "type": "paragraph",
        "text": "CVID 的核心问题，是身体难以形成足量、有效、持久的抗体。"
      },
      {
        "type": "paragraph",
        "text": "TACI 正好参与 B 细胞成熟、抗体类别转换和记忆形成。因此，TACI 功能受影响时，患者可能有低免疫球蛋白、抗体反应不佳和反复感染，看起来很像 CVID。"
      },
      {
        "type": "paragraph",
        "text": "但 TACI 也参与免疫耐受，所以有些患者的表现不只停留在感染。对这部分人来说，CVID 可能只是疾病被发现时最先使用的临床名称，背后还需要继续理解 B 细胞成熟和免疫调节的关系。"
      },
      {
        "type": "heading",
        "text": "遗传线索怎样理解"
      },
      {
        "type": "paragraph",
        "text": "TNFRSF13B/TACI 相关疾病的遗传方式较复杂。"
      },
      {
        "type": "paragraph",
        "text": "已确认的情况可以是常染色体隐性遗传，也可以见于带有一份变异的患者。但“常染色体显性”在这里不能简单理解为“只要一份变异就一定患病”。"
      },
      {
        "type": "paragraph",
        "text": "关键概念是："
      },
      {
        "type": "paragraph",
        "text": "外显率不完全：携带变异的人不一定出现症状；"
      },
      {
        "type": "paragraph",
        "text": "可变表达：即使有症状，感染、自身免疫和抗体缺陷的程度也可能不同；"
      },
      {
        "type": "paragraph",
        "text": "遗传修饰：其他基因和环境可能共同决定最后会不会表现为疾病。"
      },
      {
        "type": "paragraph",
        "text": "因此，TACI 变异尤其需要结合免疫球蛋白、疫苗抗体反应、B 细胞亚群、家族史，以及是否还存在其他免疫相关基因变异一起解释。"
      },
      {
        "type": "paragraph",
        "text": "意义未明变异（VUS）更不能单独用于确诊。"
      },
      {
        "type": "heading",
        "text": "目前研究已经知道什么"
      },
      {
        "type": "paragraph",
        "text": "较可靠的结论是：TACI 接收 BAFF 和 APRIL 信号，参与 B 细胞成熟、抗体类别转换和免疫耐受；双等位基因的明确有害变异可以导致抗体缺陷。IUIS 2024 分类将 TACI 缺陷列在以抗体缺陷为主的 IEI 中。 IUIS 2024 分类"
      },
      {
        "type": "paragraph",
        "text": "较不确定、但正在被认真研究的问题是：单份 TNFRSF13B 变异究竟在多大程度上直接致病，又在多大程度上只是提高了发生抗体缺陷的可能性。"
      },
      {
        "type": "paragraph",
        "text": "这不是一个无关紧要的学术问题。它直接关系到患者和家属应如何理解遗传报告，也提醒我们不能把“发现变异”误写成“已经找到唯一病因”。"
      }
    ],
    "sources": [
      "Castigli E, et al. TACI is mutant in common variable immunodeficiency and IgA deficiency. Nature Genetics. 2005.",
      "Re-evaluation of the contribution of TNFRSF13B variants to antibody deficiency. Journal of Allergy and Clinical Immunology. 2025.",
      "Tangye SG, et al. Human inborn errors of immunity: 2024 update from the IUIS Expert Committee. Journal of Human Immunity. 2025."
    ]
  },
  {
    "slug": "tnfrsf13c-baffr",
    "category": "gene",
    "title": "TNFRSF13C/BAFF-R：年轻 B 细胞为什么需要一张“留下来”的通行证",
    "excerpt": "B 细胞并不是一出生就能制造抗体。",
    "blocks": [
      {
        "type": "paragraph",
        "text": "B 细胞并不是一出生就能制造抗体。"
      },
      {
        "type": "paragraph",
        "text": "它们先在骨髓中经历早期发育，再离开骨髓，进入血液、脾脏和淋巴结继续学习。在这段路上，很多年轻 B 细胞会自然离开队伍；只有一部分能得到合适信号、通过检查，成为成熟 B 细胞。"
      },
      {
        "type": "paragraph",
        "text": "BAFF-R 就是帮助年轻 B 细胞收到“你可以继续留下来、继续成长”的重要受体。"
      },
      {
        "type": "paragraph",
        "text": "如果它工作不足，B 细胞可能在真正成熟前就过早离场。最后留下来能参与抗体反应的 B 细胞变少，长期抗体保护也可能不足。"
      },
      {
        "type": "heading",
        "text": "B 细胞成长，并不是越多越好"
      },
      {
        "type": "paragraph",
        "text": "身体每天会产生许多年轻 B 细胞，但并不是每一个都应该留下。"
      },
      {
        "type": "paragraph",
        "text": "有些 B 细胞可能没有足够能力识别真正的病原体；还有一些可能太容易攻击身体自身。免疫系统需要允许合适的 B 细胞继续成长，也需要让不合适的 B 细胞退出。"
      },
      {
        "type": "paragraph",
        "text": "这是一种精细的平衡：留下得太少，抗体防御不足；留下得太多或筛选不够严格，又可能增加免疫失调的风险。"
      },
      {
        "type": "paragraph",
        "text": "BAFF 是 B 细胞成长环境中的一种重要信号。它像一份有限供应的营养和通行证，告诉合格的年轻 B 细胞：“你可以继续活下去，进入下一阶段。”"
      },
      {
        "type": "paragraph",
        "text": "BAFF-R，就是接收这份信号的主要接口。"
      },
      {
        "type": "heading",
        "text": "BAFF-R 在 B 细胞旅程中的位置"
      },
      {
        "type": "paragraph",
        "text": "年轻 B 细胞离开骨髓后，还不能立刻成为可靠的抗体工厂。"
      },
      {
        "type": "paragraph",
        "text": "它们需要经过一段过渡期，适应身体的免疫环境，接受更多筛选，然后才能成为成熟的初始 B 细胞。之后，它们才有机会在遇到感染时进入生发中心训练，形成记忆 B 细胞和浆细胞。"
      },
      {
        "type": "paragraph",
        "text": "BAFF-R 在这段过渡期特别重要。"
      },
      {
        "type": "paragraph",
        "text": "可以把年轻 B 细胞想成刚到新城市学习的学生。BAFF 是生活补助和入学许可；BAFF-R 是学生手中的接收证。没有这张证，学生很难留下来完成后面的课程。"
      },
      {
        "type": "paragraph",
        "text": "BAFF-R 与 TACI 都能接触 BAFF，但两者的工作重点不一样。BAFF-R 更像帮助年轻 B 细胞存活和成熟的“基础通行证”；TACI 更接近后续抗体类别转换和安全筛选中的调节者。"
      },
      {
        "type": "heading",
        "text": "如果 BAFF-R 功能不足"
      },
      {
        "type": "paragraph",
        "text": "当 BAFF-R 的功能明显受影响时，部分年轻 B 细胞可能无法在体内长期存活。"
      },
      {
        "type": "paragraph",
        "text": "患者血液中的成熟 B 细胞数量可能减少，尤其是已经完成较多训练、具有记忆功能的 B 细胞。由于抗体形成的“后备队”不足，患者可能出现："
      },
      {
        "type": "paragraph",
        "text": "IgG 偏低；"
      },
      {
        "type": "paragraph",
        "text": "IgM 也可能偏低；"
      },
      {
        "type": "paragraph",
        "text": "对感染或疫苗形成的抗体反应不够可靠；"
      },
      {
        "type": "paragraph",
        "text": "反复鼻窦炎、支气管炎或肺炎等感染。"
      },
      {
        "type": "paragraph",
        "text": "有些患者的症状相对轻，有些则更早或更明显地表现为抗体缺陷。原因可能与变异对 BAFF-R 功能影响的程度、其他遗传背景和感染经历有关。"
      },
      {
        "type": "paragraph",
        "text": "这也是为什么“同一个基因相关疾病”并不等于“每个人都会有同一份症状清单”。"
      },
      {
        "type": "heading",
        "text": "为什么它会表现得像 CVID"
      },
      {
        "type": "paragraph",
        "text": "CVID 的共同点是有效抗体不足。"
      },
      {
        "type": "paragraph",
        "text": "BAFF-R 功能缺失会让 B 细胞在成熟道路上少掉一部分能够进入后续抗体反应的成员。结果是，身体难以建立足量、持久的抗体保护，尤其是 IgG 和部分患者的 IgM。"
      },
      {
        "type": "paragraph",
        "text": "所以，BAFF-R 缺陷可以表现得像 CVID。"
      },
      {
        "type": "paragraph",
        "text": "从外表看，患者可能是反复呼吸道感染和低免疫球蛋白；从更深层看，问题发生在 B 细胞长大、存活和建立后备队的阶段。"
      },
      {
        "type": "paragraph",
        "text": "这是一种典型情况：临床表现与 CVID 相似，但能提供更具体的 B 细胞生物学解释。"
      },
      {
        "type": "heading",
        "text": "遗传线索怎样理解"
      },
      {
        "type": "paragraph",
        "text": "TNFRSF13C 是编码 BAFF-R 的基因。"
      },
      {
        "type": "paragraph",
        "text": "目前确认的 BAFF-R 缺陷通常为常染色体隐性遗传。患者往往从父母各继承一份功能明显受影响的变异；父母各自只有一份变异时，通常没有典型的抗体缺陷。"
      },
      {
        "type": "paragraph",
        "text": "遗传报告需要结合真实的免疫情况解读。团队通常会看："
      },
      {
        "type": "paragraph",
        "text": "是否两份 TNFRSF13C 基因都受到影响；"
      },
      {
        "type": "paragraph",
        "text": "成熟 B 细胞和记忆 B 细胞的数量；"
      },
      {
        "type": "paragraph",
        "text": "IgG、IgM、IgA 以及疫苗抗体反应；"
      },
      {
        "type": "paragraph",
        "text": "变异是否已被归类为致病或可能致病；"
      },
      {
        "type": "paragraph",
        "text": "家族成员是否有相似感染或免疫表现。"
      },
      {
        "type": "paragraph",
        "text": "如果报告是意义未明变异（VUS），它不能单独成为 BAFF-R 缺陷的诊断依据。"
      },
      {
        "type": "heading",
        "text": "目前研究已经知道什么"
      },
      {
        "type": "paragraph",
        "text": "较可靠的研究结论是：BAFF-R 是年轻 B 细胞获得生存和成熟信号的重要受体；它功能缺失可造成以低 IgG、低 IgM 和反复感染为主的遗传性抗体缺陷。IUIS 2024 分类将 BAFF-R 缺陷列入以抗体缺陷为主的 IEI。 IUIS 2024 分类"
      },
      {
        "type": "paragraph",
        "text": "研究也提示，BAFF 本身和其他 BAFF/APRIL 相关信号可能在不同 CVID 患者中发生变化。但这不表示测量一次 BAFF 数值，就能解释某个患者的疾病，更不表示所有 CVID 都是 BAFF-R 问题。"
      },
      {
        "type": "heading",
        "text": "仍不确定的问题"
      },
      {
        "type": "paragraph",
        "text": "BAFF-R 缺陷已知患者非常少。"
      },
      {
        "type": "paragraph",
        "text": "研究者仍在了解：为什么一些患者成熟 B 细胞减少得更多；为什么有些人感染较轻；BAFF-R 以外的其他 B 细胞生存信号能否在某些患者中部分补偿；以及不同变异是否带来不同的长期风险。"
      },
      {
        "type": "paragraph",
        "text": "这些问题说明，BAFF-R 是理解 B 细胞成长的一条重要线索，但不是预测个人病程的水晶球。"
      }
    ],
    "sources": [
      "Tangye SG, et al. Human inborn errors of immunity: 2024 update from the IUIS Expert Committee. Journal of Human Immunity. 2025.",
      "Bogaert DJA, et al. Genes associated with common variable immunodeficiency. Journal of Medical Genetics. 2016.",
      "Bonilla FA, et al. International Consensus Document: Common Variable Immunodeficiency Disorders. Journal of Allergy and Clinical Immunology. 2016."
    ]
  },
  {
    "slug": "icos",
    "category": "gene",
    "title": "ICOS：让 T 细胞找到 B 细胞，并说出那句“继续训练”",
    "excerpt": "B 细胞能不能做出好抗体，并不只取决于 B 细胞自己。",
    "blocks": [
      {
        "type": "paragraph",
        "text": "B 细胞能不能做出好抗体，并不只取决于 B 细胞自己。"
      },
      {
        "type": "paragraph",
        "text": "它需要另一位重要伙伴：CD4 T 细胞。T 细胞不会替 B 细胞制造抗体，但它能帮助 B 细胞确认目标、进入训练、形成记忆。没有这种帮助，B 细胞可能只能完成感染早期的一部分工作，很难留下长期、精确的抗体保护。"
      },
      {
        "type": "paragraph",
        "text": "ICOS 就是让这位 T 细胞伙伴成为“好教练”的重要分子。"
      },
      {
        "type": "heading",
        "text": "B 细胞训练营里，为什么需要教练"
      },
      {
        "type": "paragraph",
        "text": "在一次感染后，少数识别到病原体的 B 细胞会进入淋巴结或脾脏中的生发中心。"
      },
      {
        "type": "paragraph",
        "text": "生发中心像一个抗体训练营。B 细胞在这里不断练习、筛选，努力制造更能抓住病原体的抗体。经过训练后，它们才可能成为记忆 B 细胞或浆细胞。"
      },
      {
        "type": "paragraph",
        "text": "但 B 细胞不能独自决定自己是否训练合格。"
      },
      {
        "type": "paragraph",
        "text": "它需要一类特别的 CD4 T 细胞帮助。这类 T 细胞会来到 B 细胞聚集的区域，检查 B 细胞展示的病原体信息，并给予关键的协作信号。"
      },
      {
        "type": "paragraph",
        "text": "可以把它想成考试时的指导老师。B 细胞做题，老师不会替它答题，却会判断它有没有抓住重点、是否值得进入下一阶段。"
      },
      {
        "type": "heading",
        "text": "ICOS 让 T 细胞成为这位教练"
      },
      {
        "type": "paragraph",
        "text": "ICOS 是活化 T 细胞表面的一个分子。"
      },
      {
        "type": "paragraph",
        "text": "当 T 细胞需要更深入地参与免疫反应时，ICOS 帮助它与其他免疫细胞建立联系，也帮助一部分 T 细胞走向生发中心附近，成为擅长帮助 B 细胞的滤泡辅助性 T 细胞。"
      },
      {
        "type": "paragraph",
        "text": "这听起来很专业，但可以把它理解成：ICOS 帮助 T 细胞找到正确的教室，并具备指导 B 细胞的能力。"
      },
      {
        "type": "paragraph",
        "text": "有了 ICOS，T 细胞更能帮助 B 细胞："
      },
      {
        "type": "paragraph",
        "text": "继续在生发中心中训练；"
      },
      {
        "type": "paragraph",
        "text": "完成抗体类别转换；"
      },
      {
        "type": "paragraph",
        "text": "形成记忆 B 细胞；"
      },
      {
        "type": "paragraph",
        "text": "变成稳定制造抗体的浆细胞。"
      },
      {
        "type": "paragraph",
        "text": "因此，ICOS 虽然主要出现在 T 细胞上，却会深深影响最后能不能形成 IgG、IgA 和长期抗体记忆。"
      },
      {
        "type": "heading",
        "text": "如果 ICOS 功能不足"
      },
      {
        "type": "paragraph",
        "text": "当 ICOS 功能明显不足时，T 细胞给 B 细胞的帮助会减少。"
      },
      {
        "type": "paragraph",
        "text": "B 细胞并不是完全没有反应，但它们较难完成生发中心训练。于是，记忆 B 细胞和类别转换后的 B 细胞可能减少，抗体保护也会不足。"
      },
      {
        "type": "paragraph",
        "text": "患者可能出现："
      },
      {
        "type": "paragraph",
        "text": "IgG 偏低，常伴 IgA 偏低；"
      },
      {
        "type": "paragraph",
        "text": "对感染或疫苗形成的抗体记忆不足；"
      },
      {
        "type": "paragraph",
        "text": "鼻窦炎、支气管炎、肺炎等反复呼吸道感染；"
      },
      {
        "type": "paragraph",
        "text": "脾大、淋巴结增大或肠道淋巴组织增生；"
      },
      {
        "type": "paragraph",
        "text": "部分患者出现自身免疫性血细胞减少、肠病或其他炎症表现。"
      },
      {
        "type": "paragraph",
        "text": "早期研究主要把 ICOS 缺陷看作一种表现与 CVID 相似、以抗体不足为主的遗传病。随着患者随访增加，研究者发现有些患者还可能更容易出现病毒感染、机会性感染或肿瘤相关问题。"
      },
      {
        "type": "paragraph",
        "text": "这说明 ICOS 的作用可能比“帮助 B 细胞做抗体”更广。它也提醒我们：有些最初看起来像 CVID 的疾病，后来会发现还涉及更完整的 T、B 细胞合作。"
      },
      {
        "type": "heading",
        "text": "为什么它会表现得像 CVID"
      },
      {
        "type": "paragraph",
        "text": "从患者经历看，ICOS 缺陷很容易呈现 CVID 的样子：反复呼吸道感染、低免疫球蛋白、抗体反应不佳、记忆 B 细胞不足。"
      },
      {
        "type": "paragraph",
        "text": "但如果把镜头拉远，就会发现 B 细胞本身并不一定是最早出问题的地方。问题可能始于 T 细胞无法成为一位足够有效的教练。"
      },
      {
        "type": "paragraph",
        "text": "这正是 ICOS 对 CVID 研究的价值。它帮助我们理解：有时 B 细胞做不出抗体，不是因为它不会做，而是因为它没有得到完成训练所需要的帮助。"
      },
      {
        "type": "heading",
        "text": "遗传线索怎样理解"
      },
      {
        "type": "paragraph",
        "text": "ICOS 缺陷通常为常染色体隐性遗传。"
      },
      {
        "type": "paragraph",
        "text": "患者通常从父母各继承一份功能明显受影响的 ICOS 变异。父母各自携带一份变异时，通常没有典型的免疫缺陷表现。"
      },
      {
        "type": "paragraph",
        "text": "有一个容易被忽略的事实：ICOS 相关疾病不一定只在儿童期被发现。早期研究中，部分患者到成年后才因反复感染和低免疫球蛋白被确诊。"
      },
      {
        "type": "paragraph",
        "text": "因此，成年后出现的 CVID 表现并不能排除遗传性原因。"
      },
      {
        "type": "paragraph",
        "text": "若遗传报告发现 ICOS 变异，团队会结合："
      },
      {
        "type": "paragraph",
        "text": "是否两份 ICOS 基因都受到影响；"
      },
      {
        "type": "paragraph",
        "text": "活化 T 细胞表面的 ICOS 是否缺失；"
      },
      {
        "type": "paragraph",
        "text": "记忆 B 细胞和类别转换 B 细胞的情况；"
      },
      {
        "type": "paragraph",
        "text": "是否有感染之外的炎症、肠病或淋巴组织表现；"
      },
      {
        "type": "paragraph",
        "text": "变异是否已有致病或可能致病证据。"
      },
      {
        "type": "paragraph",
        "text": "意义未明变异（VUS）不能单独解释疾病。"
      },
      {
        "type": "heading",
        "text": "目前研究已经知道什么"
      },
      {
        "type": "paragraph",
        "text": "较可靠的研究显示，ICOS 对形成能够帮助 B 细胞的 T 细胞很重要；人类 ICOS 缺陷可导致记忆 B 细胞明显减少、低免疫球蛋白，及与 CVID 相似的临床表现。 ICOS 缺陷的早期人类研究"
      },
      {
        "type": "paragraph",
        "text": "长期随访也显示，IC​​OS 缺陷的表现比最初预期更广：除抗体不足外，部分患者还出现自身免疫、肠病、淋巴组织增生、病毒或机会性感染。 15 名患者的长期随访"
      },
      {
        "type": "paragraph",
        "text": "不过，已报告患者总数仍很少。不同变异是否会带来不同风险、哪些患者会出现更复杂的炎症表现、怎样预测长期结局，仍没有足够答案。"
      }
    ],
    "sources": [
      "Grimbacher B, et al. Homozygous loss of ICOS is associated with adult-onset common variable immunodeficiency. Nature Immunology. 2003.",
      "Warnatz K, et al. Human ICOS deficiency abrogates the germinal center reaction. Blood. 2006.",
      "Fekrvand S, et al. Fourteen years after discovery: clinical follow-up on 15 patients with ICOS deficiency. Journal of Clinical Immunology. 2017."
    ]
  },
  {
    "slug": "il21-il21r",
    "category": "gene",
    "title": "IL21/IL21R：B 细胞训练营里的“毕业信号”",
    "excerpt": "B 细胞进入生发中心后，并不会自动变成记忆 B 细胞或浆细胞。",
    "blocks": [
      {
        "type": "paragraph",
        "text": "B 细胞进入生发中心后，并不会自动变成记忆 B 细胞或浆细胞。"
      },
      {
        "type": "paragraph",
        "text": "它们需要经过一轮又一轮训练：学会更准确地识别病原体，学会从 IgM 转换为 IgG 或 IgA，也学会在感染过去后留下记忆。"
      },
      {
        "type": "paragraph",
        "text": "在这段训练快结束时，B 细胞还需要听到一句很关键的话："
      },
      {
        "type": "paragraph",
        "text": "“你已经准备好了，可以成为长期保护的一部分。”"
      },
      {
        "type": "paragraph",
        "text": "IL-21 就像这句话。IL-21R 则是听到这句话的接收器。"
      },
      {
        "type": "heading",
        "text": "一条从 T 细胞发出的重要信息"
      },
      {
        "type": "paragraph",
        "text": "IL-21 是一种由 T 细胞发出的信号分子。它最重要的来源之一，是淋巴结生发中心中的滤泡辅助性 T 细胞。"
      },
      {
        "type": "paragraph",
        "text": "前一篇的 ICOS，帮助 T 细胞成为能够指导 B 细胞的教练；IL-21 则像这位教练在训练过程中说出的关键指令。"
      },
      {
        "type": "paragraph",
        "text": "B 细胞表面有 IL-21R，也就是 IL-21 受体。当 IL-21 与 IL-21R 结合，B 细胞会收到继续成熟、增殖、转换抗体类别并成为浆细胞的信号。"
      },
      {
        "type": "paragraph",
        "text": "可以把它理解为："
      },
      {
        "type": "paragraph",
        "text": "IL-21：教练发出的“毕业通知”；"
      },
      {
        "type": "paragraph",
        "text": "IL-21R：B 细胞接收通知的天线。"
      },
      {
        "type": "paragraph",
        "text": "两者缺一不可。"
      },
      {
        "type": "heading",
        "text": "为什么 B 细胞特别需要这句“毕业通知”"
      },
      {
        "type": "paragraph",
        "text": "感染早期，B 细胞可以较快制造 IgM。可如果身体想获得更贴合病原体、更持久的保护，就需要形成 IgG、IgA、记忆 B 细胞和长寿命浆细胞。"
      },
      {
        "type": "paragraph",
        "text": "这些成熟阶段很依赖生发中心训练。"
      },
      {
        "type": "paragraph",
        "text": "IL-21 帮助 B 细胞在训练营中继续增殖，接受筛选，完成抗体类别转换，并走向最终的两条长期道路："
      },
      {
        "type": "paragraph",
        "text": "一条是成为记忆 B 细胞，把这次感染记下来；\n另一条是成为浆细胞，持续制造抗体。"
      },
      {
        "type": "paragraph",
        "text": "如果 IL-21 信号不足，B 细胞可能已经进入训练营，却难以顺利毕业。"
      },
      {
        "type": "heading",
        "text": "IL-21 或 IL-21R 出问题后，会发生什么"
      },
      {
        "type": "paragraph",
        "text": "如果 IL21 基因本身，或 IL21R 基因中的两份拷贝都存在明显影响功能的变异，IL-21 信号就可能无法正常传递。"
      },
      {
        "type": "paragraph",
        "text": "B 细胞会因此较难形成高质量抗体记忆。患者可能出现："
      },
      {
        "type": "paragraph",
        "text": "IgG 偏低，也可能伴 IgA 或 IgM 异常；"
      },
      {
        "type": "paragraph",
        "text": "类别转换记忆 B 细胞减少；"
      },
      {
        "type": "paragraph",
        "text": "对感染或疫苗的抗体反应不足；"
      },
      {
        "type": "paragraph",
        "text": "反复鼻窦炎、支气管炎、肺炎等呼吸道感染。"
      },
      {
        "type": "paragraph",
        "text": "但 IL-21 的作用不只在 B 细胞。"
      },
      {
        "type": "paragraph",
        "text": "它也参与 T 细胞和自然杀伤细胞的功能。因此，IL-21 或 IL-21R 缺陷有时比典型 CVID 更复杂：部分患者可有真菌、病毒或机会性感染，或出现明显肠道、肝脏问题。"
      },
      {
        "type": "heading",
        "text": "IL-21 缺陷和 IL-21R 缺陷，有相似也有不同"
      },
      {
        "type": "paragraph",
        "text": "两者都可能让 B 细胞无法顺利完成抗体训练，因此都可表现得像 CVID。"
      },
      {
        "type": "paragraph",
        "text": "但现有报道中，两者又有一些不同线索。"
      },
      {
        "type": "paragraph",
        "text": "IL-21 缺陷患者可出现非常早发的肠道炎症、慢性腹泻或类似炎症性肠病的表现，同时伴反复呼吸道感染和抗体不足。"
      },
      {
        "type": "paragraph",
        "text": "IL-21R 缺陷患者除反复呼吸道感染外，曾较多报告隐孢子虫感染。隐孢子虫是一种可影响肠道和胆道的寄生虫；在部分患者中，它可能与长期胆管炎、肝病有关。"
      },
      {
        "type": "paragraph",
        "text": "这并不代表每个 IL-21R 缺陷患者都会感染隐孢子虫，也不代表 IL-21 缺陷一定会发生肠炎。它只是提醒人们：IL-21 信号影响的不只是“做不做抗体”，还涉及更广的免疫合作。"
      },
      {
        "type": "heading",
        "text": "为什么它会表现得像 CVID"
      },
      {
        "type": "paragraph",
        "text": "如果只看低 IgG、记忆 B 细胞不足和反复呼吸道感染，IL-21 或 IL-21R 缺陷很像 CVID。"
      },
      {
        "type": "paragraph",
        "text": "但如果患者在儿童期很早发病，或同时有严重肠病、机会性感染、隐孢子虫感染、慢性肝胆问题等，医生可能会进一步考虑：这是否不只是典型 CVID，而是一个影响 T、B 细胞合作的更具体 IEI。"
      },
      {
        "type": "paragraph",
        "text": "这不是在给疾病贴“更严重”的标签，而是帮助团队看见哪些线索需要被更认真地评估。"
      },
      {
        "type": "heading",
        "text": "遗传线索怎样理解"
      },
      {
        "type": "paragraph",
        "text": "IL21 缺陷和 IL21R 缺陷通常都是常染色体隐性遗传。"
      },
      {
        "type": "paragraph",
        "text": "患者往往从父母各继承一份功能明显受影响的变异。父母各自携带一份变异时，通常没有典型疾病表现。"
      },
      {
        "type": "paragraph",
        "text": "遗传结果需要与临床和免疫检查共同解释。团队会关注："
      },
      {
        "type": "paragraph",
        "text": "是否两份 IL21 或 IL21R 基因都受到影响；"
      },
      {
        "type": "paragraph",
        "text": "记忆 B 细胞和类别转换 B 细胞的情况；"
      },
      {
        "type": "paragraph",
        "text": "T 细胞、自然杀伤细胞及其功能是否存在线索；"
      },
      {
        "type": "paragraph",
        "text": "是否有肠道、肝胆或机会性感染表现；"
      },
      {
        "type": "paragraph",
        "text": "变异是否有可靠的致病证据。"
      },
      {
        "type": "paragraph",
        "text": "意义未明变异（VUS）不能单独作为确诊依据。"
      },
      {
        "type": "heading",
        "text": "目前研究已经知道什么"
      },
      {
        "type": "paragraph",
        "text": "细胞、动物和人类遗传研究一致支持：IL-21 是生发中心反应、抗体类别转换、浆细胞形成和长期抗体记忆的重要信号。 IL-21 与生发中心反应综述"
      },
      {
        "type": "paragraph",
        "text": "人类病例研究也支持，IL-21 或 IL-21R 的双等位基因功能缺失可造成低免疫球蛋白、记忆 B 细胞不足和反复感染；IL-21R 缺陷患者中，隐孢子虫相关胆管炎和肝病是需要认识的代表性线索。 IL-21R 缺陷研究"
      },
      {
        "type": "heading",
        "text": "仍不确定的问题"
      },
      {
        "type": "paragraph",
        "text": "IL-21 和 IL-21R 缺陷都非常罕见。"
      },
      {
        "type": "paragraph",
        "text": "研究者仍在了解，为什么一些患者以抗体不足为主，另一些却有严重肠病、肝胆问题或机会性感染；不同变异如何影响 T、B、自然杀伤细胞；以及哪些早期检查最能预测长期器官风险。"
      },
      {
        "type": "paragraph",
        "text": "目前能确定的是，IL-21 信号是 B 细胞抗体训练的重要一步；仍无法确定的是，每位患者的疾病会以怎样的方式展开。"
      }
    ],
    "sources": [
      "Kotlarz D, et al. Loss-of-function mutations in the IL-21 receptor gene cause a primary immunodeficiency syndrome. Journal of Experimental Medicine. 2013.",
      "Erman B, et al. Early-onset inflammatory bowel disease and CVID-like disease caused by IL-21 deficiency. Journal of Allergy and Clinical Immunology. 2015.",
      "Hasegawa H, et al. Genomic spectrum and phenotypic heterogeneity of human IL-21 receptor deficiency. Journal of Clinical Immunology. 2021."
    ]
  },
  {
    "slug": "nfkb1",
    "category": "gene",
    "title": "NFKB1：把免疫信号翻译成行动的“内部信使”",
    "excerpt": "B 细胞表面每天都会收到很多信息。",
    "blocks": [
      {
        "type": "paragraph",
        "text": "B 细胞表面每天都会收到很多信息。"
      },
      {
        "type": "paragraph",
        "text": "有的是病原体带来的警报，有的是其他免疫细胞给出的协作信号，有的是告诉它“继续成熟”或“该停下来”的提醒。可这些信息如果只停留在细胞表面，B 细胞什么也做不了。"
      },
      {
        "type": "paragraph",
        "text": "它需要有人把消息送进细胞核，变成真正的行动指令。"
      },
      {
        "type": "paragraph",
        "text": "NFKB1 就是这类内部信使中的重要成员。"
      },
      {
        "type": "paragraph",
        "text": "它不仅影响 B 细胞能不能形成抗体，也参与许多免疫细胞如何面对感染、炎症和自身组织。因此，NFKB1 相关疾病常常不只是“抗体低”这么简单。"
      },
      {
        "type": "heading",
        "text": "细胞里的信息，怎样变成行动"
      },
      {
        "type": "paragraph",
        "text": "可以把免疫细胞想成一栋办公楼。"
      },
      {
        "type": "paragraph",
        "text": "细胞表面的受体像前台，负责接收外界消息；细胞核像总办公室，决定接下来要生产什么、派出谁、什么时候停止工作。"
      },
      {
        "type": "paragraph",
        "text": "NFKB1 像负责传达紧急文件的信使。当 B 细胞收到感染或成长信号后，NFKB1 参与把这些信息带到细胞核，帮助启动与存活、成熟、抗体形成和炎症调节有关的基因。"
      },
      {
        "type": "paragraph",
        "text": "它不是只有“打开”或“关闭”两种状态。太弱、太晚、太久，都会让免疫系统失去平衡。"
      },
      {
        "type": "heading",
        "text": "NFKB1 对 B 细胞意味着什么"
      },
      {
        "type": "paragraph",
        "text": "B 细胞要成为记忆 B 细胞或浆细胞，需要经历一连串成熟步骤。"
      },
      {
        "type": "paragraph",
        "text": "NFKB1 参与这些步骤，因此它功能不足时，B 细胞可能仍然在血液中，却较难走到最后。尤其是，部分患者的类别转换记忆 B 细胞会减少，意味着能形成长期 IgG 或 IgA 抗体记忆的 B 细胞不够。"
      },
      {
        "type": "paragraph",
        "text": "这会带来熟悉的 CVID 表现："
      },
      {
        "type": "paragraph",
        "text": "IgG 偏低，也可能伴 IgA 或 IgM 异常；"
      },
      {
        "type": "paragraph",
        "text": "对感染或疫苗的抗体反应不够持久；"
      },
      {
        "type": "paragraph",
        "text": "反复鼻窦炎、支气管炎、肺炎等呼吸道感染；"
      },
      {
        "type": "paragraph",
        "text": "随时间逐渐显现的抗体不足。"
      },
      {
        "type": "paragraph",
        "text": "这里的“逐渐”很重要。有些人幼年没有明显问题，成年后才开始反复感染或发现低免疫球蛋白。NFKB1 相关疾病不一定从出生起就有很明显的表现。"
      },
      {
        "type": "heading",
        "text": "为什么有些患者还会有自身免疫和炎症"
      },
      {
        "type": "paragraph",
        "text": "NFKB1 不只在 B 细胞中工作。"
      },
      {
        "type": "paragraph",
        "text": "它也参与 T 细胞、吞噬细胞和其他免疫细胞对感染和炎症的反应。因此，当 NFKB1 功能不足时，问题可能不仅是“信号不够”，也可能是“不同细胞之间的协调不够稳定”。"
      },
      {
        "type": "paragraph",
        "text": "部分患者除了反复感染，还会出现："
      },
      {
        "type": "paragraph",
        "text": "自身免疫性血小板减少、溶血性贫血或其他血细胞减少；"
      },
      {
        "type": "paragraph",
        "text": "脾大、淋巴结增大或异常淋巴组织增生；"
      },
      {
        "type": "paragraph",
        "text": "肠道感染、肠病或炎症；"
      },
      {
        "type": "paragraph",
        "text": "支气管扩张等慢性肺部问题；"
      },
      {
        "type": "paragraph",
        "text": "少数患者的 EB 病毒相关淋巴细胞增生或其他较复杂表现。"
      },
      {
        "type": "paragraph",
        "text": "这不是说每位 NFKB1 患者都会经历这些问题。更准确的说法是：NFKB1 相关疾病的范围很宽，抗体不足只是其中最常见的入口。"
      },
      {
        "type": "heading",
        "text": "为什么它会表现得像 CVID"
      },
      {
        "type": "paragraph",
        "text": "CVID 患者常被发现有低免疫球蛋白、抗体记忆不足和反复感染。"
      },
      {
        "type": "paragraph",
        "text": "NFKB1 功能不足可以造成这一整组表现，因此它被认为是目前已知、较常见的单基因 CVID 原因之一。在一项以欧洲患者为主的研究中，明确有害的 NFKB1 变异解释了该队列约 4% 的 CVID 病例。 欧洲队列研究"
      },
      {
        "type": "paragraph",
        "text": "但这不等于所有 CVID 都应归因于 NFKB1，也不等于每一个 NFKB1 变异都会造成 CVID。遗传结果需要经过严格判断。"
      },
      {
        "type": "paragraph",
        "text": "NFKB1 的价值在于告诉我们：有些患者的抗体不足，根源不只在 B 细胞本身，而在于细胞内部的整套信息传递能力出了问题。"
      },
      {
        "type": "heading",
        "text": "遗传线索：一份变异，也可能带来疾病"
      },
      {
        "type": "paragraph",
        "text": "NFKB1 相关疾病通常为常染色体显性遗传。"
      },
      {
        "type": "paragraph",
        "text": "这意味着，一份功能明显受影响的 NFKB1 基因就可能增加患病风险。但这并不意味着每一位携带者都会表现出相同疾病。"
      },
      {
        "type": "paragraph",
        "text": "NFKB1 很典型地具有："
      },
      {
        "type": "paragraph",
        "text": "不完全外显率：携带变异的人可能没有明显症状；"
      },
      {
        "type": "paragraph",
        "text": "可变表达：同一个家族中，有人只是轻度低免疫球蛋白，有人却有感染、自身免疫或淋巴组织问题；"
      },
      {
        "type": "paragraph",
        "text": "年龄相关性：有些表现会随年龄和免疫经历逐渐出现。"
      },
      {
        "type": "paragraph",
        "text": "因此，发现一份 NFKB1 变异后，不能只问“有没有这个变异”，还要问“它是否真的影响蛋白功能”“患者的免疫表现是否符合”“家族中是否与疾病一起出现”。"
      },
      {
        "type": "paragraph",
        "text": "意义未明变异（VUS）不能单独诊断 NFKB1 相关疾病。"
      },
      {
        "type": "heading",
        "text": "目前研究已经知道什么"
      },
      {
        "type": "paragraph",
        "text": "多项研究支持，NFKB1 功能缺失可造成以抗体不足为核心、同时可能伴自身免疫、炎症和淋巴组织增生的 IEI。"
      },
      {
        "type": "paragraph",
        "text": "在一项国际合作研究中，研究者评估了 157 名携带明确致病 NFKB1 变异的患者。大多数有低免疫球蛋白和呼吸道感染，但表现的种类和严重程度差异很大；研究也观察到年龄相关的病情变化。 157 人国际队列"
      },
      {
        "type": "paragraph",
        "text": "这类研究的重要意义，不是提供某个人的风险百分比，而是确认：NFKB1 相关疾病是真实存在、跨度很大的疾病谱，而不是只有一种固定的 CVID 模板。"
      },
      {
        "type": "heading",
        "text": "仍不确定的问题"
      },
      {
        "type": "paragraph",
        "text": "研究者还在寻找答案："
      },
      {
        "type": "paragraph",
        "text": "为什么同一变异在家族中会有如此不同的表现；"
      },
      {
        "type": "paragraph",
        "text": "哪些 B 细胞、炎症或遗传线索能预测自身免疫和肺部风险；"
      },
      {
        "type": "paragraph",
        "text": "为什么有些患者成年后才显现明显抗体缺陷；"
      },
      {
        "type": "paragraph",
        "text": "哪些 NFKB1 变异是真正有害的，哪些只是没有临床意义的遗传差异。"
      },
      {
        "type": "paragraph",
        "text": "NFKB1 是目前研究较多的 CVID 相关基因之一，但它仍不能像一本说明书那样预测每个人的未来。"
      }
    ],
    "sources": [
      "Fliegauf M, et al. Loss-of-function NFKB1 variants are the most common monogenic cause of CVID in Europeans. Journal of Allergy and Clinical Immunology. 2018.",
      "Lorenzini T, et al. Clinical and immunologic phenotype of 157 individuals with heterozygous NFKB1 mutations. Journal of Allergy and Clinical Immunology. 2020.",
      "Tuijnenburg P, et al. NFKB1 variants shape CVID clinical manifestations. Annals of Allergy, Asthma & Immunology. 2025."
    ]
  },
  {
    "slug": "stat3-gof",
    "category": "gene",
    "title": "STAT3 gain-of-function：当免疫系统的“继续执行”指令太强",
    "excerpt": "免疫系统需要迅速反应，也需要知道什么时候停下。",
    "blocks": [
      {
        "type": "paragraph",
        "text": "免疫系统需要迅速反应，也需要知道什么时候停下。"
      },
      {
        "type": "paragraph",
        "text": "STAT3 是免疫细胞内部的一条信号路线。它会接收来自外界的很多信息，例如感染、炎症和组织修复的提示，再把这些信息转成细胞的行动安排。"
      },
      {
        "type": "paragraph",
        "text": "正常情况下，STAT3 的信号应该在合适的时候打开、合适的时候减弱。"
      },
      {
        "type": "paragraph",
        "text": "但在 STAT3 gain-of-function（STAT3 GOF）疾病中，某些变异会让这条“继续执行”的指令过强，或持续得太久。它不是免疫系统更有力，而是免疫反应更难恢复平衡。"
      },
      {
        "type": "heading",
        "text": "为什么“太活跃”也会带来免疫缺陷"
      },
      {
        "type": "paragraph",
        "text": "这听起来很矛盾：如果免疫信号更强，为什么患者还会感染？"
      },
      {
        "type": "paragraph",
        "text": "因为免疫系统不是一支只需要加速的队伍。长期过度活跃会让不同免疫细胞的分工失调。有些细胞被持续驱动，有些调节性细胞无法正常发挥作用；B 细胞形成抗体和记忆的过程也可能受到影响。"
      },
      {
        "type": "paragraph",
        "text": "于是，患者可能同时出现两种看似相反的事情："
      },
      {
        "type": "paragraph",
        "text": "一边是自身免疫、炎症、淋巴细胞增生；\n另一边是低免疫球蛋白、抗体反应不足和反复感染。"
      },
      {
        "type": "paragraph",
        "text": "这不是两种独立疾病，而可能是同一条过强信号在不同免疫环节留下的痕迹。"
      },
      {
        "type": "heading",
        "text": "患者可能经历什么"
      },
      {
        "type": "paragraph",
        "text": "STAT3 GOF 常在儿童期出现线索，但也有患者在更晚年龄才获得诊断。"
      },
      {
        "type": "paragraph",
        "text": "较有代表性的表现包括："
      },
      {
        "type": "paragraph",
        "text": "自身免疫性血小板减少、贫血或多种血细胞减少；"
      },
      {
        "type": "paragraph",
        "text": "淋巴结增大、脾大，或其他良性淋巴细胞增生；"
      },
      {
        "type": "paragraph",
        "text": "慢性腹泻、肠炎、吸收不良；"
      },
      {
        "type": "paragraph",
        "text": "甲状腺、血糖、生长或其他内分泌问题；"
      },
      {
        "type": "paragraph",
        "text": "皮肤、关节、肺、肝脏、肾脏或神经系统的免疫相关表现；"
      },
      {
        "type": "paragraph",
        "text": "反复感染、低 IgG 或其他抗体异常。"
      },
      {
        "type": "paragraph",
        "text": "在一项国际自然病程研究中，191 名患者都存在不同形式的免疫失调；超过一半有体液免疫异常，包括低免疫球蛋白或抗体功能问题。 STAT3 GOF 国际队列"
      },
      {
        "type": "paragraph",
        "text": "这不表示每个患者都会累及多个器官。它说明 STAT3 GOF 的范围很宽，不能只用某一项化验或某一个器官问题来概括。"
      },
      {
        "type": "heading",
        "text": "从基因机制理解 CVID"
      },
      {
        "type": "paragraph",
        "text": "有些 STAT3 GOF 患者最初被诊断为 CVID，因为他们有低 IgG、反复感染、疫苗抗体反应不佳或记忆 B 细胞不足。"
      },
      {
        "type": "paragraph",
        "text": "遗传诊断进一步解释了：抗体不足不是孤立发生的，而是更广泛的免疫调节失衡的一部分。"
      },
      {
        "type": "paragraph",
        "text": "因此，STAT3 GOF 并不是“抗体少所以免疫低”这么简单；它更像免疫系统的不同部门收到了过强、过久的工作指令，最后既影响抗体生产，也造成炎症和自身免疫。"
      },
      {
        "type": "heading",
        "text": "遗传线索怎样理解"
      },
      {
        "type": "paragraph",
        "text": "STAT3 GOF 通常为常染色体显性遗传。"
      },
      {
        "type": "paragraph",
        "text": "患者只需一份会让 STAT3 信号增强的致病变异，就可能出现疾病。许多患者的变异是新发生的，也就是说家族中未必有人有类似病史。"
      },
      {
        "type": "paragraph",
        "text": "这里必须区分两种完全不同的情况："
      },
      {
        "type": "paragraph",
        "text": "STAT3 gain-of-function：信号过强，可造成免疫失调；"
      },
      {
        "type": "paragraph",
        "text": "STAT3 loss-of-function：信号不足，是另一类不同疾病。"
      },
      {
        "type": "paragraph",
        "text": "所以，遗传报告不能只写“STAT3 变异”就结束。关键是变异究竟让蛋白功能增强、减弱，还是目前仍无法判断。VUS 也不能用于确认 STAT3 GOF。"
      },
      {
        "type": "heading",
        "text": "目前研究已经知道什么"
      },
      {
        "type": "paragraph",
        "text": "较可靠的结论是：经过功能确认的杂合 STAT3 GOF 变异，可导致以早发自身免疫、淋巴细胞增生和多器官炎症为特点的 IEI；抗体不足和感染也是这一疾病谱中的重要部分。 STAT3 GOF 自然病程研究"
      },
      {
        "type": "paragraph",
        "text": "因为机制比较明确，研究者正在探索降低过强 JAK–STAT 信号的治疗策略。一些队列观察到了症状改善的线索，但不同器官表现、长期安全性和最适合的人群仍需要更多高质量研究。研究性结果不应被理解为适用于所有患者的统一方案。"
      }
    ],
    "sources": [
      "Jägle S, et al. Natural history of STAT3 gain-of-function syndrome. Journal of Allergy and Clinical Immunology. 2023.",
      "STAT3 GOF in an adult patient initially diagnosed with CVID. Frontiers in Immunology. 2021.",
      "Tangye SG, et al. Human inborn errors of immunity: 2024 IUIS update."
    ]
  },
  {
    "slug": "stat1-gof",
    "category": "gene",
    "title": "STAT1 gain-of-function：为什么抗病毒警报一直响，反而让免疫失衡？",
    "excerpt": "STAT1 是免疫细胞里的一条警报线路。",
    "blocks": [
      {
        "type": "paragraph",
        "text": "STAT1 是免疫细胞里的一条警报线路。"
      },
      {
        "type": "paragraph",
        "text": "当身体发现病毒或其他威胁时，细胞会发出干扰素等信息。STAT1 接到这些信息后，帮助免疫系统进入防御状态。"
      },
      {
        "type": "paragraph",
        "text": "短时间内，这是一件好事。"
      },
      {
        "type": "paragraph",
        "text": "但如果警报一直响，问题就出现了。细胞会长期处于紧张状态，其他免疫路线可能被干扰，原本应该维持平衡的反应也会受影响。"
      },
      {
        "type": "paragraph",
        "text": "STAT1 gain-of-function（STAT1 GOF）就是这样一种情况：某些遗传变异让 STAT1 的警报信号过强或关闭得太慢。"
      },
      {
        "type": "heading",
        "text": "最有代表性的线索：反复念珠菌感染"
      },
      {
        "type": "paragraph",
        "text": "STAT1 GOF 最典型的表现，是口腔、皮肤、指甲或生殖道反复、持续发生念珠菌感染。"
      },
      {
        "type": "paragraph",
        "text": "念珠菌本来就可能少量存在于人体表面。健康免疫系统通常能把它控制住，不让它反复造成问题。抵御念珠菌时，一条与 IL-17 有关的免疫路线特别重要。"
      },
      {
        "type": "paragraph",
        "text": "STAT1 信号过强时，反而会干扰这条抗真菌路线。于是，患者可能反复出现鹅口疮、口角炎、指甲真菌感染或其他黏膜念珠菌问题。"
      },
      {
        "type": "paragraph",
        "text": "这是一种很容易被误解的现象：警报太强，不等于防御一定更强。免疫系统里，一条线路过度占用资源，可能让另一条重要线路无法正常工作。"
      },
      {
        "type": "heading",
        "text": "患者还可能经历什么"
      },
      {
        "type": "paragraph",
        "text": "STAT1 GOF 的表现不只包括念珠菌感染。"
      },
      {
        "type": "paragraph",
        "text": "国际队列研究发现，患者还可能有："
      },
      {
        "type": "paragraph",
        "text": "反复细菌感染，尤其是呼吸道或皮肤感染；"
      },
      {
        "type": "paragraph",
        "text": "疱疹病毒等病毒感染；"
      },
      {
        "type": "paragraph",
        "text": "自身免疫性甲状腺病、糖尿病、血细胞减少等；"
      },
      {
        "type": "paragraph",
        "text": "肠道、肝脏或血管相关问题；"
      },
      {
        "type": "paragraph",
        "text": "部分患者的低免疫球蛋白、记忆 B 细胞减少或抗体反应不足。"
      },
      {
        "type": "paragraph",
        "text": "因此，一些患者会因低 IgG、反复感染或抗体反应问题进入 CVID 的诊断路径；STAT1 GOF 进一步解释了，为什么患者同时还有顽固念珠菌感染或自身免疫线索。"
      },
      {
        "type": "paragraph",
        "text": "但念珠菌感染也有许多其他原因。只有经过遗传和功能证据确认的 STAT1 GOF，才能作为明确解释。"
      },
      {
        "type": "heading",
        "text": "从基因机制理解 CVID"
      },
      {
        "type": "paragraph",
        "text": "STAT1 GOF 患者中的抗体不足，并不是每个人都会有，也不是这个疾病最早被发现的核心特征。"
      },
      {
        "type": "paragraph",
        "text": "但对存在低免疫球蛋白、反复感染和抗体功能异常的患者来说，STAT1 GOF 能把这些表现放进更完整的免疫图景：持续的警报信号，可能影响 T 细胞帮助、抗真菌免疫、免疫耐受和 B 细胞成熟。"
      },
      {
        "type": "paragraph",
        "text": "所以，患者不必把“感染”“念珠菌”“自身免疫”“抗体低”看成几个无关的问题；它们可能是同一条异常信号在不同地方造成的结果。"
      },
      {
        "type": "heading",
        "text": "遗传线索怎样理解"
      },
      {
        "type": "paragraph",
        "text": "STAT1 GOF 通常为常染色体显性遗传。"
      },
      {
        "type": "paragraph",
        "text": "一份会让 STAT1 功能增强的致病变异就可能导致疾病。变异可从父母继承，也可新发生。"
      },
      {
        "type": "paragraph",
        "text": "STAT1 特别需要强调“变异功能”的判断："
      },
      {
        "type": "paragraph",
        "text": "有些 STAT1 变异会让功能增强，即 STAT1 GOF；"
      },
      {
        "type": "paragraph",
        "text": "另一些会让功能减弱，可造成完全不同的感染易感模式；"
      },
      {
        "type": "paragraph",
        "text": "还有很多变异目前无法确定其意义。"
      },
      {
        "type": "paragraph",
        "text": "因此，报告中的 STAT1 变异必须结合功能实验、临床表现和专业遗传解释，不能只按“有变异”处理。"
      },
      {
        "type": "heading",
        "text": "目前研究已经知道什么"
      },
      {
        "type": "paragraph",
        "text": "较可靠的研究支持，经过功能确认的杂合 STAT1 GOF 变异是慢性皮肤黏膜念珠菌感染的重要遗传原因，也可伴细菌、病毒感染、自身免疫和内分泌问题。 274 名患者国际队列"
      },
      {
        "type": "paragraph",
        "text": "研究也支持，STAT1 过度活跃与 IL-17 抗真菌免疫受损有关。 STAT1 GOF 的发现研究"
      },
      {
        "type": "paragraph",
        "text": "目前仍不清楚的是：为什么同样的 STAT1 GOF 变异在不同家庭中严重程度不同；哪些患者更容易出现低免疫球蛋白；以及降低异常信号的机制导向治疗在长期随访中的获益和风险。"
      }
    ],
    "sources": [
      "Toubiana J, et al. Heterozygous STAT1 gain-of-function mutations underlie a broad clinical phenotype. Blood. 2016.",
      "Liu L, et al. STAT1 gain-of-function mutations impair IL-17 immunity and cause chronic mucocutaneous candidiasis. Journal of Experimental Medicine. 2011.",
      "Asano T, et al. STAT1 GOF and chronic mucocutaneous candidiasis: comprehensive review. Immunological Reviews. 2024."
    ]
  },
  {
    "slug": "pik3r1",
    "category": "gene",
    "title": "PIK3R1：免疫细胞的油门旁边，为什么还需要一个调节器？",
    "excerpt": "免疫细胞遇到感染时，需要加速。",
    "blocks": [
      {
        "type": "paragraph",
        "text": "免疫细胞遇到感染时，需要加速。"
      },
      {
        "type": "paragraph",
        "text": "它们要增殖、移动、发出信号、帮助 B 细胞、清除感染。PI3Kδ 是驱动这些动作的重要信号系统，可以把它想成免疫细胞的油门。"
      },
      {
        "type": "paragraph",
        "text": "但油门不能一直踩到底。"
      },
      {
        "type": "paragraph",
        "text": "PIK3R1 编码的是这套系统里的调节部分。它并不负责直接“加速”，而是帮助限制和校准 PI3Kδ 信号的强度。"
      },
      {
        "type": "paragraph",
        "text": "某些 PIK3R1 变异会让这个调节器失去作用。结果不是油门失灵，而是 PI3Kδ 信号变得过强，形成 APDS2。"
      },
      {
        "type": "heading",
        "text": "为什么油门太强，最后会变成免疫缺陷"
      },
      {
        "type": "paragraph",
        "text": "这又是一个容易让人困惑的免疫故事。"
      },
      {
        "type": "paragraph",
        "text": "一开始，过强的 PI3Kδ 信号会让免疫细胞看起来很活跃。但长期持续加速后，细胞可能过早消耗、成熟失衡，尤其是 T 细胞和 B 细胞。"
      },
      {
        "type": "paragraph",
        "text": "可以把它想成一支永远不能休息的跑步队。刚开始跑得很快，久了却更容易疲惫、队形混乱，也难以应对真正需要耐力的任务。"
      },
      {
        "type": "paragraph",
        "text": "于是，患者可能同时出现："
      },
      {
        "type": "paragraph",
        "text": "反复呼吸道感染；"
      },
      {
        "type": "paragraph",
        "text": "抗体不足；"
      },
      {
        "type": "paragraph",
        "text": "异常淋巴细胞增生；"
      },
      {
        "type": "paragraph",
        "text": "病毒感染；"
      },
      {
        "type": "paragraph",
        "text": "自身免疫或肠道炎症。"
      },
      {
        "type": "paragraph",
        "text": "这些不是互相矛盾的表现，而是长期“油门过度”造成的不同后果。"
      },
      {
        "type": "heading",
        "text": "患者可能经历什么"
      },
      {
        "type": "paragraph",
        "text": "PIK3R1 相关 APDS2 的常见线索包括："
      },
      {
        "type": "paragraph",
        "text": "反复中耳炎、鼻窦炎、支气管炎和肺炎；"
      },
      {
        "type": "paragraph",
        "text": "IgG、IgA 偏低，而 IgM 可能偏高；"
      },
      {
        "type": "paragraph",
        "text": "脾大、淋巴结增大、扁桃体或腺样体明显增生；"
      },
      {
        "type": "paragraph",
        "text": "支气管扩张；"
      },
      {
        "type": "paragraph",
        "text": "慢性腹泻、肠道感染或肠道淋巴组织增生；"
      },
      {
        "type": "paragraph",
        "text": "疱疹病毒、EB 病毒或巨细胞病毒相关问题；"
      },
      {
        "type": "paragraph",
        "text": "自身免疫性血细胞减少；"
      },
      {
        "type": "paragraph",
        "text": "部分患者身材偏矮、发育迟缓、学习困难，或牙齿萌出延迟；"
      },
      {
        "type": "paragraph",
        "text": "长期需要认真评估淋巴瘤等风险线索。"
      },
      {
        "type": "paragraph",
        "text": "在最早的 36 名 APDS2 患者队列中，反复上呼吸道感染、肺炎和慢性淋巴组织增生非常常见；多数患者有 IgG、IgA 偏低，部分患者 IgM 偏高。 APDS2 国际队列"
      },
      {
        "type": "paragraph",
        "text": "这组数据能帮助理解疾病范围，却不能用作个人一定会发生某项问题的概率。"
      },
      {
        "type": "heading",
        "text": "从基因机制理解 CVID"
      },
      {
        "type": "paragraph",
        "text": "部分 PIK3R1 患者最初被诊断为 CVID，因为他们有低 IgG、低 IgA、反复感染和抗体反应不佳。"
      },
      {
        "type": "paragraph",
        "text": "PIK3R1 的遗传诊断提供了更完整的解释：抗体不足不是单纯 B 细胞“做不出抗体”，而是 PI3Kδ 这条加速路线长期过度活跃，使 B、T 细胞都难以保持正常成熟与平衡。"
      },
      {
        "type": "paragraph",
        "text": "这也解释了为什么 APDS2 患者常同时有感染、脾大或淋巴结增大、病毒问题和自身免疫。"
      },
      {
        "type": "heading",
        "text": "遗传线索怎样理解"
      },
      {
        "type": "paragraph",
        "text": "APDS2 通常为常染色体显性遗传。"
      },
      {
        "type": "paragraph",
        "text": "一份特定、经过确认会导致 PI3Kδ 过度活化的 PIK3R1 变异就可能造成 APDS2。部分来自父母，部分为新发生变异。"
      },
      {
        "type": "paragraph",
        "text": "PIK3R1 很复杂，因为不同类型、不同位置的变异可以造成不同疾病。例如，有些 PIK3R1 变异与 SHORT 综合征有关，并不等于 APDS2。"
      },
      {
        "type": "paragraph",
        "text": "因此，遗传报告必须回答的不只是“是不是 PIK3R1”，还包括："
      },
      {
        "type": "paragraph",
        "text": "变异位于哪里；"
      },
      {
        "type": "paragraph",
        "text": "它会让 PI3Kδ 信号增强还是造成其他影响；"
      },
      {
        "type": "paragraph",
        "text": "患者的免疫表现是否符合 APDS2；"
      },
      {
        "type": "paragraph",
        "text": "是否有家族验证或功能证据。"
      },
      {
        "type": "paragraph",
        "text": "VUS 不能单独确诊 APDS2。"
      },
      {
        "type": "heading",
        "text": "目前研究已经知道什么"
      },
      {
        "type": "paragraph",
        "text": "较可靠的研究结论是：特定 PIK3R1 变异可使 PI3Kδ 信号过度活化，导致 APDS2；这是一种可造成抗体不足、感染、淋巴细胞增生、自身免疫和肠道问题的遗传性免疫疾病。 APDS GeneReviews 概览"
      },
      {
        "type": "paragraph",
        "text": "因为 APDS2 的异常通路明确，PI3Kδ 抑制策略已从机制研究进入正式临床研究和部分地区的临床应用。现有证据显示，它能改善某些与淋巴组织增生相关的指标；但对不同患者、不同器官问题的长期效果仍在持续收集。患者不应把“有靶向药”理解为不需要个体化评估。"
      }
    ],
    "sources": [
      "Deau MC, et al. Clinical and immunologic phenotype of activated PI3Kδ syndrome 2. Journal of Allergy and Clinical Immunology. 2016.",
      "Sacco K, Uzel G. Activated PI3K Delta Syndrome. GeneReviews. Updated 2025.",
      "Elkaim E, et al. ESID APDS registry: disease evolution and response to rapamycin. Journal of Allergy and Clinical Immunology. 2018."
    ]
  },
  {
    "slug": "lab-results",
    "category": "practical",
    "title": "我的免疫球蛋白化验单，到底在说什么？",
    "excerpt": "拿到化验单时，最容易看到的是一串缩写：IgG、IgA、IgM、IgG 亚类、抗体滴度、记忆 B 细胞。",
    "blocks": [
      {
        "type": "paragraph",
        "text": "拿到化验单时，最容易看到的是一串缩写：IgG、IgA、IgM、IgG 亚类、抗体滴度、记忆 B 细胞。"
      },
      {
        "type": "paragraph",
        "text": "它们看起来像一张成绩单，但其实更像一张地图：每一项都在回答不同问题。没有哪一个数字能独自说明“免疫力好不好”，也没有哪一次抽血能写出完整结论。"
      },
      {
        "type": "heading",
        "text": "IgG：血液和组织里的主要保护抗体"
      },
      {
        "type": "paragraph",
        "text": "IgG 是血液中最主要的抗体类型。它能帮助中和病原体、标记病原体、让吞噬细胞更容易清除目标。"
      },
      {
        "type": "paragraph",
        "text": "CVID 诊断中，持续偏低的 IgG 是重要线索。但 IgG 数值本身不能说明全部事情。"
      },
      {
        "type": "paragraph",
        "text": "两位患者的 IgG 都偏低，其中一位可能很少感染，另一位可能频繁肺炎；两位患者的 IgG 都在相近范围，也不代表他们对疫苗、细菌或病毒的保护相同。"
      },
      {
        "type": "paragraph",
        "text": "医生会把 IgG 放回感染史、疫苗抗体反应、B 细胞检查和器官情况中理解，而不是只看一个数字。"
      },
      {
        "type": "heading",
        "text": "IgA：守在呼吸道和肠道门口的抗体"
      },
      {
        "type": "paragraph",
        "text": "IgA 特别适合留在鼻腔、气道和肠道等黏膜表面。"
      },
      {
        "type": "paragraph",
        "text": "它像边界上的一层保护，帮助阻止病原体黏附和进入人体组织。IgA 偏低时，有些人会有更多呼吸道或肠道问题；也有不少人症状并不明显。"
      },
      {
        "type": "paragraph",
        "text": "因此，IgA 偏低不是“必然会生病”的预言，也不应被忽略。对 CVID 来说，低 IgG 合并低 IgA，或低 IgG 合并低 IgM，是诊断评估中的重要组合之一。"
      },
      {
        "type": "heading",
        "text": "IgM：较早出现的抗体"
      },
      {
        "type": "paragraph",
        "text": "IgM 往往是一次感染早期较快出现的抗体。"
      },
      {
        "type": "paragraph",
        "text": "它像一张大网，能帮助身体先把病原体围住。不同 CVID 患者的 IgM 可以低、正常，偶尔也会偏高。它的意义取决于完整免疫图景。"
      },
      {
        "type": "paragraph",
        "text": "例如，在某些 PI3K 相关疾病中，IgG 和 IgA 可以偏低，而 IgM 反而偏高；这并不代表抗体保护更好，而是提示 B 细胞成熟和类别转换可能没有顺利完成。"
      },
      {
        "type": "heading",
        "text": "“抗体滴度”在问什么"
      },
      {
        "type": "paragraph",
        "text": "疫苗抗体或特异性抗体滴度，问的不是“身体里有多少抗体”，而是："
      },
      {
        "type": "heading",
        "text": "身体是否能针对某个具体目标制造抗体，并把它保留下来？"
      },
      {
        "type": "paragraph",
        "text": "例如，医生可能会观察肺炎球菌、破伤风、乙型肝炎等相关抗体。不同疫苗需要用不同方式解释；一次结果低，也不能脱离接种时间、既往接种史、年龄和正在使用的治疗来判断。"
      },
      {
        "type": "paragraph",
        "text": "如果已经开始免疫球蛋白替代治疗，血液中测到的某些特异性 IgG 可能部分来自输入的制剂，而不是患者自身产生的抗体。因此，治疗前后的化验含义并不完全一样。"
      },
      {
        "type": "heading",
        "text": "IgG 亚类：有用，但不能单独下结论"
      },
      {
        "type": "paragraph",
        "text": "IgG 还可分为不同亚类，例如 IgG1、IgG2、IgG3、IgG4。"
      },
      {
        "type": "paragraph",
        "text": "有些亚类与应对特定类型病原体有关。比如 IgG2 与对某些细菌荚膜多糖的反应有关。但亚类数值会随年龄、实验室方法和时间波动。"
      },
      {
        "type": "paragraph",
        "text": "所以，“某个亚类低”是一个值得结合病史进一步看的线索，不是单独就能诊断 CVID 的标签。"
      },
      {
        "type": "heading",
        "text": "B 细胞检查又在说什么"
      },
      {
        "type": "paragraph",
        "text": "B 细胞检查不是直接测抗体，而是看“抗体生产线上的人在哪里”。"
      },
      {
        "type": "paragraph",
        "text": "常见项目包括："
      },
      {
        "type": "paragraph",
        "text": "B 细胞总数：有没有足够的 B 细胞；"
      },
      {
        "type": "paragraph",
        "text": "初始 B 细胞：还没有遇到特定病原体的 B 细胞；"
      },
      {
        "type": "paragraph",
        "text": "类别转换记忆 B 细胞：是否形成过更成熟的抗体记忆；"
      },
      {
        "type": "paragraph",
        "text": "浆母细胞等：是否正在走向抗体工厂的阶段。"
      },
      {
        "type": "paragraph",
        "text": "这些检查能帮助理解抗体为什么不足，但也不能单独预测一个人的全部病程。"
      },
      {
        "type": "heading",
        "text": "一张化验单最不该告诉你的事"
      },
      {
        "type": "paragraph",
        "text": "它不该让人觉得：“我的数字低，所以我一定会怎样。”\n也不该让人觉得：“这次正常，所以问题一定不存在。”"
      },
      {
        "type": "paragraph",
        "text": "CVID 的评估需要看趋势，而不是只看一次结果；需要看病人，而不是只看数字。专业指南也强调，CVID 诊断应结合低 IgG、其他免疫球蛋白异常或抗体反应问题，并排除继发性原因。 2025 IEI 实践参数"
      }
    ],
    "sources": [
      "AAAAI/ACAAI 2025 IEI 实践参数。",
      "Bonilla FA, et al. ICON：CVID 国际共识.",
      "ESID. IEI 临床诊断工作定义。"
    ]
  },
  {
    "slug": "immunoglobulin-replacement",
    "category": "practical",
    "title": "补充免疫球蛋白，到底补进了什么？",
    "excerpt": "免疫球蛋白替代治疗最容易被误解成“打针提高免疫力”。",
    "blocks": [
      {
        "type": "paragraph",
        "text": "免疫球蛋白替代治疗最容易被误解成“打针提高免疫力”。"
      },
      {
        "type": "paragraph",
        "text": "它做的事其实更具体，也更朴素：把患者自己难以稳定制造的 IgG 抗体，定期补充进来。"
      },
      {
        "type": "paragraph",
        "text": "它不是让 B 细胞重新长出来，也不是重启患者自己的免疫记忆；它是提供一批可以立刻使用的“现成抗体”。"
      },
      {
        "type": "heading",
        "text": "补进来的是谁的抗体？"
      },
      {
        "type": "paragraph",
        "text": "免疫球蛋白制剂来自许多健康捐献者的血浆，经过筛选、纯化和多重安全处理后制成。"
      },
      {
        "type": "paragraph",
        "text": "其中绝大部分是 IgG。因为捐献者来自广泛人群，制剂中包含针对许多常见病原体的抗体。输入后，这些抗体会暂时在患者血液和组织液中巡逻，帮助识别和中和一些感染。"
      },
      {
        "type": "paragraph",
        "text": "可以把它想成：患者自己的抗体工厂供应不足，于是定期收到一批由许多人共同建立的“现成防护库存”。"
      },
      {
        "type": "heading",
        "text": "它能做什么"
      },
      {
        "type": "paragraph",
        "text": "替代治疗最明确的作用，是降低部分细菌性呼吸道感染的频率和严重程度。"
      },
      {
        "type": "paragraph",
        "text": "这些输入的 IgG 可以："
      },
      {
        "type": "paragraph",
        "text": "中和部分病原体或毒素；"
      },
      {
        "type": "paragraph",
        "text": "给病原体贴上更容易被吞噬细胞识别的标签；"
      },
      {
        "type": "paragraph",
        "text": "补足患者血液中缺少的抗体保护。"
      },
      {
        "type": "paragraph",
        "text": "许多患者会发现鼻窦炎、支气管炎或肺炎减少，恢复更顺利。但效果也会受到既往肺部损伤、病原体种类、器官炎症和其他免疫问题影响。"
      },
      {
        "type": "heading",
        "text": "它不能做什么"
      },
      {
        "type": "paragraph",
        "text": "这部分同样重要。"
      },
      {
        "type": "paragraph",
        "text": "补充免疫球蛋白不能："
      },
      {
        "type": "paragraph",
        "text": "让患者自己的 B 细胞自动恢复正常成熟；"
      },
      {
        "type": "paragraph",
        "text": "让身体重新建立完整的疫苗或感染记忆；"
      },
      {
        "type": "paragraph",
        "text": "自动消除自身免疫、肠病、GLILD 或淋巴组织增生；"
      },
      {
        "type": "paragraph",
        "text": "代替对感染、肺部或其他器官问题的评估。"
      },
      {
        "type": "paragraph",
        "text": "这不是治疗“能力不够”，而是治疗目标本来就不同。它补充的是抗体防护，不是把整套免疫系统修复回原状。"
      },
      {
        "type": "heading",
        "text": "静脉和皮下：同样是 IgG，不同的送达方式"
      },
      {
        "type": "paragraph",
        "text": "静脉免疫球蛋白（IVIG）通过静脉输入，通常间隔较长。输入后血液中的 IgG 会先升高，再逐渐下降。"
      },
      {
        "type": "paragraph",
        "text": "皮下免疫球蛋白（SCIG）在皮下组织中缓慢吸收，通常输入更频繁，但 IgG 水平相对更平稳。"
      },
      {
        "type": "paragraph",
        "text": "哪种方式更适合，并没有一个对所有人通用的答案。输入频率、生活节奏、静脉条件、既往反应、所在地医疗系统和个人偏好都会影响选择。两种方式都可以有效提供替代性 IgG。 IDF 免疫球蛋白替代治疗说明"
      },
      {
        "type": "heading",
        "text": "为什么有的人感觉“下一次输注前更容易不舒服”"
      },
      {
        "type": "paragraph",
        "text": "有些使用 IVIG 的患者会感到，在下一次输注前几天，疲劳或感染担忧增加。原因之一可能是血液中的 IgG 水平会随时间逐渐下降。"
      },
      {
        "type": "paragraph",
        "text": "但疲劳、头痛、鼻塞或腹部不适并不一定都由 IgG 水平造成，也可能与感染、睡眠、压力、炎症或其他疾病有关。任何稳定出现的规律，都值得记录并和团队讨论，而不是自行调整剂量或间隔。"
      },
      {
        "type": "heading",
        "text": "关于安全，最重要的事实"
      },
      {
        "type": "paragraph",
        "text": "免疫球蛋白制剂是血液来源产品，因此生产过程会对捐献者、血浆和最终产品进行多重筛查与病毒灭活/去除处理。它的安全记录总体良好，但任何治疗都有可能出现不良反应。"
      },
      {
        "type": "paragraph",
        "text": "不同产品、输入方式和个人身体情况都不同。输入中的不适、持续头痛、皮疹、胸闷、呼吸困难、明显尿量变化或其他新症状，应按个人治疗计划及时联系输注团队或医疗服务。"
      }
    ],
    "sources": [
      "Immune Deficiency Foundation. Immunoglobulin replacement therapy。",
      "Immune Deficiency Foundation. Ig replacement therapy is as individual as you。",
      "Bonilla FA, et al. ICON：CVID 国际共识。"
    ]
  },
  {
    "slug": "family",
    "category": "practical",
    "title": "家人需要知道什么？",
    "excerpt": "CVID 的诊断很少只影响一个人。",
    "blocks": [
      {
        "type": "paragraph",
        "text": "CVID 的诊断很少只影响一个人。"
      },
      {
        "type": "paragraph",
        "text": "患者会担心：“这会不会遗传给孩子？”\n家人会担心：“会不会传染？”\n也有人不知道该怎样帮忙，只能不断说“你看起来没事”。"
      },
      {
        "type": "paragraph",
        "text": "一篇给家人的科普，最重要的不是让每个人都学会免疫学，而是帮助他们知道：这是什么、它不是什么，以及怎样成为真正有用的支持。"
      },
      {
        "type": "heading",
        "text": "CVID 不会传染"
      },
      {
        "type": "paragraph",
        "text": "CVID 是免疫系统本身的疾病，不是感染本身。"
      },
      {
        "type": "paragraph",
        "text": "患者可能更容易感染，但不会把 CVID “传给”家人、同事或同学。家人不需要因此隔离患者，也不需要把患者当作传染源。"
      },
      {
        "type": "paragraph",
        "text": "真正需要留意的是：患者面对某些感染时，可能恢复更慢或风险更高。因此，家人的理解、及时沟通和共同减少不必要的感染暴露，才是更有帮助的事。"
      },
      {
        "type": "heading",
        "text": "CVID 有遗传线索，但不是每个家庭都有同一种答案"
      },
      {
        "type": "paragraph",
        "text": "部分 CVID 患者能找到明确遗传机制；部分患者没有单一基因答案。即使同一个家族携带相同变异，症状也可能差异很大。"
      },
      {
        "type": "paragraph",
        "text": "所以，“家里有人有 CVID”不等于每位亲属都需要马上做同一种检测；“家里没人有类似病史”也不等于没有遗传因素。"
      },
      {
        "type": "paragraph",
        "text": "更值得告诉医生的，是家族中是否有人有："
      },
      {
        "type": "paragraph",
        "text": "反复或严重感染；"
      },
      {
        "type": "paragraph",
        "text": "低免疫球蛋白；"
      },
      {
        "type": "paragraph",
        "text": "不明原因的自身免疫性血细胞减少；"
      },
      {
        "type": "paragraph",
        "text": "脾大、淋巴结长期增大；"
      },
      {
        "type": "paragraph",
        "text": "早发或复杂的肠病、肺病；"
      },
      {
        "type": "paragraph",
        "text": "已知 IEI 或免疫相关遗传结果。"
      },
      {
        "type": "paragraph",
        "text": "由免疫专科和遗传团队判断，哪些亲属需要进一步评估，会比全家自行猜测更可靠。"
      },
      {
        "type": "heading",
        "text": "家人能怎样真正帮上忙"
      },
      {
        "type": "paragraph",
        "text": "最有帮助的支持，常常不是“你要坚强”，而是把长期疾病从患者一个人的任务，变成可以共同管理的生活安排。"
      },
      {
        "type": "paragraph",
        "text": "例如："
      },
      {
        "type": "paragraph",
        "text": "理解输注、复诊、感染恢复需要时间，不把它当作“偶尔请假”；"
      },
      {
        "type": "paragraph",
        "text": "帮助记录感染、治疗反应和检查时间线；"
      },
      {
        "type": "paragraph",
        "text": "在患者感到不适或发热时，尊重既定的医疗联系计划；"
      },
      {
        "type": "paragraph",
        "text": "不用“你看起来很好”否定疲劳、焦虑或慢性症状；"
      },
      {
        "type": "paragraph",
        "text": "在患者愿意时，陪同重要门诊，帮助记住信息和提出问题；"
      },
      {
        "type": "paragraph",
        "text": "尊重患者对隐私的选择：是否告诉亲友、同事、学校，由患者决定。"
      },
      {
        "type": "heading",
        "text": "对孩子和青少年，怎样解释"
      },
      {
        "type": "paragraph",
        "text": "儿童或青少年不需要听完整套分子机制。"
      },
      {
        "type": "paragraph",
        "text": "可以从生活语言开始：“你的身体制造保护抗体的能力比别人慢一些，所以医生会帮你补充抗体、预防感染。”随着年龄增长，再逐步解释疾病、治疗和遗传线索。"
      },
      {
        "type": "paragraph",
        "text": "最重要的是避免把孩子定义成“脆弱的人”。CVID 是他或她生活的一部分，不是全部身份。"
      },
      {
        "type": "heading",
        "text": "家人也可以有自己的情绪"
      },
      {
        "type": "paragraph",
        "text": "家属可能同时感到担心、内疚、疲惫或无力。尤其在遗传结果出现后，有些父母会反复问：“是不是我传给了孩子？”"
      },
      {
        "type": "paragraph",
        "text": "遗传不是谁的过错。绝大多数人并不知道自己携带什么变异；有些变异本来就是新发生的。与其把精力放在自责，不如把问题转成更有用的方向：现在需要了解什么、如何陪伴、怎样获得可靠信息。"
      }
    ],
    "sources": [
      "CDC. About Primary Immunodeficiency。",
      "ESID. IEI 临床诊断工作定义。",
      "Tangye SG, et al. Human inborn errors of immunity: 2024 IUIS update。"
    ]
  },
  {
    "slug": "research-participation",
    "category": "research",
    "title": "参与患者登记和研究，究竟意味着什么？",
    "excerpt": "CVID 很少见，但患者并不孤单。",
    "blocks": [
      {
        "type": "paragraph",
        "text": "CVID 很少见，但患者并不孤单。"
      },
      {
        "type": "paragraph",
        "text": "每一位患者经历的反复感染、肺部检查、肠道问题、遗传结果、输注体验和漫长等待，都是医学尚未完全回答的问题。正是许多患者愿意把这些经历汇聚起来，医生才逐渐看见：CVID 不只是抗体不足；不同人的疾病可以走向很不一样的方向；有些风险需要更早被发现，有些治疗需要更贴近真实生活。"
      },
      {
        "type": "paragraph",
        "text": "参与研究，不只是“贡献一份数据”。它是在帮助医学更认真地认识这群患者，也是在为后来的人把路走得更清楚一些。"
      },
      {
        "type": "heading",
        "text": "一个人的经历，怎样帮助很多人"
      },
      {
        "type": "paragraph",
        "text": "对罕见病来说，单个医院很难看到足够多的患者。"
      },
      {
        "type": "paragraph",
        "text": "有的人主要反复肺炎；有的人有肠病、自身免疫或脾大；有的人多年后才发现遗传原因；有的人最困扰的不是感染，而是疲劳、治疗负担或“看起来没病”的压力。"
      },
      {
        "type": "paragraph",
        "text": "当这些长期经历被系统地记录下来，研究者才能逐渐回答："
      },
      {
        "type": "paragraph",
        "text": "哪些问题更常一起出现；"
      },
      {
        "type": "paragraph",
        "text": "哪些表现可能提示更高的器官风险；"
      },
      {
        "type": "paragraph",
        "text": "哪些基因结果真正与疾病有关；"
      },
      {
        "type": "paragraph",
        "text": "哪些检查值得长期进行；"
      },
      {
        "type": "paragraph",
        "text": "什么才是患者真正关心的治疗改善。"
      },
      {
        "type": "paragraph",
        "text": "患者愿意参与，才能让研究不只围绕化验数字，也围绕真实生活。"
      },
      {
        "type": "heading",
        "text": "患者登记：让疾病有一张更完整的长期地图"
      },
      {
        "type": "paragraph",
        "text": "患者登记通常记录诊断、感染、治疗、检查、遗传和长期随访资料。"
      },
      {
        "type": "paragraph",
        "text": "它不是新药试验，也不要求患者改变现有治疗。它更像为 CVID 建立一张长期地图：每个人贡献一段自己的路线，最终让研究者看清疾病的全貌。"
      },
      {
        "type": "paragraph",
        "text": "很多今天已经被重视的问题——例如自身免疫、肺部炎症、肠病、肝脾问题和淋巴组织增生——都离不开长期患者队列和登记研究。"
      },
      {
        "type": "paragraph",
        "text": "ESID、USIDNET 等登记系统的意义正在于此：让不同地区、不同年龄和不同表现的患者经验能够被汇聚、被看见。 USIDNET 介绍"
      },
      {
        "type": "heading",
        "text": "科学研究：寻找“为什么”的答案"
      },
      {
        "type": "paragraph",
        "text": "除了患者登记，患者也可能参与遗传、免疫细胞、样本或生活质量研究。"
      },
      {
        "type": "paragraph",
        "text": "有些研究会分析血液、唾液、粪便或其他样本，了解 B 细胞为什么难以形成抗体记忆；有些研究会寻找新的遗传机制；有些会研究肠道微生物组、GLILD 或长期炎症；还有一些会记录疲劳、工作、学习、心理压力和输注体验。"
      },
      {
        "type": "paragraph",
        "text": "这些项目的直接收益未必立刻回到某一位参与者身上，但它们是未来更精准诊断和更好治疗的基础。"
      },
      {
        "type": "paragraph",
        "text": "一位患者的样本，可能帮助确认一个新基因。\n一份长期随访资料，可能帮助研究者理解某种肺部风险。\n一张生活质量问卷，可能让临床研究开始认真衡量“患者是否过得更好”，而不是只看一个化验结果。"
      },
      {
        "type": "heading",
        "text": "临床试验：让新方法真正接受检验"
      },
      {
        "type": "paragraph",
        "text": "临床试验是另一种更直接的研究。"
      },
      {
        "type": "paragraph",
        "text": "它不是“试试看新药”，而是在严格设计和监督下，回答一个明确问题：一种新药、新检查、新剂量方案或新治疗策略，是否安全？是否有效？适合哪些人？"
      },
      {
        "type": "paragraph",
        "text": "CVID 和明确遗传机制相关的研究，特别需要患者参与。因为没有足够的参与者，再有希望的机制也无法证明是否真的能改善感染、炎症、器官表现或生活质量。"
      },
      {
        "type": "paragraph",
        "text": "临床试验可能研究："
      },
      {
        "type": "paragraph",
        "text": "针对特定免疫通路的新药；"
      },
      {
        "type": "paragraph",
        "text": "改善免疫球蛋白替代体验的新方式；"
      },
      {
        "type": "paragraph",
        "text": "预测肺部或肠道风险的新检查；"
      },
      {
        "type": "paragraph",
        "text": "适合特定遗传机制患者的精准治疗；"
      },
      {
        "type": "paragraph",
        "text": "已有治疗在不同患者群体中的长期效果。"
      },
      {
        "type": "paragraph",
        "text": "参与临床试验，有机会让患者更早接触正在研究的新方法；但它不保证个人一定获益。研究中的治疗可能有效，也可能效果有限，或不适合某些人。正因为如此，临床试验需要伦理审查、持续安全监测和完整的知情同意流程。 ClinicalTrials.gov：了解临床研究"
      },
      {
        "type": "heading",
        "text": "参与的意义，不只是为了“以后的人”"
      },
      {
        "type": "paragraph",
        "text": "很多患者会说：“我参加，是因为我不希望后来的人也花很多年才得到答案。”"
      },
      {
        "type": "paragraph",
        "text": "这是一种很珍贵的力量。"
      },
      {
        "type": "paragraph",
        "text": "但参与研究也不必被说成无私牺牲。患者有权希望得到更清楚的疾病解释、更密切的随访、更可靠的信息，也有权希望自己的经验被医学真正重视。"
      },
      {
        "type": "paragraph",
        "text": "对罕见病而言，患者、家属、医生和研究者本来就应该站在同一边。研究不是研究者单方面“研究患者”，而是共同寻找答案。"
      },
      {
        "type": "heading",
        "text": "知情同意：参与的前提，是被尊重"
      },
      {
        "type": "paragraph",
        "text": "鼓励患者参与研究，必须建立在自愿、充分知情和隐私保护的基础上。"
      },
      {
        "type": "paragraph",
        "text": "在正式参加前，研究团队应清楚说明研究内容、需要提供什么资料或样本、可能增加哪些随访或检查、已知风险、潜在获益、资料如何保存，以及退出研究的方式。"
      },
      {
        "type": "paragraph",
        "text": "知情同意不是一次签字就结束。患者在研究过程中始终有权了解进展、提出疑问和重新决定是否继续参与。ESID 登记也要求在录入资料前取得患者知情同意，并遵循当地伦理与数据保护要求。 ESID 知情同意说明"
      },
      {
        "type": "paragraph",
        "text": "不参加研究，不会影响常规医疗照护。\n参加研究，也不意味着必须接受自己不理解或不愿意接受的安排。"
      },
      {
        "type": "paragraph",
        "text": "真正值得鼓励的研究参与，是患者在被充分尊重、充分理解后，选择成为改变的一部分。"
      },
      {
        "type": "heading",
        "text": "患者的声音，也应决定研究什么"
      },
      {
        "type": "paragraph",
        "text": "患者最清楚哪些问题真正影响生活。"
      },
      {
        "type": "paragraph",
        "text": "研究者可能最先想到免疫球蛋白数值、细胞亚群和影像结果；患者则可能更关心：为什么总是疲劳？为什么输注日影响工作？为什么感染恢复比别人慢？我还能不能安心旅行、上学、养育孩子？"
      },
      {
        "type": "paragraph",
        "text": "这些问题同样值得进入研究。"
      },
      {
        "type": "paragraph",
        "text": "一个真正面向患者的 CVID 网站，不只应发布研究结果，也应帮助患者参与决定未来研究优先回答什么。患者不只是研究的对象，更是研究方向的重要共同制定者。"
      }
    ],
    "sources": [
      "ESID. Informed Patient Consent for the ESID Registry。",
      "USIDNET. About USIDNET。",
      "ClinicalTrials.gov. Learn About Studies。",
      "NIH. Clinical Research Trials and You: The Basics。"
    ]
  }
];

Object.assign(exports, {chineseArticles});
},
"src/network-directory.js": function(require, exports) {
const { expandedCards } = require("src/expanded-teams.js");
const additions=[
{id:'intrepid',name:'INTREPID · University of Cambridge',zh:'INTREPID · 剑桥大学',country:'United Kingdom',type:'Research programme',title:'Integrative Translational Research in Primary Immunodeficiency',description:'Clinical and genetic investigation of primary immunodeficiency. The linked UK Biobank project is marked current; this does not establish open patient recruitment.',descriptionZh:'结合临床和遗传信息研究原发性免疫缺陷。所链接的 UK Biobank 项目标注为进行中，不代表正在公开招募患者。',url:'https://www.ukbiobank.ac.uk/projects/integrative-translational-research-in-primary-immunodeficiency-intrepid/',features:['autoimmunity','recurrent_infections'],status:'unknown'},
{id:'cpi',name:'Centre for Personalised Immunology · ANU',zh:'澳大利亚国立大学个体化免疫学中心 CPI',country:'Australia',type:'Research centre',title:'Personalised immunology',description:'A research centre investigating immune dysregulation. NHMRC describes its personalised immunology work; current recruitment is not established by this historical case study.',descriptionZh:'研究免疫调节失衡的中心。NHMRC 的项目介绍记录了其个体化免疫学工作；该历史介绍不确认当前招募情况。',url:'https://www.nhmrc.gov.au/about-us/resources/personalised-immunology',features:['autoimmunity'],status:'unknown'},
{id:'fudan',name:'Children’s Hospital of Fudan University',zh:'复旦大学附属儿科医院临床免疫团队',country:'China',type:'Published cohort',title:'Screening for primary immunodeficiency diseases by next-generation sequencing in early life',description:'Published infant PID cohort (2020), including clinical immunology and genetics teams. Broader paediatric IEI evidence, not a CVID-specific recruitment study.',descriptionZh:'2020 年发表的婴儿 PID 队列，涉及临床免疫和遗传学团队。属于儿科 IEI 证据，并非 CVID 专项招募研究。',url:'https://pubmed.ncbi.nlm.nih.gov/32431812/',features:['recurrent_infections'],status:'completed'},
{id:'chongqing',name:'Children’s Hospital of Chongqing Medical University',zh:'重庆医科大学附属儿童医院免疫研究团队',country:'China',type:'Published cohort',title:'Distribution, clinical features and molecular analysis of primary immunodeficiency diseases in Chinese children: a single-center study from 2005 to 2011',description:'A published paediatric PID cohort (2013), relevant to clinical and molecular patterns across IEI. It is historical research rather than a current recruitment opportunity.',descriptionZh:'2013 年发表的儿科 PID 队列，研究 IEI 临床及分子特征。作为历史研究收录，不作为当前招募机会。',url:'https://pubmed.ncbi.nlm.nih.gov/23673420/',features:['recurrent_infections'],status:'completed'}
];
const communities=[
['PID Care China · PID 加油宝贝关爱中心','China','Patient and family education, support and advocacy.','患者与家属教育、支持及倡导。','https://e-news.ipopi.org/workshop-china-summer-2025/'],
['Immunodeficiency UK','United Kingdom','Support and information for people with immune deficiencies.','为免疫缺陷患者提供支持与信息。','https://www.immunodeficiencyuk.org/'],
['Immune Deficiency Foundation (IDF)','United States','National patient organisation for primary immunodeficiency.','美国原发性免疫缺陷患者组织。','https://primaryimmune.org/'],
['Immune Deficiency Foundation of Australia (IDFA)','Australia','Australian immune deficiency patient organisation.','澳大利亚免疫缺陷患者组织。','https://www.idfa.org.au/'],
['IPOPI','International','International network of national PID patient organisations.','连接各国 PID 患者组织的国际网络。','https://ipopi.org/organisations/'],
['ÖSPID','Austria','National PID patient organisation listed by IPOPI.','IPOPI 收录的奥地利 PID 患者组织。','https://ipopi.org/organisations/'],
['AAPIDP','Argentina','National PID patient organisation listed by IPOPI.','IPOPI 收录的阿根廷 PID 患者组织。','https://ipopi.org/organisations/']
];
function directory(lang,kind,existing=[]){const zh=lang==='zh',t=(a,b)=>zh?b:a;return `<section class="page-shell"><h1>${kind==='community'?t('Communities for people like me','与我相关的社群'):t('Research teams & centres','研究团队与中心')}</h1><p>${t('Explore organisations and follow their public sources for further information.','探索相关组织，通过公开来源了解更多信息。')}</p>${kind!=='community'?`<div class="directory-tools"><label>${t('Search teams or interests','搜索团队或研究方向')}<input id="team-search" type="search"></label><label>${t('Country','国家')}<select id="team-country"><option value="">${t('All countries','全部国家')}</option>${['China','United Kingdom','United States','Germany','Australia','Belgium'].map(c=>`<option>${c}</option>`).join('')}</select></label><p><span id="team-count"></span> ${t('entries','条记录')}</p></div>`:''}<div class="card-grid" ${kind!=='community'?'data-team-directory':''}>${kind==='community'?communities.map(([name,country,en,cn,url])=>`<article class="panel"><small>${country}</small><h2>${name}</h2><p>${t(en,cn)}</p><a href="${url}" target="_blank" rel="noopener">${t('Organisation / source','组织介绍 / 来源')} ↗</a></article>`).join(''):additions.map(a=>`<article class="panel" id="${a.id}"><small>${a.country} · ${a.type}</small><h2>${t(a.name,a.zh)}</h2><p>${t(a.description,a.descriptionZh)}</p><a class="back-link" href="#research/${a.id}">${t('Related research','相关研究')} →</a><p><a href="${a.url}" target="_blank" rel="noopener">${t('Public evidence','公开资料')} ↗</a></p></article>`).join('')+expandedCards(lang)+existing.map(r=>`<article class="panel"><h2>${r[1]}</h2><p>${r[2]}</p><p>${r[3]}</p></article>`).join('')}</div></section>`;}
function extraProjects(){return additions.map(a=>({id:a.id,title:a.title,institution:a.name,country:a.country,status:a.status==='completed'?'Completed':'Unknown',types:[a.type],diagnoses:['suspected_iei'],features:a.features,who:a.description,question:a.description,participation:'See the source; current participation is not confirmed.',source:a.url}));}

Object.assign(exports, {additions,communities,directory,extraProjects});
},
"src/expanded-teams.js": function(require, exports) {
const expandedTeams = [
 ['warnatz','Klaus Warnatz · Freiburg CCI','Germany','CVID · GLILD · clinical immunology','CVID、GLILD 与临床免疫','https://www.uniklinik-freiburg.de/cci/forschung/klaus-warnatz.html'],
 ['grimbacher','Bodo Grimbacher · Freiburg CCI','Germany','Genetic causes of immunodeficiency and immune dysregulation','免疫缺陷与免疫失调的遗传机制','https://www.uniklinik-freiburg.de/cci/forschung/bodo-grimbacher.html'],
 ['cunningham-rundles','Charlotte Cunningham-Rundles · Mount Sinai','United States','Primary immunodeficiency research and clinical immunology','原发性免疫缺陷研究与临床免疫','https://profiles.mountsinai.org/charlotte-cunningham-rundles'],
 ['tangye','Stuart Tangye Lab · Garvan','Australia','B-cell and T-cell biology, antibody responses and IEI','B/T 细胞生物学、抗体应答与 IEI','https://www.garvan.org.au/research/labs/immunology-and-immunodeficiency'],
 ['hambleton','Sophie Hambleton · Newcastle University','United Kingdom','Cellular and molecular causes of childhood IEI','儿童 IEI 的细胞与分子机制','https://www.ncl.ac.uk/medical-sciences/people/profile/sophiehambleton.html'],
 ['sullivan','Kathleen Sullivan Laboratory · CHOP','United States','Rare immunodeficiencies and immune dysregulation','罕见免疫缺陷与免疫调节异常','https://www.research.chop.edu/sullivan-laboratory'],
 ['casanova','Jean-Laurent Casanova · Rockefeller University','United States','Human genetics of susceptibility to infectious disease','感染易感性的人类遗传学','https://www.rockefeller.edu/research/2247-casanova-laboratory-2/'],
 ['meyts','Isabelle Meyts · KU Leuven','Belgium','Inborn Errors of Immunity research group','先天性免疫错误研究组','https://www.kuleuven.be/wieiswie/en/unit/regional/50546724'],
 ['cincinnati','Cincinnati Children’s · Immune Deficiencies and Dysregulation','United States','Specialist team with research and clinical-trial pathways','免疫缺陷和免疫失调专科团队及研究入口','https://www.cincinnatichildrens.org/service/i/immune-deficiency'],
 ['newcastle-hi','Haematopoiesis and Immunity Laboratory · Newcastle','United Kingdom','Dendritic-cell and monocyte immunodeficiencies','树突状细胞与单核细胞免疫缺陷','https://research.ncl.ac.uk/hilab/']
];
function expandedCards(lang){return expandedTeams.map(([id,name,country,en,zh,url])=>`<article class="panel" id="team-${id}"><small>${country} · ${lang==='zh'?'研究团队 / 专科团队':'Research / specialist team'}</small><h2>${name}</h2><p>${lang==='zh'?zh:en}</p><p><a href="${url}" target="_blank" rel="noopener">${lang==='zh'?'机构介绍与研究资料':'Institution profile & research'} ↗</a></p></article>`).join('');}
function bindDirectory(){const host=document.querySelector('[data-team-directory]');if(!host)return;const search=document.querySelector('#team-search');const country=document.querySelector('#team-country');const cards=[...host.querySelectorAll(':scope > article')];const update=()=>{let count=0;for(const card of cards){const text=card.textContent.toLowerCase();card.hidden=!(text.includes(search.value.toLowerCase().trim())&&(!country.value||text.includes(country.value.toLowerCase())));if(!card.hidden)count++;}document.querySelector('#team-count').textContent=count;};search.oninput=update;country.onchange=update;update();}

Object.assign(exports, {expandedTeams,expandedCards,bindDirectory});
}};
const cache={};
function require(id){if(cache[id])return cache[id];const exports=cache[id]={};modules[id](require,exports);return exports;}
try { require("src/main.js"); } catch(error) { console.error(error); const app=document.querySelector('#app'); if(app)app.textContent='The page could not load. Please keep index.html, src, assets and education together. 页面加载失败，请保留完整文件夹。'; }
})();
