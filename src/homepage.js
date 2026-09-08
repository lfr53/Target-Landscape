const copy = {
  en: {
    eyebrow: 'CVID & related immune conditions',
    title: 'Find similar cases.<br><span>Discover research.<br>Connect with expertise.</span>',
    intro: 'Explore shared symptoms and immune findings to find anonymous cases, relevant studies and teams working on similar questions.',
    cases: 'Explore similar cases', research: 'Explore research',
    people: 'Patients & families', clinicians: 'Clinicians', scientists: 'Researchers',
    pattern: 'Shared features', tags: ['CVID', 'Lung inflammation', 'Autoimmunity'],
    caption: 'Explore connections through symptoms and immune findings.',
    start: 'What would you like to explore?',
    roles: [
      ['Find people like me', 'Explore similar experiences, research involving people with your features, and supportive communities.', 'Start with my features', '#find'],
      ['Investigate a clinical pattern', 'Explore anonymous cases with similar findings and discover related studies and specialist teams.', 'Explore similar cases', '#clinicians'],
      ['Find groups and collaborators', 'Explore patient groups, family patterns and teams studying related questions.', 'Explore patient groups', '#researchers/explore']
    ],
    studies: 'Research around similar cases',
    studiesIntro: 'Discover the populations being studied, the questions being asked and the teams behind the work.',
    paths: [
      ['Natural history & family studies', 'Explore how conditions develop over time and how features appear within families.', '#research/nih-cvid-natural-history'],
      ['Registries & cohorts', 'Find groups of people with antibody deficiencies across participating centres.', '#research/esid-unpad'],
      ['Clinical trials', 'Explore intervention studies and the patient groups they investigate.', '#research/cincinnati-abcvild']
    ],
    view: 'Explore this research →', teams: 'Find research teams →',
    learn: 'Understand CVID', learnIntro: 'Explore explanations of immune mechanisms, symptoms, tests and everyday life with CVID.', learnCta: 'Visit the CVID learning hub →',
    nav: ['Home', 'CVID', 'Find People', 'Research', 'Researchers', 'Community']
  },
  zh: {
    eyebrow: 'CVID 与相关免疫疾病',
    title: '寻找相似病例，<br><span>发现相关研究，<br>连接专业团队。</span>',
    intro: '从症状和免疫检测特征出发，探索相似的匿名病例、相关研究，以及关注同类问题的临床医生和研究团队。',
    cases: '探索相似病例', research: '探索相关研究',
    people: '患者与家属', clinicians: '临床医生', scientists: '研究者',
    pattern: '共同的疾病特征', tags: ['CVID', '肺部炎症', '自身免疫'],
    caption: '通过症状与免疫检测特征，发现彼此之间的联系。',
    start: '你希望探索什么？',
    roles: [
      ['寻找与我相似的人', '了解相似经历、研究同类疾病特征的项目，以及可以提供支持的社群。', '从我的特征开始', '#find'],
      ['探索临床中的相似表现', '查找具有相似检测结果和症状的匿名病例，了解相关研究与专科团队。', '探索相似病例', '#clinicians'],
      ['寻找研究人群与合作团队', '探索患者群体、家族特征，以及正在研究相关问题的团队。', '探索患者群体', '#researchers/explore']
    ],
    studies: '看看相似病例正在如何被研究',
    studiesIntro: '了解研究关注哪些人群、希望回答什么问题，以及背后的研究团队。',
    paths: [
      ['自然病程与家族研究', '了解疾病如何随时间变化，以及相关特征如何出现在家庭成员中。', '#research/nih-cvid-natural-history'],
      ['登记系统与队列', '发现参与中心中具有不同抗体缺陷特征的患者群体。', '#research/esid-unpad'],
      ['临床试验', '了解干预性研究及其关注的患者群体。', '#research/cincinnati-abcvild']
    ],
    view: '了解这项研究 →', teams: '探索研究团队 →',
    learn: '了解 CVID', learnIntro: '阅读有关免疫机制、症状、检测，以及与 CVID 共同生活的科普内容。', learnCta: '进入 CVID 科普专区 →',
    nav: ['首页', '了解 CVID', '寻找相似病例', '研究', '研究团队', '社群']
  }
};
export function homepage(lang = 'en') {
  const c = copy[lang] || copy.en;
  const icons = ['◎', '✚', '⌕'];
  return `<section class="hero discovery-hero"><div><div class="eyebrow">${c.eyebrow}</div><h1>${c.title}</h1><p>${c.intro}</p><div class="hero-actions"><a class="button primary" href="#find">${c.cases}</a><a class="button secondary" href="#research">${c.research}</a></div></div>
    <div class="connection-scene"><svg class="connection-lines" viewBox="0 0 440 400" aria-hidden="true"><path d="M220 65 L85 305 L355 305 Z"/><path d="M220 65 V200 M85 305 L220 200 L355 305"/></svg>
      <a class="connection-person connection-patient" href="#find"><span>◎</span><strong>${c.people}</strong></a>
      <div class="connection-pattern"><small>${c.pattern}</small><div>${c.tags.map(t=>`<span class="tag">${t}</span>`).join('')}</div></div>
      <a class="connection-person connection-clinician" href="#clinicians"><span>✚</span><strong>${c.clinicians}</strong></a>
      <a class="connection-person connection-researcher" href="#researchers/explore"><span>⌕</span><strong>${c.scientists}</strong></a>
      <p class="connection-caption">${c.caption}</p></div></section>
    <section class="section"><h2>${c.start}</h2><div class="role-grid">${c.roles.map((r,i)=>`<article class="role-card"><span class="icon">${icons[i]}</span><small>${[c.people,c.clinicians,c.scientists][i]}</small><h3>${r[0]}</h3><p>${r[1]}</p><a class="button ${i?'secondary':'primary'}" href="${r[3]}">${r[2]}</a></article>`).join('')}</div></section>
    <section class="section"><div class="section-heading"><div><h2>${c.studies}</h2><p class="section-intro">${c.studiesIntro}</p></div><a class="back-link" href="#researchers">${c.teams}</a></div><div class="card-grid">${c.paths.map(r=>`<article class="panel"><h3>${r[0]}</h3><p>${r[1]}</p><a class="back-link" href="${r[2]}">${c.view}</a></article>`).join('')}</div></section>
    <section class="section"><div class="panel education-window"><div><h2>${c.learn}</h2><p>${c.learnIntro}</p></div><a class="button secondary" href="#cvid">${c.learnCta}</a></div></section>`;
}
export function localizeNavigation(lang) {
  const c = copy[lang] || copy.en;
  document.querySelectorAll('.site-header nav a').forEach((a,i) => a.textContent = c.nav[i]);
}
