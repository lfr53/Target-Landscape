export const selections = { clinician: [], researcher: [] };
export function caseValues(c) { return [c.diagnosis, ...c.features, ...c.immune, c.genetic]; }
export function selectCases(cases, filters) {
  return cases.filter(c => filters.every(f => caseValues(c).includes(f)));
}
export function distribution(cases, field) {
  const counts = new Map();
  cases.forEach(c => {
    const values = Array.isArray(c[field]) ? c[field] : [c[field] || 'not_recorded'];
    [...new Set(values.length ? values : ['not_recorded'])].forEach(v => counts.set(v, (counts.get(v) || 0) + 1));
  });
  return [...counts].sort((a,b) => b[1]-a[1]);
}
export function exploration(mode, cases, projects, labels, lang) {
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
export function bindExploration(mode, rerender) {
  document.querySelectorAll('[data-phenotype]').forEach(button => button.onclick = () => {
    const v = button.dataset.phenotype;
    selections[mode] = selections[mode].includes(v) ? selections[mode].filter(x=>x!==v) : [...selections[mode],v];
    rerender();
    document.querySelector(`[data-phenotype="${v}"]`)?.focus();
  });
  const reset = document.querySelector('[data-clear-filters]');
  if(reset) reset.onclick = () => { selections[mode] = []; rerender(); };
}
