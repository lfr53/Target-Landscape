/* Target Landscape — client.
 *
 * No framework and no build step: the whole interface is one file of plain
 * DOM code. That is a deliberate call for a tool whose value is the analysis
 * underneath — a toolchain here would be more moving parts to explain and
 * nothing a reader of the repo learns from.
 *
 * Two ideas shape the code:
 *
 * 1. **One filter state, every view.** Filters live in one object and every
 *    tab derives from the same filtered asset set. Filtering to antibodies and
 *    then opening the indication matrix shows the antibody matrix, not the
 *    unfiltered one. That is what makes this a database rather than a report
 *    with tabs.
 *
 * 2. **The mode reorders; it never hides.** A scientist needs the market view
 *    and an investor needs the mechanism, so Investor/Scientist changes which
 *    figures lead the summary and which tab opens first — and nothing else.
 *    Every number stays reachable in both modes, one click away.
 */

'use strict';

// ── State ────────────────────────────────────────────────────────────────

const state = {
  data: null,          // the landscape payload
  lens: localStorage_get('lens', 'investor'),
  libraryOpen: false,
  tab: localStorage_get('tab', null),
  filters: {},         // group -> Set of selected values
  sort: { key: 'max_phase', dir: -1 },
  trialsByNct: new Map(),
  suggestIndex: -1,
  suggestions: [],
};

function localStorage_get(key, fallback) {
  // Storage can throw outright in some embedding contexts, so every access is
  // guarded and the interface works identically when it returns nothing.
  try { return localStorage.getItem('tl.' + key) || fallback; } catch (e) { return fallback; }
}
function localStorage_set(key, value) {
  try { localStorage.setItem('tl.' + key, value); } catch (e) { /* non-essential */ }
}

const $ = (sel, root) => (root || document).querySelector(sel);
const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));

const PHASE_LABEL = { '-1': 'Unknown', 0: 'Preclinical', 1: 'Phase 1', 2: 'Phase 2', 3: 'Phase 3', 4: 'Approved' };
const PHASE_SHORT = { '-1': '·', 0: 'PC', 1: '1', 2: '2', 3: '3', 4: 'Appr' };

function el(tag, attrs, children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    // ARIA states are strings, not HTML boolean attributes. Passing true here
    // used to produce aria-selected="" and passing false dropped the
    // attribute, so the CSS rule .tab[aria-selected="true"] never matched and
    // the open tab was never highlighted -- the eight tabs looked identical
    // whichever one you were on.
    if (k.startsWith('aria-') && typeof v === 'boolean') {
      node.setAttribute(k, v ? 'true' : 'false');
      continue;
    }
    if (v === null || v === undefined || v === false) continue;
    if (k === 'class') node.className = v;
    else if (k === 'text') node.textContent = v;
    else if (k === 'html') node.innerHTML = v;
    else if (k.startsWith('on')) node.addEventListener(k.slice(2), v);
    else node.setAttribute(k, v === true ? '' : String(v));
  }
  for (const child of [].concat(children || [])) {
    if (child === null || child === undefined || child === false) continue;
    node.appendChild(typeof child === 'string' ? document.createTextNode(child) : child);
  }
  return node;
}

function clickableRow(onActivate, children) {
  // A <tr onclick> is invisible to a keyboard and to a screen reader. Rows
  // that open something get a tab stop, a role, and Enter/Space — the same
  // affordance a button would have.
  return el('tr', {
    tabindex: '0',
    role: 'button',
    onclick: onActivate,
    onkeydown: (event) => {
      if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); onActivate(); }
    },
  }, children);
}

function toast(message) {
  const node = $('#toast');
  node.textContent = message;
  node.hidden = false;
  clearTimeout(toast._t);
  toast._t = setTimeout(() => { node.hidden = true; }, 2600);
}

// ── Data access ──────────────────────────────────────────────────────────
//
// Every read goes through here so the same interface can run two ways: against
// the API, or fully static with the payloads inlined into the page (see
// scripts/make_static_demo.py). The static build is what makes a shareable,
// zero-infrastructure demo possible without a second implementation.

const STATIC = typeof window !== 'undefined' ? window.TL_STATIC : null;

async function api(path, options) {
  if (STATIC) return staticApi(path, options);
  const response = await fetch(path, options);
  return { ok: response.ok, status: response.status, json: () => response.json() };
}

function staticResult(status, body) {
  return { ok: status >= 200 && status < 300, status, json: async () => body };
}

// Which targets this copy actually holds. The single-file export inlines every
// record; the split export -- the one that scales past a handful -- ships each
// in its own file beside the page and fetches it when it is opened, so opening
// the site does not download a library the reader may never look at.
const BUILT = new Set(
  (STATIC && (STATIC.built || Object.keys(STATIC.targets || {}))) || []);

function isBuilt(symbol) {
  return BUILT.has(String(symbol || '').toUpperCase());
}

async function staticTarget(symbol) {
  if (STATIC.targets) return STATIC.targets[symbol] || null;
  try {
    const res = await fetch(
      (STATIC.data_base || 'targets/') + encodeURIComponent(symbol) + '.json');
    return res.ok ? await res.json() : null;
  } catch (err) {
    // A page opened from a file path cannot fetch its neighbours. That is what
    // the single-file export is for; this one is meant to be served.
    return null;
  }
}

async function staticApi(path) {
  if (path === '/api/library') {
    return staticResult(200, {
      targets: STATIC.library, count: STATIC.library.length, empty_hint: '',
      // Without this the landing page rendered its search box and its index and
      // nothing else: the six tiles come from the API, and the static build was
      // not carrying them.
      showcase: STATIC.showcase || null,
    });
  }
  let match = path.match(/^\/api\/target\/([^?]+)/);
  if (match) {
    const symbol = decodeURIComponent(match[1]).toUpperCase();
    const record = await staticTarget(symbol);
    return record
      ? staticResult(200, record)
      : staticResult(404, { detail: { symbol, message: 'Not built in this copy.' } });
  }
  match = path.match(/^\/api\/search\?q=([^&]*)/);
  if (match) {
    const q = decodeURIComponent(match[1]).toLowerCase();
    const pool = STATIC.index || STATIC.library;
    return staticResult(200, {
      results: pool
        .filter((r) => r.symbol.toLowerCase().includes(q)
          || (r.name || '').toLowerCase().includes(q)
          || (r.aliases || []).some((a) => a.toLowerCase().includes(q)))
        .slice(0, 12)
        .map((r) => ({ ...r, tier: isBuilt(r.symbol) ? 'curated' : 'index',
                       matched_on: r.symbol })),
    });
  }
  if (path.startsWith('/api/browse')) {
    const area = (path.match(/[?&]area=([^&]*)/) || [])[1];
    const pool = STATIC.index || STATIC.library;
    const decoded = area ? decodeURIComponent(area) : null;
    return staticResult(200, {
      targets: pool
        .filter((r) => !decoded || (r.areas || []).includes(decoded))
        .map((r) => ({ ...r, tier: isBuilt(r.symbol) ? 'curated' : 'index' })),
      areas: STATIC.areas || [],
      area: decoded,
      index_size: pool.length,
    });
  }
  return staticResult(404, {});
}

// ── Routing ──────────────────────────────────────────────────────────────

function showView(name) {
  // The compact search belongs in the bar everywhere except the landing page,
  // where the search box is the page.
  const top = $('#topsearch');
  if (top) top.hidden = (name === 'home');
  for (const view of $$('.view')) view.hidden = view.id !== 'view-' + name;
  window.scrollTo({ top: 0, behavior: 'instant' in window ? 'instant' : 'auto' });
}

// What the app is showing, kept independently of the address bar. The static
// export runs from a file:// path or inside a sandboxed frame, where the
// document has an opaque origin and the History API refuses every URL --
// including the page's own. Routing cannot depend on the URL changing.
let currentPath = null;

function navigate(path, replace) {
  currentPath = path;
  const url = STATIC ? '#' + path : path;
  try {
    if (replace) history.replaceState({}, '', url); else history.pushState({}, '', url);
  } catch (err) {
    // No history entry here, so back and forward will not work. Every link
    // still opens, which is the part that matters.
  }
  route();
}

async function route() {
  closeSuggestions();
  const path = currentPath
    || (STATIC ? ((location.hash || '').replace(/^#/, '') || '/') : location.pathname);

  const match = path.match(/^\/target\/([A-Za-z0-9-]+)\/?$/);
  if (match) {
    await openTarget(decodeURIComponent(match[1]));
    return;
  }

  document.title = 'Target Landscape';
  showView('home');
  loadLibrary();
}

// Back and forward. ``currentPath`` is what the app is showing; the browser
// moving through history is the one case where the address bar is ahead of it,
// so clear it and let ``route`` read the URL again. Both events are wired: the
// served build changes the pathname, the static build changes the hash.
window.addEventListener('popstate', () => { currentPath = null; route(); });
window.addEventListener('hashchange', () => { currentPath = null; route(); });

// ── The worked example ───────────────────────────────────────────────────
//
// Six tiles, on a real target, with that target's real numbers. A first-time
// visitor cannot picture a target page from a description of one, and an
// essay about methodology is the thing they skip — so the landing page shows
// the six answers instead of describing them, and each tile says which view
// carries it.
//
// The numbers come from the engine (analysis/showcase.py) rather than from
// copy, so they cannot drift away from what the target page shows.

function boldSegments(text) {
  // The engine marks a figure with **asterisks**. Not Markdown — one rule,
  // so the emphasis can be applied without returning HTML from the engine.
  const out = [];
  for (const [i, chunk] of String(text || '').split('**').entries()) {
    if (!chunk) continue;
    out.push(i % 2 ? el('b', { text: chunk }) : document.createTextNode(chunk));
  }
  return out;
}

// Two words, because the colour carries one distinction and no severity. The
// six are in the same order everywhere, so the grouping does the explaining.
function faceLegend() {
  const key = (face, label) => el('span', { class: 'face-key' }, [
    el('span', { class: 'face-dot face-' + face }),
    document.createTextNode(label),
  ]);
  return el('div', { class: 'face-legend' }, [
    key('science', 'Science'),
    key('business', 'Business'),
  ]);
}

function renderShowcase(showcase) {
  const host = $('#tiles');
  const note = $('#tiles-note');
  host.innerHTML = '';
  const tiles = (showcase || {}).tiles || [];
  if (!tiles.length) { note.hidden = true; return; }

  note.hidden = false;
  note.textContent = 'What a page holds — shown on ' + showcase.symbol;

  const tabLabel = (key) => (TABS.find((x) => x.key === key) || {}).label || key;
  for (const tile of tiles) {
    host.appendChild(el('button', {
      class: 'tile face-' + (tile.face || 'science'),
      // Clicking opens the showcase target on the view that tile describes,
      // so the routing is real rather than a picture of routing.
      onclick: () => {
        state.tab = tile.tabs[0];
        // Land on the view the tile describes. Without this every tile opened
        // the same screen -- the top of the target page -- and the six of them
        // were indistinguishable on arrival, which defeats the point of
        // showing six different answers.
        state.landOnTab = true;
        navigate('/target/' + showcase.symbol);
      },
    }, [
      el('div', { class: 'tile-h', text: tile.title }),
      el('div', { class: 'tile-body' }, boldSegments(tile.text)),
      el('div', { class: 'tile-where' },
        tile.tabs.map((key) => el('span', { class: 'tile-chip', text: tabLabel(key) }))),
    ]));
  }
  const legend = $('#tiles-legend');
  if (legend) { legend.innerHTML = ''; legend.appendChild(faceLegend()); }
}

// ── Library ──────────────────────────────────────────────────────────────
//
// The landing page is a browser, not a list of what happens to be
// precomputed: every target in the index is reachable without knowing its
// symbol, filtered by therapeutic area.

// The browse grid is driven by the area chips and nothing else. It used to
// carry a query too, set from the search box on every keystroke.
let browseState = { area: null };

async function loadLibrary() {
  const grid = $('#library-grid');
  if (grid.dataset.loaded) return;
  let payload;
  try {
    payload = await (await api('/api/library')).json();
  } catch (e) {
    grid.innerHTML = '';
    grid.appendChild(el('div', { class: 'empty', text: 'Could not reach the server.' }));
    return;
  }
  grid.dataset.loaded = '1';
  grid.setAttribute('aria-busy', 'false');
  grid.innerHTML = '';

  if (!payload.targets.length) {
    grid.appendChild(el('div', { class: 'empty' }, [
      el('p', { text: 'The library is empty — no targets have been precomputed yet.' }),
      el('p', { class: 'hint', style: 'margin-top:8px', text: payload.empty_hint }),
      el('p', { class: 'hint', style: 'margin-top:8px',
        text: 'You can still search for any target above; it will be built live.' }),
    ]));
    return;
  }

  renderShowcase(payload.showcase);

  // A short row under the search box, no wider than the box itself. Every
  // built target opens instantly, but offering all of them made a two-line
  // block that competed with the box it sits under; ordering them by
  // crowding put an empty page first as often as a full one.
  //
  // So these are chosen, not ranked. Each is a name the reader will
  // recognise, and each opens on a page with something in every tab: a
  // target whose asset table is empty is an honest page and a poor
  // advertisement. Anything not in the list still opens from the box.
  const PREFERRED = [
    'PDCD1',      // PD-1: the fullest page here, and the worked example above
    'ERBB2',      // HER2: known to everyone, and it proves the alias search
    'KRAS',       // the famous undruggable one, now drugged
    'CD19',       // CAR-T
    'CLDN18',     // zolbetuximab: a recent approval on a newer target
    'TNFSF15',    // TL1A: the most contested target in IBD right now
    'TNFRSF13C',  // BAFF-R
  ];
  const eg = $('#home-eg');
  eg.innerHTML = '';
  if (payload.targets.length) {
    eg.hidden = false;
    eg.appendChild(el('span', { text: 'Try' }));
    const built = new Map(payload.targets.map((r) => [r.symbol, r]));
    const chosen = PREFERRED.map((sym) => built.get(sym)).filter(Boolean);
    // Top up from the API's own order if the library does not hold them yet,
    // so a fresh install still shows something to click.
    for (const row of payload.targets) {
      if (chosen.length >= 7) break;
      if (!chosen.includes(row)) chosen.push(row);
    }
    for (const row of chosen.slice(0, 7)) {
      eg.appendChild(el('button', {
        class: 'eg', text: row.symbol, title: row.name || row.symbol,
        onclick: () => navigate('/target/' + row.symbol),
      }));
    }
  }

  loadBrowse();
}

async function loadBrowse() {
  let payload;
  try {
    payload = await (await api('/api/browse' + (browseState.area
      ? '?area=' + encodeURIComponent(browseState.area) : ''))).json();
  } catch (e) { return; }

  const chips = $('#area-chips');
  chips.innerHTML = '';
  chips.appendChild(el('span', {
    class: 'chip selectable' + (browseState.area ? '' : ' on'),
    onclick: () => { browseState.area = null; loadBrowse(); },
    text: 'All areas',
  }));
  for (const row of payload.areas || []) {
    chips.appendChild(el('span', {
      class: 'chip selectable' + (browseState.area === row.area ? ' on' : ''),
      onclick: () => { browseState.area = row.area; loadBrowse(); },
      text: row.area + ' · ' + row.n,
    }));
  }
  renderTargetGrid(payload.targets, payload.index_size);
}


// Which aliases to show, and in what order.
//
// HGNC lists every name a gene has ever carried, alphabetically, and the card
// showed the first three. MAP3K14 came out as "FTDCR1B · HS · HSNIK" -- three
// codes nobody says out loud -- while NIK, the only name a reader would
// recognise, sat fourth and was cut. The alias line exists so someone can
// recognise a gene they know under another name, so the list has to be sieved
// rather than truncated.
//
// Nothing is invented: every name shown is one HGNC lists. What is decided
// here is only which of them a person is likely to have typed.
const _CLONE = /^(MGC|FLJ|KIAA|DKFZ|LOC|RP\d|IMAGE|BC\d|DJ\d)/i;
const _SPECIES = /^(HS|HU|HUM|H)(?=[A-Z])/;

function rankedAliases(aliases, limit) {
  const list = (aliases || []).map((a) => String(a || '').trim()).filter(Boolean);
  const flat = (a) => a.toUpperCase().replace(/[^A-Z0-9]/g, '');

  const usable = list.filter((a) => {
    if (flat(a).length <= 2) return false;          // "HS" identifies nothing
    if (_CLONE.test(a)) return false;               // MGC129934, FLJ21930
    if (a.split(/\s+/).length >= 3) return false;   // a description, not a name
    if (/[()]/.test(a)) return false;               // p185(erbB2)
    if (/^[a-z]/.test(a)) return false;             // neu, c-ERB-2, hPD-1
    return true;
  });

  // One name, two spellings: BAFF-R and BAFFR. Keep the readable one.
  const byKey = new Map();
  for (const a of usable) {
    const key = flat(a);
    const held = byKey.get(key);
    if (!held || (/[^A-Za-z0-9]/.test(a) && !/[^A-Za-z0-9]/.test(held))) byKey.set(key, a);
  }
  let unique = [...byKey.values()];

  // One alias inside another: HSNIK is NIK with a species tag, so NIK stays;
  // TL1 is TL1A cut short, so TL1A stays.
  const keyOf = new Map(unique.map((a) => [a, flat(a)]));
  unique = unique.filter((a) => !unique.some((b) => {
    if (a === b) return false;
    const ka = keyOf.get(a), kb = keyOf.get(b);
    if (ka === kb) return false;
    if (ka.length > kb.length && ka.endsWith(kb) && _SPECIES.test(ka)) return true;
    if (ka.length < kb.length && kb.startsWith(ka)) return true;
    return false;
  }));

  const score = (a) => {
    const key = flat(a);
    let s = key.length <= 4 ? 14 : (key.length <= 6 ? 10 : 4);
    if (/^CD\d+$/i.test(key)) s -= 8;    // a catalogue code, not what people say
    if (/[^A-Za-z0-9]/.test(a)) s += 5;  // BAFF-R, PD-1, HER-2
    return s;
  };
  return unique.map((a, i) => ({ a, s: score(a), i }))
    .sort((x, y) => y.s - x.s || x.i - y.i)
    .slice(0, limit || 4).map((x) => x.a);
}

function renderTargetGrid(rows, indexSize) {
  // One grid, in the browse section, under the chips that filter it. It used
  // to be inserted after a separate curated grid that no longer exists, which
  // left the chips sitting above an empty section.
  const host = $('#library-grid');
  const list = rows;
  host.innerHTML = '';
  // Twenty-four to start with: enough to show what the index holds and to
  // give someone who does not know what to search something to click, without
  // turning the landing page into a directory.
  const shown = state.libraryOpen ? list.slice(0, 120) : list.slice(0, 24);
  for (const row of shown) {
    host.appendChild(el('button', {
      class: 'card plain', onclick: () => navigate('/target/' + row.symbol),
    }, [
      el('div', { class: 'card-sym' }, [
        document.createTextNode(row.symbol),
        row.tier === 'curated' ? el('span', { class: 'badge-instant', style: 'margin-left:7px', text: 'instant' }) : null,
      ]),
      el('div', { class: 'card-name', text: row.name || '' }),
      (row.aliases || []).length
        ? el('div', { class: 'card-alias', text: rankedAliases(row.aliases, 4).join(' · ') }) : null,
    ]));
  }
  if (!shown.length) {
    host.appendChild(el('div', { class: 'empty',
      text: 'The index is empty. Run scripts/seed_target_index.py.' }));
  }
  const total = indexSize ? indexSize.toLocaleString() : '';
  $('#browse-more').textContent = list.length > shown.length
    ? 'Showing ' + shown.length + ' of ' + list.length + '. These are the targets that come '
      + 'up in drug development'
      + (STATIC
        // The published copy ships a trimmed index, so "all human genes" would
        // be a claim it cannot back. It says what it actually carries.
        ? ', and the ' + list.length.toLocaleString() + ' here are searchable above. '
          + 'The ones marked instant are built in this copy.'
        : '; all ' + total + ' human genes are searchable above.')
    : (total ? total + ' human genes indexed. '
        + (STATIC
          ? 'This published copy carries the ' + STATIC.library.length + ' marked instant, '
            + 'each fully built. Any other one opens onto a page saying it is not built, '
            + 'rather than onto a guess. Run the project locally and it builds any of them '
            + 'from the same public APIs.'
          : 'Any of them can be opened. The ones marked instant are already built; the rest '
            + 'are built live on first view.') : '');
}

// ── Search ───────────────────────────────────────────────────────────────

// Two boxes, one behaviour: a compact one in the bar and the large one on
// the landing page. Whichever the reader is typing in becomes the active
// pair, so the suggestion list always opens under the box in use.
let searchInput = $('#search');
let suggestBox = $('#suggestions');
let searchTimer = null;

function bindSearch(input, box) {
  if (!input || !box) return;

  input.addEventListener('focus', () => { searchInput = input; suggestBox = box; });

  input.addEventListener('input', () => {
    searchInput = input;
    suggestBox = box;
    clearTimeout(searchTimer);
    const q = input.value.trim();
    // Typing no longer narrows the browse grid. The suggestion list under the
    // box is what answers a query; re-filtering the grid as well emptied the
    // section below -- type "MAP3K14" and the twenty-four cards became two --
    // so the part of the page that shows what the library holds disappeared
    // exactly when someone was looking for something in it.
    if (q.length < 1) { closeSuggestions(); return; }
    // Debounced: the live half of this hits Open Targets, and one request per
    // keystroke is rude to an API this tool depends on.
    searchTimer = setTimeout(() => runSearch(q), 220);
  });

  input.addEventListener('keydown', (event) => {
    searchInput = input;
    suggestBox = box;
    if (event.key === 'Escape') { closeSuggestions(); input.blur(); return; }
    if (!state.suggestions.length) {
      if (event.key === 'Enter' && input.value.trim()) {
        navigate('/target/' + input.value.trim().toUpperCase());
        closeSuggestions();
      }
      return;
    }
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault();
      const delta = event.key === 'ArrowDown' ? 1 : -1;
      state.suggestIndex = (state.suggestIndex + delta + state.suggestions.length) % state.suggestions.length;
      paintSuggestions();
    } else if (event.key === 'Enter') {
      event.preventDefault();
      const pick = state.suggestions[Math.max(0, state.suggestIndex)];
      if (pick) { navigate('/target/' + pick.symbol); closeSuggestions(); }
    }
  });
}

const libraryToggle = $('#library-toggle');
if (libraryToggle) {
  libraryToggle.addEventListener('click', () => {
    state.libraryOpen = !state.libraryOpen;
    libraryToggle.textContent = state.libraryOpen ? 'Show less' : 'Show all';
    loadBrowse();
  });
}

for (const button of $$('.eg')) {
  button.addEventListener('click', () => navigate('/target/' + button.dataset.symbol));
}

bindSearch($('#search'), $('#suggestions'));
bindSearch($('#home-search'), $('#home-suggestions'));

document.addEventListener('click', (event) => {
  if (!event.target.closest('.searchbox')) closeSuggestions();
});

async function runSearch(q) {
  try {
    const payload = await (await api('/api/search?q=' + encodeURIComponent(q))).json();
    state.suggestions = payload.results || [];
  } catch (e) {
    state.suggestions = [];
  }
  // Always offer the raw text: a valid symbol the search endpoint does not
  // rank is still buildable, and refusing to try would be worse than a miss.
  // Offer the raw text only when nothing already covers it — including as an
  // alias, so typing "BAFF" does not offer a bare "BAFF" underneath TNFSF13B.
  const typed = q.toUpperCase();
  const covered = state.suggestions.some((r) =>
    r.symbol === typed
    || (r.matched_on || '').toUpperCase() === typed
    || (r.aliases || []).some((a) => a.toUpperCase() === typed));
  if (!STATIC && /^[A-Z0-9-]{2,32}$/.test(typed) && !covered) {
    state.suggestions.push({ symbol: typed, name: 'Look this up directly', tier: 'live' });
  }
  state.suggestIndex = 0;
  paintSuggestions();
}

function paintSuggestions() {
  if (!state.suggestions.length) { closeSuggestions(); return; }
  suggestBox.innerHTML = '';
  state.suggestions.forEach((row, i) => {
    suggestBox.appendChild(el('div', {
      class: 'sg', role: 'option', 'aria-selected': i === state.suggestIndex,
      onmousedown: (e) => { e.preventDefault(); navigate('/target/' + row.symbol); closeSuggestions(); },
    }, [
      el('span', { class: 'sg-sym', text: row.symbol }),
      // When the hit came from an alias, show it: someone who typed HER2
      // needs to see that ERBB2 is the same thing, not wonder why the
      // symbol changed under them.
      (row.matched_on && row.matched_on !== row.symbol)
        ? el('span', { class: 'sg-alias', text: '= ' + row.matched_on }) : null,
      el('span', { class: 'sg-name', text: row.name || '' }),
      el('span', { class: 'sg-tier ' + (row.tier || ''),
        // "build" and "live" are promises. The published copy is a set of
        // files and cannot keep them, so there it says what is true instead.
        text: row.tier === 'curated' ? 'instant'
          : (STATIC ? 'not built' : (row.tier === 'index' ? 'build' : 'live')) }),
    ]));
  });
  suggestBox.hidden = false;
  searchInput.setAttribute('aria-expanded', 'true');
}

function closeSuggestions() {
  // Both boxes: the reader may have switched between them.
  for (const box of $$('.suggestions')) box.hidden = true;
  for (const input of [$('#search'), $('#home-search')]) {
    if (input) input.setAttribute('aria-expanded', 'false');
  }
  state.suggestions = [];
  state.suggestIndex = -1;
}

// ── Loading a target ─────────────────────────────────────────────────────

async function openTarget(symbol, force) {
  showView('building');
  $('#build-symbol').textContent = symbol;
  $('#build-error').hidden = true;
  $('#build-label').textContent = force ? 'Rebuilding…' : 'Looking up…';
  $('#build-fill').style.width = '0%';
  $('#build-stages').innerHTML = '';

  if (!force) {
    const res = await api('/api/target/' + encodeURIComponent(symbol));
    if (res.ok) { renderTarget(await res.json()); return; }
    if (res.status === 400) { buildFailed('That does not look like a gene symbol.'); return; }
  }

  if (STATIC) {
    buildFailed('Not built in this published copy. It carries the ' + STATIC.library.length
      + ' targets in the library below, each one complete. The engine builds any human gene '
      + 'from Open Targets, ChEMBL and ClinicalTrials.gov in about half a minute — but it '
      + 'needs a server to do that, and this copy is a single file.');
    return;
  }

  const started = await (await fetch('/api/build/' + encodeURIComponent(symbol) + (force ? '?force=true' : ''), { method: 'POST' })).json();
  if (started.status === 'ready') {
    const res = await api('/api/target/' + encodeURIComponent(symbol));
    if (res.ok) { renderTarget(await res.json()); return; }
  }
  pollJob(started.job.id, symbol);
}

function paintStages(job) {
  const list = $('#build-stages');
  if (!list.dataset.built) {
    list.dataset.built = '1';
    for (let i = 0; i < job.total; i++) list.appendChild(el('li', { 'data-i': i, text: '' }));
  }
  $$('#build-stages li').forEach((node, i) => {
    node.className = i < job.index ? 'done' : (i === job.index ? 'active' : '');
    if (i === job.index) node.textContent = job.label;
    else if (!node.textContent) node.textContent = '…';
  });
}

async function pollJob(jobId, symbol) {
  const list = $('#build-stages');
  list.dataset.built = '';
  list.innerHTML = '';
  for (let attempt = 0; attempt < 400; attempt++) {
    let job;
    try {
      job = await (await fetch('/api/job/' + jobId)).json();
    } catch (e) {
      buildFailed('Lost contact with the server.');
      return;
    }
    if (job.detail) { buildFailed('That build expired. Try again.'); return; }
    $('#build-label').textContent = job.label || 'Working…';
    $('#build-fill').style.width = Math.round(job.progress * 100) + '%';
    paintStages(job);

    if (job.status === 'done') {
      const res = await api('/api/target/' + encodeURIComponent(symbol));
      if (res.ok) { renderTarget(await res.json()); return; }
      buildFailed('Built, but could not be loaded back.');
      return;
    }
    if (job.status === 'error') { buildFailed(job.error); return; }
    await new Promise((r) => setTimeout(r, 900));
  }
  buildFailed('This is taking much longer than expected. The APIs may be slow right now.');
}

function buildFailed(message) {
  $('#build-label').textContent = 'Could not build this target';
  const box = $('#build-error');
  box.textContent = message;
  box.hidden = false;
}

$('#build-cancel').addEventListener('click', () => navigate('/'));

// ── Lens ─────────────────────────────────────────────────────────────────

for (const button of $$('.lens-btn')) {
  button.addEventListener('click', () => {
    state.lens = button.dataset.lens;
    localStorage_set('lens', state.lens);
    for (const other of $$('.lens-btn')) other.setAttribute('aria-pressed', other === button);
    if (state.data) { renderTabs(); }
  });
}
for (const button of $$('.lens-btn')) button.setAttribute('aria-pressed', button.dataset.lens === state.lens);


// ── Render: target ───────────────────────────────────────────────────────



// ── Taking the data away ─────────────────────────────────────────────────
//
// A reader who has narrowed the asset table to Phase 3 antibodies wants those
// rows in a spreadsheet, not a screenshot. Every table on the page can leave
// as CSV, and what leaves is what the filters are showing -- exporting the
// unfiltered set would hand back something the reader never asked for.
//
// One file, with the chosen tables one after another, each under its own
// heading. Excel opens it; a person reads it; and the header block carries the
// target, the date, the filters in force and the sources, so a figure pasted
// into a memo can still be traced back.

function csvCell(value) {
  if (value === null || value === undefined) return '';
  let text = Array.isArray(value) ? value.join('; ') : String(value);
  text = text.replace(/\r?\n/g, ' ').trim();
  // A leading =, +, - or @ makes Excel treat the cell as a formula.
  if (/^[=+\-@]/.test(text)) text = "'" + text;
  return /[",;]/.test(text) ? '"' + text.replace(/"/g, '""') + '"' : text;
}

function csvBlock(title, columns, rows) {
  if (!rows.length) return '';
  const out = ['# ' + title + ' (' + rows.length + ' rows)'];
  out.push(columns.map((c) => csvCell(c.label)).join(','));
  for (const row of rows) out.push(columns.map((c) => csvCell(c.get(row))).join(','));
  return out.join('\n') + '\n';
}

// One definition per table: what a row is, and which columns are worth taking.
const EXPORTS = [
  {
    key: 'assets', label: 'Assets',
    rows: () => filteredAssets(),
    columns: [
      { label: 'Asset', get: (a) => a.name },
      { label: 'Sponsor', get: (a) => a.sponsor },
      { label: 'Highest phase', get: (a) => PHASE_LABEL[a.max_phase] || 'Unknown' },
      { label: 'Modality', get: (a) => a.modality },
      { label: 'Mechanism class', get: (a) => a.mechanism_class },
      { label: 'Mechanism (source text)', get: (a) => a.mechanism_text },
      { label: 'First approval', get: (a) => a.first_approval },
      { label: 'Withdrawn', get: (a) => (a.withdrawn ? 'yes' : '') },
      { label: 'Still active', get: (a) => (a.is_active ? 'yes' : 'no') },
      { label: 'Indications', get: (a) => (a.indications || []).slice(0, 12) },
      { label: 'Trials', get: (a) => a.trials },
      { label: 'ChEMBL id', get: (a) => a.chembl_id },
    ],
  },
  {
    key: 'stops', label: 'Terminations',
    rows: () => stopsOf(filteredAssets()),
    columns: [
      { label: 'NCT', get: (t) => t.nct_id },
      { label: 'Title', get: (t) => t.title },
      { label: 'Sponsor', get: (t) => t.sponsor },
      { label: 'Phase', get: (t) => PHASE_LABEL[t.phase] || 'Unknown' },
      { label: 'Status', get: (t) => t.status },
      { label: 'Why stopped (sponsor text)', get: (t) => t.why_stopped },
      { label: 'Classified as', get: (t) => t.failure_class },
      { label: 'Why classified that way', get: (t) => t.failure_rationale },
      { label: 'Conditions', get: (t) => t.conditions },
      { label: 'URL', get: (t) => 'https://clinicaltrials.gov/study/' + t.nct_id },
    ],
  },
  {
    key: 'trials', label: 'Trials',
    rows: () => trialsOf(filteredAssets()),
    columns: [
      { label: 'NCT', get: (t) => t.nct_id },
      { label: 'Title', get: (t) => t.title },
      { label: 'Sponsor', get: (t) => t.sponsor },
      { label: 'Phase', get: (t) => PHASE_LABEL[t.phase] || 'Unknown' },
      { label: 'Status', get: (t) => t.status },
      { label: 'Allocation', get: (t) => t.allocation },
      { label: 'Masking', get: (t) => t.masking },
      { label: 'Enrolment', get: (t) => t.enrollment },
      { label: 'Primary outcome', get: (t) => t.primary_outcomes },
      { label: 'What a result could support', get: (t) => t.evidence_level },
      { label: 'Primary completion', get: (t) => t.completion_date },
      { label: 'Date is', get: (t) => (t.completion_date_type === 'ACTUAL' ? 'actual' : 'sponsor estimate') },
      { label: 'Countries', get: (t) => t.countries },
      { label: 'Interventions', get: (t) => t.interventions },
      { label: 'URL', get: (t) => 'https://clinicaltrials.gov/study/' + t.nct_id },
    ],
  },
  {
    key: 'licensing', label: 'Licensing signals',
    rows: () => licensingRows(filteredAssets()),
    columns: [
      { label: 'Asset', get: (r) => r.asset },
      { label: 'Sponsor', get: (r) => r.sponsor },
      { label: 'Highest phase', get: (r) => PHASE_LABEL[r.max_phase] || 'Unknown' },
      { label: 'Read', get: (r) => r.read },
      { label: 'Signals', get: (r) => (r.signals || []).map((s) => s.label) },
      { label: 'Evidence', get: (r) => (r.signals || []).map((s) => s.detail) },
    ],
  },
  {
    key: 'deals', label: 'Deal comparables',
    rows: () => ((state.data.licensing || {}).deals || {}).deals || [],
    columns: [
      { label: 'Date', get: (d) => d.date },
      { label: 'Acquirer', get: (d) => d.acquirer },
      { label: 'Counterparty', get: (d) => d.target_company },
      { label: 'Asset', get: (d) => d.asset },
      { label: 'Mechanism', get: (d) => d.mechanism },
      { label: 'Type', get: (d) => d.deal_type },
      { label: 'Stage at deal', get: (d) => d.stage_at_deal },
      { label: 'Upfront $m', get: (d) => d.upfront_usd_m },
      { label: 'Total $m', get: (d) => d.total_usd_m },
      { label: 'Territory', get: (d) => d.territory },
      { label: 'Source', get: (d) => d.source_url },
    ],
  },
  {
    key: 'mechanisms', label: 'Mechanism classes',
    rows: () => clustersOf(filteredAssets()).map((c) => ({
      label: c.label, n: c.list.length, best: c.best,
      names: c.list.map((a) => a.name),
    })),
    columns: [
      { label: 'Mechanism class', get: (c) => c.label },
      { label: 'Assets', get: (c) => c.n },
      { label: 'Furthest phase', get: (c) => PHASE_LABEL[c.best] || 'Unknown' },
      { label: 'Molecules', get: (c) => c.names },
    ],
  },
  {
    key: 'indications', label: 'Indications',
    rows: () => matrixOf(filteredAssets()).rows,
    columns: [
      { label: 'Indication', get: (r) => r.indication },
      // matrixOf returns n and cells; n_assets and max_phase were the engine's
      // field names, and the download printed two empty columns.
      { label: 'Programmes', get: (r) => r.n },
      { label: 'Furthest phase',
        get: (r) => PHASE_LABEL[Math.max.apply(null, r.cells)] || 'Unknown' },
    ],
  },
  {
    key: 'whitespace', label: 'Gaps',
    rows: () => state.data.whitespace || [],
    columns: [
      { label: 'Indication', get: (r) => r.disease },
      { label: 'Association score', get: (r) => r.association_score },
      { label: 'Genetic evidence', get: (r) => r.genetic_score },
      { label: 'Furthest reached', get: (r) => (r.highest_phase >= 0 ? PHASE_LABEL[r.highest_phase] : 'None in clinic') },
      { label: 'EFO id', get: (r) => r.disease_id },
    ],
  },
  {
    key: 'reading', label: 'References',
    rows: () => (state.data.literature || {}).papers || [],
    columns: [
      { label: 'Title', get: (p) => p.title },
      { label: 'Journal', get: (p) => p.journal },
      { label: 'Year', get: (p) => p.year },
      { label: 'PMID', get: (p) => p.pmid },
      { label: 'URL', get: (p) => (p.pmid ? 'https://europepmc.org/article/MED/' + p.pmid : '') },
    ],
  },
];

function activeFilterSummary() {
  const parts = [];
  for (const [key, values] of Object.entries(state.filters || {})) {
    const list = [...(values || [])];
    if (list.length) parts.push(key + ': ' + list.join(' / '));
  }
  return parts.join('; ');
}

function buildExportCsv(keys) {
  const target = (state.data.target || {});
  const filters = activeFilterSummary();
  const head = [
    '# ' + (target.symbol || '') + ' - ' + (target.name || ''),
    '# Target Landscape export, ' + new Date().toISOString().slice(0, 10),
    '# Record generated ' + (state.data.generated || 'unknown'),
    '# Filters in force: ' + (filters || 'none - the full table'),
    '# Sources: Open Targets Platform (CC0); ChEMBL (CC BY-SA 3.0); '
      + 'ClinicalTrials.gov (US Government public domain); UniProt (CC BY 4.0). '
      + 'Deal rows are hand-entered from the parties\' own releases; each carries its source.',
    '',
  ];
  const blocks = EXPORTS
    .filter((e) => keys.includes(e.key))
    .map((e) => {
      let rows = [];
      try { rows = e.rows() || []; } catch (err) { rows = []; }
      return csvBlock(e.label, e.columns, rows);
    })
    .filter(Boolean);
  if (!blocks.length) return null;
  return head.join('\n') + '\n' + blocks.join('\n');
}

function renderExportPanel() {
  const host = $('#export-choices');
  if (!host) return;
  host.innerHTML = '';
  for (const entry of EXPORTS) {
    let count = 0;
    try { count = (entry.rows() || []).length; } catch (err) { count = 0; }
    const id = 'exp-' + entry.key;
    const box = el('label', { class: 'export-choice' + (count ? '' : ' empty') }, [
      el('input', {
        type: 'checkbox', id, 'data-export': entry.key,
        checked: count > 0 && ['assets', 'stops', 'trials'].includes(entry.key),
        disabled: !count,
        onchange: () => updateExportNote(),
      }),
      el('span', { text: entry.label }),
      el('span', { class: 'export-count', text: count ? String(count) : 'none' }),
    ]);
    host.appendChild(box);
  }
  updateExportNote();
}

function chosenExports() {
  return $$('#export-choices input:checked').map((i) => i.dataset.export);
}

function updateExportNote() {
  const note = $('#export-note');
  if (!note) return;
  const filters = activeFilterSummary();
  const total = chosenExports().reduce((sum, key) => {
    const entry = EXPORTS.find((e) => e.key === key);
    try { return sum + (entry.rows() || []).length; } catch (err) { return sum; }
  }, 0);
  note.textContent = total
    ? total + ' rows, as one CSV. ' + (filters
        ? 'Filtered: ' + filters + '.'
        : 'No filters set, so this is the whole table.')
    : 'Nothing selected.';
  const button = $('#t-export-csv');
  if (button) button.disabled = !total;
}

function downloadCsv() {
  const keys = chosenExports();
  const text = buildExportCsv(keys);
  if (!text) return;
  const symbol = (state.data.target || {}).symbol || 'target';
  const name = symbol + '_target-landscape_' + new Date().toISOString().slice(0, 10) + '.csv';
  // The BOM is what makes Excel read UTF-8 rather than the machine's code page,
  // which is the difference between "Sjogren's" and mojibake.
  const blob = new Blob(['\ufeff' + text], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = el('a', { href: url, download: name });
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  toast('Downloaded ' + name);
}

function bindExport() {
  const open = $('#t-export-open');
  const panel = $('#export-panel');
  if (!open || !panel) return;
  open.onclick = () => {
    const show = panel.hidden;
    if (show) renderExportPanel();
    panel.hidden = !show;
    open.setAttribute('aria-expanded', show ? 'true' : 'false');
  };
  const close = $('#t-export-close');
  if (close) close.onclick = () => { panel.hidden = true; open.setAttribute('aria-expanded', 'false'); };
  const go = $('#t-export-csv');
  if (go) go.onclick = downloadCsv;
}

function renderTarget(payload) {
  state.data = payload;
  state.filters = {};
  state.sort = { key: 'max_phase', dir: -1 };
  state.trialsByNct = new Map(payload.trials.map((t) => [t.nct_id, t]));

  const target = payload.target;
  document.title = target.symbol + ' — Target Landscape';
  $('#t-symbol').textContent = target.symbol;
  $('#t-name').textContent = target.name || '';
  $('#t-ensembl').textContent = target.ensembl_id || '';

  const meta = payload.meta || {};
  const tier = $('#t-tier');
  tier.className = 'tier ' + (meta.tier || '');
  tier.textContent = meta.tier === 'curated'
    ? 'curated · ' + (payload.generated || '')
    : (meta.tier === 'cached' ? 'built ' + fmtAge(meta.age_days) : 'live');

  // Open Targets abbreviates tractability modalities. Expanding them costs
  // nothing and the abbreviation means nothing to most readers.
  const MODALITY_NAME = { SM: 'Small molecule', AB: 'Antibody', PR: 'Protein',
    OC: 'Other clinical', PROTAC: 'PROTAC' };
  const tract = $('#t-tract');
  tract.innerHTML = '';
  for (const [modality, buckets] of Object.entries(target.tractability || {})) {
    const strong = buckets.some((b) => /high conf|approved drug|advanced|clinical/i.test(b));
    tract.appendChild(el('span', {
      class: 'chip' + (strong ? ' strong' : ''),
      title: buckets.join(' · '),
      text: (MODALITY_NAME[modality] || modality) + (strong ? ' · tractable' : ' · predicted'),
    }));
  }
  if (!Object.keys(target.tractability || {}).length) {
    tract.appendChild(el('span', { class: 'chip', text: 'No tractability data' }));
  }

  const warnings = $('#t-warnings');
  if (payload.warnings && payload.warnings.length) {
    warnings.hidden = false;
    warnings.innerHTML = '';
    warnings.appendChild(el('strong', { text: 'Run warnings. ' }));
    warnings.appendChild(document.createTextNode(payload.warnings.join(' ')));
  } else {
    warnings.hidden = true;
  }

  $('#t-export-html').href = '/api/export/' + target.symbol + '.html';
  $('#t-export-md').href = '/api/export/' + target.symbol + '.md';
  $('#t-export-md').setAttribute('download', target.symbol + '_landscape.md');
  $('#t-rebuild').onclick = () => openTarget(target.symbol, true);
  if (STATIC) {
    $('#t-rebuild').hidden = true;
    $('#t-export-html').hidden = true;
    $('#t-export-md').hidden = true;
  }

  const c = payload.crowding || {};
  $('#t-method').innerHTML =
    '<strong>Method.</strong> Density is a phase-weighted count of active programmes — '
    + escapeHtml(Object.entries(c.weights_used || {}).map(([k, v]) => k + ' ' + v).join(', '))
    + '. Bands: ' + escapeHtml((c.bands_used || []).map((b) => b.verdict + ' ≥ ' + b.from).join(', '))
    + '. These are this tool’s own convention, not a measurement.<br>'
    + '<strong>Data.</strong> Open Targets Platform (CC0) · ChEMBL (CC BY-SA 3.0) · '
    + 'ClinicalTrials.gov (US Government public domain).'
    // How this record was assembled. These used to be pushed into the warning
    // box, where "1 trial did not name this target" read as a fault on a page
    // where nothing had gone wrong.
    + ((payload.notes && payload.notes.length)
        ? '<br><strong>How this was assembled.</strong> '
          + escapeHtml(payload.notes.join(' '))
        : '');

  bindExport();
  const exportPanel = $('#export-panel');
  if (exportPanel) exportPanel.hidden = true;

  renderIntro();
  renderCard();
  renderLensBlock();
  renderFilters();
  renderTabs();
  showView('target');

  if (state.landOnTab) {
    state.landOnTab = false;
    // After the view is visible, not before: scrollIntoView on a hidden
    // element does nothing. The header stays reachable one scroll up rather
    // than being skipped, so the reader still sees which target they opened.
    requestAnimationFrame(() => {
      const panel = document.querySelector('.workspace');
      if (panel) panel.scrollIntoView({ block: 'start', behavior: 'auto' });
    });
  }
}

function fmtAge(days) {
  if (days === undefined || days === null) return 'recently';
  if (days < 1) return 'today';
  if (days < 2) return 'yesterday';
  return Math.round(days) + ' days ago';
}

function escapeHtml(text) {
  return String(text === null || text === undefined ? '' : text)
    .replace(/[&<>"']/g, (ch) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
}

// ── Under the symbol: intro, then two blocks ─────────────────────────────
//
// A short introduction to the molecule, then a split: the left block changes
// with the reading mode, the right card holds the facts that do not.
//
// The mode reorders, it never hides. An investor opening this page gets the
// six questions first and the mechanism one tab away; a scientist gets the
// mechanism first and the six questions one tab away. Both are on the page.

// The card carries what the target *is*. Development is in the six lines and
// the tables; the germline disease is in the intro paragraph, labelled. Both
// were on the card once and it ran a third longer than the block beside it.
const FACT_ORDER = ['class', 'location', 'topology', 'domain'];

function renderIntro() {
  const host = $('#t-intro');
  const header = state.data.header || {};
  const rows = header.facts || [];
  const mech = header.mechanism || {};
  const fn = rows.find((r) => r.key === 'function');
  const genetics = rows.find((r) => r.key === 'genetics');

  host.innerHTML = '';
  const text = mech.text || (fn && fn.value) || '';
  if (!text) { host.hidden = true; return; }
  host.hidden = false;

  host.appendChild(document.createTextNode(text));
  for (const pmid of (mech.pmids || (fn && fn.pmids) || []).slice(0, 4)) {
    host.appendChild(el('a', {
      class: 'cite', href: 'https://europepmc.org/article/MED/' + pmid,
      target: '_blank', rel: 'noopener', title: 'PubMed ' + pmid, text: pmid,
    }));
  }
  // The germline disease closes the paragraph, labelled. It is one clause and
  // it does not deserve its own row on the card, where a reader scanning
  // labels would take it for the indication.
  if (genetics) {
    host.appendChild(document.createTextNode(
      ' Germline variants cause ' + genetics.value + ' — genetic validation of the '
      + 'target, not an indication being developed against it.'));
    for (const pmid of (genetics.pmids || []).slice(0, 2)) {
      host.appendChild(el('a', {
        class: 'cite', href: 'https://europepmc.org/article/MED/' + pmid,
        target: '_blank', rel: 'noopener', title: 'PubMed ' + pmid, text: pmid,
      }));
    }
  }
}

// The card: what the target is, independent of who is reading.
function renderCard() {
  const host = $('#t-card');
  const header = state.data.header || {};
  const target = state.data.target || {};
  const rows = (header.facts || []).filter((r) => FACT_ORDER.includes(r.key));
  host.innerHTML = '';

  host.appendChild(el('div', { class: 'card-label', text: 'The molecule' }));
  const list = el('dl', { class: 'facts' });

  const add = (label, value, note) => {
    list.appendChild(el('dt', { class: 'fact-k', text: label }));
    const dd = el('dd', { class: 'fact-v' }, [document.createTextNode(value)]);
    if (note) dd.appendChild(el('div', { class: 'fact-note', text: note }));
    list.appendChild(dd);
  };

  if (target.name) add('Protein', target.name);
  for (const key of FACT_ORDER) {
    const row = rows.find((r) => r.key === key);
    if (row) add(row.label, row.value, row.note);
  }
  if (target.ensembl_id) add('Ensembl', target.ensembl_id);
  host.appendChild(list);

  const tract = Object.entries(target.tractability || {});
  if (tract.length) {
    host.appendChild(el('div', { class: 'card-label', style: 'margin-top:16px',
                                 text: 'Tractability' }));
    const chips = el('div', { class: 'chips' });
    const MODALITY_NAME = { SM: 'Small molecule', AB: 'Antibody', PR: 'Protein',
      OC: 'Other clinical', PROTAC: 'PROTAC' };
    for (const [modality, buckets] of tract) {
      const strong = buckets.some((b) => /high conf|approved drug|advanced|clinical/i.test(b));
      chips.appendChild(el('span', {
        class: 'chip' + (strong ? ' strong' : ''), title: buckets.join(' · '),
        text: MODALITY_NAME[modality] || modality,
      }));
    }
    host.appendChild(chips);
  }

  if (header.curated_source) {
    const src = el('p', { class: 'card-src' });
    src.appendChild(document.createTextNode('Protein facts from UniProt' + ' '));
    src.appendChild(el('a', { href: header.url || '#', target: '_blank', rel: 'noopener',
                              text: header.accession || 'UniProt' }));
    host.appendChild(src);
  }
}

// Both modes open the same way. The reading mode reorders the tabs below —
// it does not change what a reader meets first, because the six questions are
// the ones anyone arrives with.
function renderLensBlock() {
  const host = $('#t-lensblock');
  host.innerHTML = '';
  renderRead(host);
}

// ── Where this target sits ───────────────────────────────────────────────
//
// Four lines, and the last one is the reason the block exists. A description
// of a pathway is something a reader can get anywhere; what they cannot get
// anywhere is the same sentence with the neighbouring targets turned into
// pages they can open. That is the whole product claim in four lines: the
// science and the commercial picture normally live in different databases.
//
// The first three are hand-written with a citation, in data/pathways.csv. The
// last two are computed, because a hand-written answer to "which of these do
// we hold a page for" and "what has actually been approved here" goes stale
// the moment the library or the asset table changes.
function renderPathway(host) {
  const p = state.data.pathway || {};
  if (!p.pathway) return;

  const block = el('section', { class: 'pathway' });
  block.appendChild(el('div', { class: 'read-label', text: 'Where this target sits' }));
  const list = el('ol', { class: 'pathway-lines' });

  const line = (label, nodes) => {
    const li = el('li', {}, [el('span', { class: 'pw-k', text: label })]);
    const body = el('span', { class: 'pw-v' });
    for (const node of nodes) body.appendChild(node);
    li.appendChild(body);
    return li;
  };

  list.appendChild(line('Pathway', [
    el('b', { text: p.pathway }),
    document.createTextNode(p.does ? ' — ' + p.does : ''),
  ]));
  if (p.role) list.appendChild(line('Its role', [document.createTextNode(p.role)]));

  const neighbours = p.neighbours || [];
  if (neighbours.length) {
    const nodes = [];
    neighbours.forEach((n, i) => {
      if (i) nodes.push(document.createTextNode(' · '));
      nodes.push(n.in_library
        ? el('button', { class: 'link', text: n.symbol,
            onclick: () => navigate('/target/' + n.symbol) })
        : el('a', { class: 'pw-out', target: '_blank', rel: 'noopener', text: n.symbol,
            href: 'https://platform.opentargets.org/search?q=' + encodeURIComponent(n.symbol) }));
    });
    nodes.push(el('span', { class: 'hint', text:
      '  in bold: a page on this site. The rest open in Open Targets.' }));
    list.appendChild(line('Drugged on the same pathway', nodes));
  }

  const approved = p.approved_here || [];
  const unnamed = p.approved_unclassified || 0;
  let worked;
  if (!approved.length && !unnamed) {
    worked = 'Nothing on this target has reached approval yet.';
  } else if (!approved.length) {
    worked = unnamed + ' approved programme' + (unnamed === 1 ? '' : 's')
      + ', none of which the record classifies by mechanism.';
  } else {
    worked = approved.map(shortMechanism).join(' · ')
      + ' — every other approach here is still in development'
      + (unnamed ? '; ' + unnamed + ' approved programme'
          + (unnamed === 1 ? ' carries' : 's carry') + ' no mechanism in the record' : '')
      + '.';
  }
  list.appendChild(line('What has worked here', [document.createTextNode(worked)]));

  block.appendChild(list);
  const foot = el('p', { class: 'hint', style: 'margin:8px 0 0' }, [
    document.createTextNode((p.note || '') + ' '),
    p.source_url
      ? el('a', { href: p.source_url, target: '_blank', rel: 'noopener', text: 'source' })
      : null,
  ]);
  block.appendChild(foot);
  host.appendChild(block);
}

// ── The six questions ────────────────────────────────────────────────────
//
// Six answers, each a count or a date taken from the tables below, each
// linking to them. There is deliberately no generated sentence saying what
// they add up to: on most targets the record does not support a conclusion,
// and a template with a slot for one writes it anyway.

function renderRead(host) {
  const f = state.data.feasibility || {};
  if (!(f.lines || []).length) return;

  host.appendChild(el('div', { class: 'read-head' }, [
    el('div', { class: 'read-label', text: 'What the record holds' }),
    faceLegend(),
  ]));

  const list = el('ol', { class: 'read-lines' });
  for (const line of (f.lines || []).slice(0, 6)) {
    const detail = el('p', { class: 'read-why', text: line.detail || '', hidden: true });
    const toggle = el('button', {
      class: 'read-more', 'aria-expanded': 'false',
      text: 'Where from',
      onclick: (ev) => {
        const open = detail.hidden;
        detail.hidden = !open;
        ev.currentTarget.setAttribute('aria-expanded', String(open));
        ev.currentTarget.textContent = open ? 'Hide' : 'Where from';
      },
    });
    const jump = line.anchor ? el('button', {
      class: 'read-jump', text: 'Evidence →',
      onclick: () => openEvidence(line.anchor),
    }) : null;

    list.appendChild(el('li', { class: 'read-line face-' + (line.face || 'science') }, [
      el('span', { class: 'read-q', text: line.label }),
      el('span', { class: 'read-a', text: line.value }),
      el('span', { class: 'read-acts' }, jump ? [toggle, jump] : [toggle]),
      detail,
    ]));
  }
  host.appendChild(list);

  if (f.audience) host.appendChild(el('p', { class: 'read-foot', text: f.audience }));
}

// Anchors in the read are tab names, not DOM ids: the evidence for a line
// lives in a panel that may not be rendered yet.
const EVIDENCE_TABS = {
  '#precedent': 'assets', '#failures': 'stops', '#crowding': 'mechanisms',
  '#readouts': 'trials', '#modalities': 'whitespace', '#whitespace': 'whitespace',
  '#licensing': 'licensing',
};

function openEvidence(anchor) {
  const tab = EVIDENCE_TABS[anchor] || 'assets';
  state.tab = tab;
  renderTabs();
  $('#tabs').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function firstSentences(text, count) {
  // Split *at* sentence boundaries rather than matching sentence bodies.
  // Matching bodies means a "." inside a decimal ends a sentence, and
  // "association 0.62" gets cut into "association 0" — the boundary form only
  // splits where punctuation is followed by whitespace and a capital, which
  // a decimal never is.
  const parts = String(text || '').split(/(?<=[.!?])\s+(?=[A-Z(“"'])/);
  return parts.slice(0, count).join(' ').trim();
}

// ── Tab: licensing ───────────────────────────────────────────────────────

function licensingRows(assets) {
  const lic = state.data.licensing || {};
  const shown = new Set(assets.map((a) => a.name));
  return (lic.assets || []).filter((r) => shown.has(r.asset));
}

function renderLicensing(assets, host) {
  const lic = state.data.licensing || {};
  const rows = licensingRows(assets);
  const deals = lic.deals || {};
  const dealRows = deals.deals || [];
  const licensed = new Set(dealRows.map((d) => d.matched_asset).filter(Boolean));

  host.appendChild(el('p', { class: 'panel-intro', text:
    'Two things, kept apart. What has already been licensed, taken from the parties\u2019 '
    + 'own announcements. And where every programme on this target stands \u2014 who holds '
    + 'it, how far it went, what it last read out, and whether a deal is on file for it. '
    + 'There is no availability score: the weights behind one are somebody\u2019s judgement '
    + 'wearing a number, and yours will differ.' }));

  host.appendChild(el('h3', { class: 'panel-h', text: 'Deals on file' }));
  if (!dealRows.length) {
    host.appendChild(el('div', { class: 'empty' }, [
      el('p', { text: 'No deal has been entered for this target.' }),
      el('p', { class: 'hint', style: 'margin-top:8px', text:
        'There is no free, redistributable deal database, so this file is maintained by '
        + 'hand: add data/deals/' + state.data.target.symbol + '.csv and it appears here '
        + 'on the next load. An empty file means nobody has filled it in \u2014 not that '
        + 'nothing has been licensed.' }),
    ]));
  } else {
    const body = el('tbody');
    for (const deal of dealRows) {
      body.appendChild(el('tr', {}, [
        el('td', { class: 'who', text: deal.date || '\u2014' }),
        el('td', {}, [
          el('div', { text: deal.acquirer || '\u2014' }),
          deal.target_company
            ? el('div', { class: 'asset-syn', text: '\u2190 ' + deal.target_company }) : null,
        ]),
        el('td', {}, [
          el('div', { text: deal.asset || '\u2014' }),
          deal.matched_asset ? el('span', { class: 'pill', text: 'in this table' }) : null,
        ]),
        el('td', { class: 'who' }, [
          document.createTextNode(deal.stage_at_deal || '\u2014'),
          (deal.deal_type && deal.deal_type !== 'licence')
            ? el('div', { class: 'asset-syn', text: deal.deal_type }) : null,
        ]),
        el('td', { class: 'num', text: deal.upfront_usd_m ?? '\u2014' }),
        el('td', { class: 'num', text: deal.total_usd_m ?? '\u2014' }),
        el('td', { class: 'who', text: deal.territory || '\u2014' }),
        el('td', {}, [deal.source_url
          ? el('a', { href: deal.source_url, target: '_blank', rel: 'noopener', text: 'source' })
          : document.createTextNode('\u2014')]),
      ]));
    }
    host.appendChild(el('div', { class: 'tablewrap' }, [el('table', {}, [
      el('thead', {}, [el('tr', {},
        ['Date', 'Acquirer \u2190 seller', 'Asset', 'Stage at deal', 'Upfront $m',
         'Total $m', 'Territory', ''].map((label, i) =>
          el('th', { class: (i === 4 || i === 5) ? 'num' : '', text: label })))]),
      body])]));
    // No median. A handful of hand-entered rows is a sample size a reader would
    // reject on sight, and a median printed from it reads as a market rate.
    host.appendChild(el('p', { class: 'hint', style: 'margin:10px 0 0', text:
      'Figures are as the party\u2019s own announcement stated them; a total includes '
      + 'milestones where the release said so. No average is computed \u2014 a handful of '
      + 'rows cannot support one, and mixing an acquisition into a column of licence '
      + 'upfronts reports a price no asset was ever sold for.' }));
  }

  host.appendChild(el('h3', { class: 'panel-h', style: 'margin-top:26px',
    text: 'Where each programme stands' }));
  if (!rows.length) { host.appendChild(emptyState()); return; }

  const byName = new Map(assets.map((a) => [a.name, a]));
  const nUnplaced = rows.filter((r) => !licensed.has(r.asset)).length;
  host.appendChild(el('p', { class: 'hint', style: 'margin:0 0 12px', text:
    nUnplaced + ' of ' + rows.length + ' programmes are not on a deal in this file. '
    + 'That is not the same as being available: it means this record cannot show a deal '
    + 'for them.' }));

  // Not on a deal first, then stopped before running, then by phase. This is a
  // sort, not a score: a programme that reached Phase 2 and then stopped is
  // what a reader opened this tab for, and ordering by phase alone buried it
  // under every approved drug a large sponsor is still selling.
  const ordered = rows.slice().sort((a, b) =>
    ((licensed.has(a.asset) ? 1 : 0) - (licensed.has(b.asset) ? 1 : 0))
    || ((a.is_active ? 1 : 0) - (b.is_active ? 1 : 0))
    || (b.phase - a.phase) || a.asset.localeCompare(b.asset));

  const body = el('tbody');
  for (const row of ordered) {
    const asset = byName.get(row.asset) || {};
    const onDeal = dealRows.filter((d) => d.matched_asset === row.asset);
    body.appendChild(el('tr', {}, [
      el('td', {}, [el('button', { class: 'link', text: row.asset,
        onclick: () => { if (byName.has(row.asset)) openDrawer(byName.get(row.asset)); } })]),
      el('td', { text: row.sponsor || 'not stated' }),
      el('td', { class: 'who', text: row.phase_label || '\u2014' }),
      el('td', { class: 'who', text: row.is_active ? 'Active' : 'All trials stopped' }),
      el('td', { class: 'who', text: lastOrNextReadout(asset) }),
      el('td', {}, onDeal.length
        ? onDeal.map((d) => el('div', { class: 'asset-syn', text:
            d.date + ' \u00b7 ' + d.acquirer + (d.territory ? ' \u00b7 ' + d.territory : '') }))
        : [document.createTextNode('\u2014')]),
    ]));
  }
  host.appendChild(el('div', { class: 'tablewrap' }, [el('table', {}, [
    el('thead', {}, [el('tr', {},
      ['Programme', 'Held by', 'Furthest phase', 'Status', 'Last / next readout',
       'On a deal?'].map((label) => el('th', { text: label })))]),
    body])]));
  host.appendChild(el('p', { class: 'hint', style: 'margin:10px 0 0', text:
    'Six facts, no verdict. A programme that reached Phase 2 and then stopped is the '
    + 'classic in-licensing candidate, and the first thing to establish is why it '
    + 'stopped \u2014 which the Terminations view answers, quoting the sponsor.' }));
}

// The soonest completion still ahead among an asset\u2019s trials, or the most
// recent one behind it. A date is what a BD reader schedules around.
function lastOrNextReadout(asset) {
  const today = new Date().toISOString().slice(0, 10);
  let past = null, future = null;
  for (const nct of asset.trials || []) {
    const trial = state.trialsByNct.get(nct);
    const when = trial && trial.completion_date;
    if (!when) continue;
    if (when >= today) { if (!future || when < future) future = when; }
    else if (!past || when > past) past = when;
  }
  if (future) return 'next ' + future;
  if (past) return 'last ' + past;
  return '\u2014';
}

const FILTER_GROUPS = [
  { key: 'phase', label: 'Phase', of: (a) => [String(a.max_phase)], fmt: (v) => PHASE_LABEL[v] || v,
    order: (a, b) => Number(b) - Number(a) },
  { key: 'status', label: 'Status', of: (a) => [a.is_active ? 'Active' : 'Dormant'] },
  { key: 'modality', label: 'Modality', of: (a) => [a.modality].filter(Boolean) },
  { key: 'mechanism', label: 'Mechanism class', of: (a) => [a.mechanism_class].filter(Boolean) },
  { key: 'sponsor', label: 'Sponsor', of: (a) => [a.sponsor].filter(Boolean) },
  { key: 'indication', label: 'Indication', of: (a) => a.indications || [] },
];
function renderFilters() {
  const host = $('#filter-groups');
  host.innerHTML = '';
  const assets = state.data.assets;

  for (const group of FILTER_GROUPS) {
    const counts = new Map();
    for (const asset of assets) {
      for (const value of group.of(asset)) counts.set(value, (counts.get(value) || 0) + 1);
    }
    if (counts.size < 2) continue;

    let values = Array.from(counts.keys());
    values.sort(group.order || ((a, b) => counts.get(b) - counts.get(a) || String(a).localeCompare(String(b))));

    const box = el('div', { class: 'fgroup' });
    box.appendChild(el('h3', { onclick: (e) => {
      const body = e.currentTarget.nextSibling;
      body.hidden = !body.hidden;
      $('.caret', e.currentTarget).textContent = body.hidden ? '▸' : '▾';
    } }, [
      document.createTextNode(group.label),
      el('span', { class: 'caret', text: '▾' }),
    ]));

    const body = el('div');
    const LIMIT = 6;
    values.forEach((value, i) => {
      const row = el('label', { class: 'fopt', hidden: i >= LIMIT }, [
        el('input', { type: 'checkbox', value, onchange: (e) => toggleFilter(group.key, value, e.target.checked) }),
        el('span', { text: group.fmt ? group.fmt(value) : String(value) }),
        el('span', { class: 'n', text: String(counts.get(value)) }),
      ]);
      body.appendChild(row);
    });
    if (values.length > LIMIT) {
      const more = el('button', { class: 'link fmore', text: '+ ' + (values.length - LIMIT) + ' more' });
      more.addEventListener('click', () => {
        const expanded = more.dataset.open === '1';
        $$('.fopt', body).forEach((row, i) => { if (i >= LIMIT) row.hidden = expanded; });
        more.dataset.open = expanded ? '0' : '1';
        more.textContent = expanded ? '+ ' + (values.length - LIMIT) + ' more' : 'Show fewer';
      });
      body.appendChild(more);
    }
    box.appendChild(body);
    host.appendChild(box);
  }
  updateFilterCount();
}

function toggleFilter(key, value, on) {
  if (!state.filters[key]) state.filters[key] = new Set();
  if (on) state.filters[key].add(value); else state.filters[key].delete(value);
  if (!state.filters[key].size) delete state.filters[key];
  updateFilterCount();
  renderTabs();
}

$('#f-reset').addEventListener('click', () => {
  state.filters = {};
  $$('#filter-groups input[type=checkbox]').forEach((box) => { box.checked = false; });
  updateFilterCount();
  renderTabs();
});

function filteredAssets() {
  const active = Object.entries(state.filters);
  if (!active.length) return state.data.assets;
  return state.data.assets.filter((asset) => active.every(([key, chosen]) => {
    const group = FILTER_GROUPS.find((g) => g.key === key);
    return group.of(asset).some((value) => chosen.has(value));
  }));
}

function updateFilterCount() {
  const shown = filteredAssets().length;
  const total = state.data.assets.length;
  $('#f-count').textContent = shown === total
    ? total + ' assets'
    : shown + ' of ' + total + ' assets';
}

// ── Tabs ─────────────────────────────────────────────────────────────────

// ── Tab: reading ─────────────────────────────────────────────────────────
//
// Not a literature database. Two short lists — the review that will bring
// someone up to speed, and what the field has taken up recently — and then a
// link to the live query, which is a better place to keep looking than a
// frozen copy of twenty rows.

function renderLiterature(assets, host) {
  const lit = state.data.literature || {};
  const reviews = lit.reviews || [];
  const mech = lit.mechanism || [];

  if (!reviews.length && !mech.length) {
    host.appendChild(el('p', { class: 'panel-intro', text:
      'No reading list in this build — Europe PMC was unreachable when it ran.' }));
    return;
  }

  host.appendChild(el('p', { class: 'panel-intro', text: lit.note || '' }));

  const section = (title, rows, blurb) => {
    if (!rows.length) return;
    host.appendChild(el('h3', { class: 'panel-h', text: title }));
    if (blurb) host.appendChild(el('p', { class: 'hint', text: blurb }));
    const list = el('ol', { class: 'papers' });
    for (const paper of rows) {
      list.appendChild(el('li', { class: 'paper' }, [
        el('a', { class: 'paper-title', href: paper.url, target: '_blank', rel: 'noopener',
                  text: paper.title }),
        el('div', { class: 'paper-meta' }, [
          el('span', { text: [paper.journal, paper.year].filter(Boolean).join(' · ') }),
          paper.citations ? el('span', { class: 'paper-cites',
            text: paper.citations + ' citations' }) : null,
          paper.open_access ? el('span', { class: 'paper-oa', text: 'open access' }) : null,
        ]),
      ]));
    }
    host.appendChild(list);
  };

  section('Start here', reviews,
    'Reviews, ranked by how often the field has cited them.');
  section('Recent mechanism work', mech,
    'Restricted to the last five years first, then ranked — so this is where the '
    + 'field is now, not where it started.');

  if (lit.search_url) {
    host.appendChild(el('p', { class: 'hint' }, [
      document.createTextNode('Keep looking: '),
      el('a', { href: lit.search_url, target: '_blank', rel: 'noopener',
                text: 'this query on Europe PMC' }),
      document.createTextNode('.'),
    ]));
  }
}

const TABS = [
  { key: 'assets', label: 'Assets', count: (a) => a.length, render: renderAssets },
  { key: 'mechanisms', label: 'Mechanisms', count: (a) => clustersOf(a).length, render: renderMechanisms },
  { key: 'trials', label: 'Trials', count: (a) => trialsOf(a).length, render: renderTrials },
  // The industry term, and the one a BD reader searches for. It reads the
  // registry's whyStopped field but the view is about why programmes ended,
  // which is not the same thing as a trial status.
  { key: 'stops', label: 'Terminations', count: (a) => stopsOf(a).length, render: renderStops },
  // One idea had three names on the same screen: "Whitespace" is the industry
  // word, the tab said "Gaps", the tile said "Gaps" but counted something
  // wider, and the six questions asked "What has nobody tried?". Worse, the
  // tile's answer covered untried diseases AND untried modalities while the
  // tab held only the diseases, so the two never agreed. One name, one tab,
  // and both lists inside it.
  { key: 'whitespace', label: 'Untried',
    count: () => (state.data.whitespace || []).length + untriedModalities().length,
    render: renderWhitespace },
  // Every programme the view assesses, which is what the view lists. Badging
  // it with the subset carrying availability signals put a 14 on a tab whose
  // first figure was "30 programmes assessed".
  { key: 'licensing', label: 'Licensing', count: (a) => licensingRows(a).length,
    render: renderLicensing },
  { key: 'reading', label: 'References',
    count: () => ((state.data.literature || {}).reviews || []).length
      + ((state.data.literature || {}).mechanism || []).length,
    render: renderLiterature },
];

function renderTabs() {
  const assets = filteredAssets();
  // The lens sets which tab leads, and which tab opens by default the first
  // time a target is shown.
  // "Why they stopped" sits second in both orders. It is the view no other
  // target database offers, and burying it fourth meant most readers reached
  // the tables, recognised them, and never found the part that is different.
  const order = state.lens === 'scientist'
    ? ['mechanisms', 'stops', 'reading', 'whitespace', 'trials', 'assets', 'licensing']
    : ['assets', 'stops', 'trials', 'licensing', 'mechanisms', 'whitespace', 'reading'];
  const tabs = order.map((key) => TABS.find((t) => t.key === key));

  if (!state.tab || !tabs.some((t) => t.key === state.tab)) state.tab = tabs[0].key;

  const nav = $('#tabs');
  nav.innerHTML = '';
  for (const tab of tabs) {
    nav.appendChild(el('button', {
      class: 'tab', role: 'tab', 'aria-selected': tab.key === state.tab,
      onclick: () => { state.tab = tab.key; renderTabs(); },
    }, [
      document.createTextNode(tab.label),
      el('span', { class: 'badge', text: String(tab.count(assets)) }),
    ]));
  }

  const host = $('#tab-panels');
  host.innerHTML = '';
  TABS.find((t) => t.key === state.tab).render(assets, host);
  updateFilterCount();
}

// ── Tab: assets ──────────────────────────────────────────────────────────

const ASSET_COLUMNS = [
  { key: 'name', label: 'Asset', sortable: true },
  { key: 'sponsor', label: 'Sponsor', sortable: true },
  { key: 'max_phase', label: 'Phase', sortable: true },
  { key: 'mechanism_class', label: 'Mechanism', sortable: true },
  { key: 'modality', label: 'Modality', sortable: true },
  { key: 'indications', label: 'Indications', sortable: false },
  { key: 'trials', label: 'Trials', sortable: true, num: true },
];

function sortAssets(assets) {
  const { key, dir } = state.sort;
  return assets.slice().sort((a, b) => {
    let x = a[key], y = b[key];
    if (Array.isArray(x)) { x = x.length; y = y.length; }
    if (typeof x === 'string') return dir * x.localeCompare(y);
    return dir * ((x ?? -Infinity) - (y ?? -Infinity));
  });
}

// ── Precedent ────────────────────────────────────────────────────────────
//
// Whether anyone has made a medicine out of this target is the first thing an
// early investor needs and the last thing a table of assets in development
// tells them, because approved drugs and dead programmes sit in the same
// column as everything else. So it is stated in one line, and the drug names
// are behind a disclosure — a reader who wants the list can open it, and a
// reader who wants the answer already has it.

function renderPrecedent(host) {
  const p = state.data.precedent || {};
  if (!p.tier_label) return;

  const tone = { approved: 'good', late_stage: 'good', in_flight: 'neutral',
    early_clinical: 'caution', preclinical: 'caution', failed: 'bad' }[p.tier] || 'neutral';

  const box = el('div', { class: 'precedent tone-' + tone });
  box.appendChild(el('div', { class: 'precedent-tier', text: p.tier_label }));
  box.appendChild(el('p', { class: 'precedent-read', text: p.read || '' }));

  for (const line of (p.evidence || []).slice(0, 3)) {
    box.appendChild(el('p', { class: 'precedent-ev', text: line }));
  }

  const approved = p.approved || [];
  if (approved.length) {
    const details = el('details', { class: 'disclose' });
    details.appendChild(el('summary', {
      text: approved.length + ' approved drug' + (approved.length === 1 ? '' : 's'),
    }));
    const list = el('ul', { class: 'approved-list' });
    for (const drug of approved) {
      list.appendChild(el('li', {}, [
        el('b', { text: drug.name }),
        el('span', { class: 'who', text: [drug.sponsor, drug.modality].filter(Boolean).join(' · ') }),
        el('span', { class: 'who', text: drug.first_approval ? 'approved ' + drug.first_approval : '' }),
        drug.withdrawn ? el('span', { class: 'flag-bad', text: 'withdrawn' }) : null,
      ]));
    }
    details.appendChild(list);
    box.appendChild(details);
  }
  host.appendChild(box);
}

function renderAssets(assets, host) {
  renderPrecedent(host);
  renderWhereDeveloped(assets, host);

  host.appendChild(el('p', { class: 'panel-intro', text:
    'Every programme resolved against this target, reconciled across Open Targets, '
    + 'ChEMBL and ClinicalTrials.gov. Dormant means every linked trial stopped and '
    + 'nothing is running. Click a row for its trials and provenance.' }));

  if (!assets.length) { host.appendChild(emptyState()); return; }

  const sortBy = (col) => {
    state.sort = state.sort.key === col.key
      ? { key: col.key, dir: -state.sort.dir }
      : { key: col.key, dir: col.key === 'name' || col.key === 'sponsor' ? 1 : -1 };
    renderTabs();
  };
  const head = el('tr', {}, ASSET_COLUMNS.map((col) => el('th', {
    class: (col.sortable ? 'sortable ' : '') + (col.num ? 'num' : ''),
    'aria-sort': state.sort.key === col.key ? (state.sort.dir === 1 ? 'ascending' : 'descending') : 'none',
    tabindex: col.sortable ? '0' : null,
    role: col.sortable ? 'button' : null,
    onclick: col.sortable ? () => sortBy(col) : null,
    onkeydown: col.sortable ? (event) => {
      if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); sortBy(col); }
    } : null,
  }, [
    document.createTextNode(col.label),
    col.sortable ? el('span', { class: 'arrow', text: state.sort.key === col.key ? (state.sort.dir === 1 ? '↑' : '↓') : '↕' }) : null,
  ])));

  const body = el('tbody');
  for (const asset of sortAssets(assets)) {
    body.appendChild(clickableRow(() => openDrawer(asset), [
      el('td', {}, [
        el('div', { class: 'asset-name', text: asset.name }),
        asset.synonyms && asset.synonyms.length
          ? el('div', { class: 'asset-syn', text: asset.synonyms.slice(0, 2).join(' · ') }) : null,
      ]),
      el('td', { class: 'who', text: asset.sponsor || '—' }),
      el('td', {}, [
        el('span', { class: 'pill p' + Math.max(asset.max_phase, 0), text: asset.phase_label }),
        asset.is_active ? null : el('span', { class: 'pill dormant', style: 'margin-left:5px', text: 'dormant' }),
      ]),
      el('td', { class: 'who', text: asset.mechanism_class || '—' }),
      el('td', { class: 'who', text: asset.modality || '—' }),
      el('td', { class: 'who', text: (asset.indications || []).slice(0, 2).join('; ') || '—' }),
      el('td', { class: 'num', text: String((asset.trials || []).length) }),
    ]));
  }
  host.appendChild(el('div', { class: 'tablewrap' }, [el('table', {}, [el('thead', {}, [head]), body])]));
}

function emptyState() {
  return el('div', { class: 'empty' }, [
    el('p', { text: 'Nothing matches the current filter.' }),
    el('p', { class: 'hint', style: 'margin-top:6px', text: 'Reset the filters to see everything again.' }),
  ]);
}

// ── Tab: mechanisms ──────────────────────────────────────────────────────

function clustersOf(assets) {
  const map = new Map();
  for (const asset of assets) {
    const key = asset.mechanism_class || 'Unclassified';
    if (!map.has(key)) map.set(key, []);
    map.get(key).push(asset);
  }
  return Array.from(map.entries())
    .map(([label, list]) => ({ label, list, best: Math.max.apply(null, list.map((a) => a.max_phase)) }))
    .sort((a, b) => b.best - a.best || b.list.length - a.list.length || a.label.localeCompare(b.label));
}


// The molecules in one mechanism class. A named class holds a handful and they
// are shown; "Unclassified" holds everything the mechanism rules could not
// place, which on PD-1 is most of the table, and printing two hundred chips
// buried the eight classes above it. So the long ones start closed and say how
// many they hold.
const MECH_SHOWN_CLOSED = 12;

function mechAssetList(cluster) {
  const box = el('div', { class: 'mech-assets' });
  const chip = (asset) => el('button', {
    class: 'mech-asset', onclick: () => openDrawer(asset), text: asset.name,
  });
  const long = cluster.list.length > MECH_SHOWN_CLOSED;
  const shown = long ? cluster.list.slice(0, MECH_SHOWN_CLOSED) : cluster.list;
  for (const asset of shown) box.appendChild(chip(asset));
  if (!long) return box;

  const rest = el('span', { hidden: true });
  for (const asset of cluster.list.slice(MECH_SHOWN_CLOSED)) rest.appendChild(chip(asset));
  const more = cluster.list.length - MECH_SHOWN_CLOSED;
  const toggle = el('button', {
    class: 'link mech-more',
    onclick: () => {
      const open = rest.hidden;
      rest.hidden = !open;
      toggle.textContent = open ? 'Show fewer' : 'Show ' + more + ' more';
    },
    text: 'Show ' + more + ' more',
  });
  box.appendChild(rest);
  box.appendChild(toggle);
  return box;
}

// Three of these labels name a gap rather than a mechanism, and they are not
// the same gap. A reader looking at "Antibody — mechanism unresolved" next to
// twenty-four blocking antibodies is owed the difference between a molecule no
// database has assigned an action to and a trial whose sponsor never wrote the
// molecule down.
function mechCaption(label) {
  if (label === 'Named only by class') {
    return 'The sponsor registered the trial without naming the molecule — it is '
      + 'recorded as "anti-PD-1 antibody" or "BCMA CAR-T" and nothing more. The '
      + 'programme is real and the trial is one click away; what is missing is '
      + 'the name, not the mechanism.';
  }
  if (label === 'Unclassified') {
    return 'Named molecules that no source assigns a mechanism to.';
  }
  if (label.toLowerCase().indexOf('unresolved') !== -1) {
    return 'The modality is on record. What the molecule does to the target is not.';
  }
  return '';
}

function renderMechanisms(assets, host) {
  // Where the target sits comes first, because the classes below only mean
  // something once the reader knows what the target does. It sat above the six
  // questions until it was read in place: four lines of biology between the
  // symbol and the answers pushed the answers off the screen, and the block
  // belongs with the mechanism view it explains.
  renderPathway(host);

  // The protein's location, domains and function used to be repeated here.
  // They are already on the page, above the tabs, in the molecule card the
  // reader has just read. A second copy is not depth, it is scrolling.
  host.appendChild(el('p', { class: 'panel-intro', text:
    'Grouped by what each asset does to the target, not by what it is. Depleting '
    + 'and blocking antibodies are separate classes because they are separate '
    + 'competitive propositions, even though every database calls both an antagonist antibody.' }));

  const clusters = clustersOf(assets);
  if (clusters.length) {
    const widest = Math.max.apply(null, clusters.map((c) => c.list.length));
    const grid = el('div', { class: 'mech-grid' });
    for (const cluster of clusters) {
      const card = el('div', { class: 'mech' }, [
        el('div', { class: 'mech-head' }, [
          el('span', { class: 'mech-name', text: cluster.label }),
          el('span', { class: 'pill p' + Math.max(cluster.best, 0), text: 'to ' + (PHASE_LABEL[cluster.best] || 'Unknown') }),
        ]),
        el('div', { class: 'mech-bar' }, [
          el('div', { class: 'mech-fill', style: 'width:' + (100 * cluster.list.length / widest) + '%' }),
        ]),
      ]);
      const caption = mechCaption(cluster.label);
      if (caption) card.appendChild(el('p', { class: 'mech-caption', text: caption }));
      card.appendChild(mechAssetList(cluster));
      grid.appendChild(card);
    }
    host.appendChild(grid);
  } else {
    host.appendChild(emptyState());
  }

  renderModalities(host);
}

// ── Modality fit ─────────────────────────────────────────────────────────
//
// Two lines, not a twelve-row table: what has been tried on this target, and
// what could be tried and has not. The primer for each — what it demands of
// a target, how it fails, what it costs — opens on click, for the reader who
// wants it.

function renderModalities(host) {
  const rows = state.data.modalities || [];
  if (!rows.length) return;

  const inUse = rows.filter((r) => r.in_use);
  // With no annotated location, every modality that does not depend on one
  // reports "available" — true, and no basis for calling it an opening. The
  // untried column is withheld rather than filled with a technicality.
  const located = !rows.some((r) => r.fit === 'unknown');
  const open = located
    ? rows.filter((r) => !r.in_use && r.fit === 'available' && !r.speculative) : [];
  const blocked = rows.filter((r) => r.fit === 'blocked');

  host.appendChild(el('h3', { class: 'panel-h', text: 'Modalities' }));

  const say = (label, list, cls) => {
    if (!list.length) return null;
    return el('p', { class: 'modality-line ' + cls }, [
      el('b', { text: label }),
      el('span', {}, list.map((r) => el('button', {
        class: 'modality-chip ' + cls, text: r.key,
        onclick: () => openModality(r),
        title: 'What this demands of a target',
      }))),
    ]);
  };

  const lines = [
    say('Being used here', inUse, 'used'),
    say('Available, untried', open, 'open'),
    say('Ruled out by location', blocked, 'blocked'),
  ].filter(Boolean);
  for (const line of lines) host.appendChild(line);

  host.appendChild(el('p', { class: 'hint', text: located
    ? 'Availability is a location check only — whether the modality can physically '
      + 'reach a protein annotated where this one is. Everything else it demands is '
      + 'in the panel behind each name, and needs a human.'
    : 'No subcellular location is annotated for this target, so which modalities could '
      + 'physically reach it cannot be checked. Rebuild the target to pick it up. What '
      + 'each modality demands is still in the panel behind its name.' }));
}

function openModality(row) {
  const body = el('div');
  body.appendChild(el('div', { class: 'drawer-eyebrow', text: row.fit_label }));
  body.appendChild(el('h2', { id: 'd-name', text: row.key }));
  body.appendChild(el('p', { class: 'drawer-lede', text: row.what }));
  if (row.fit_reason) body.appendChild(el('p', { class: 'drawer-fit', text: row.fit_reason }));

  const block = (title, items) => {
    if (!items || !items.length) return;
    body.appendChild(el('h3', { class: 'drawer-h', text: title }));
    body.appendChild(el('ul', { class: 'drawer-list' }, items.map((t) => el('li', { text: t }))));
  };
  block('What it demands of the target', row.requires);
  block('How programmes on it actually fail', row.fails);
  if (row.economics) {
    body.appendChild(el('h3', { class: 'drawer-h', text: 'Time and capital to a first readout' }));
    body.appendChild(el('p', { text: row.economics }));
  }
  if (row.bd_note) body.appendChild(el('p', { class: 'drawer-bd', text: row.bd_note }));
  body.appendChild(el('p', { class: 'hint', text:
    'Hand-written reference, not generated from data, and the figures are industry '
    + 'rules of thumb with wide variance.' }));

  const host = $('#drawer-content');
  host.innerHTML = '';
  host.appendChild(body);
  $('#drawer').hidden = false;
}

function matrixOf(assets) {
  // Both hard parts are done in the engine and read off the asset here.
  //
  // One name per disease: this used to group whatever spellings the registry
  // held, so "melanoma", "Melanoma" and "advanced unresectable melanoma" were
  // three rows -- the tab was badged 1,360 on PD-1 while the engine had
  // resolved 915 of them. asset.indications now arrives already resolved.
  //
  // Phase per indication: an asset in Phase 3 for one disease is not in Phase 3
  // for all of them, and using the overall maximum is how this table misleads.
  // asset.indication_phase carries what each indication actually reached.
  const cells = new Map();
  const counts = new Map();
  const mechanisms = new Set();

  for (const asset of assets) {
    const mechanism = asset.mechanism_class || 'Unclassified';
    mechanisms.add(mechanism);
    const reached = asset.indication_phase || {};
    for (const indication of (asset.indications.length ? asset.indications : ['(not stated)'])) {
      counts.set(indication, (counts.get(indication) || 0) + 1);
      const phase = indication in reached ? reached[indication] : asset.max_phase;
      const cellKey = indication + ' ' + mechanism;
      cells.set(cellKey, Math.max(cells.get(cellKey) ?? -1, phase));
    }
  }

  const mechanismList = Array.from(mechanisms).sort();
  const rows = Array.from(counts.keys()).map((indication) => ({
    indication,
    n: counts.get(indication),
    cells: mechanismList.map((m) => cells.get(indication + ' ' + m) ?? -1),
  }));
  rows.sort((a, b) => Math.max.apply(null, b.cells) - Math.max.apply(null, a.cells) || b.n - a.n
    || a.indication.localeCompare(b.indication));
  return { mechanisms: mechanismList, rows };
}

function shortMechanism(label) {
  const map = {
    'Depleting antibody (ADCC/CDC)': 'Depleting mAb',
    'Blocking antibody': 'Blocking mAb',
    'Agonist antibody': 'Agonist mAb',
    'Ligand trap / decoy receptor': 'Ligand trap',
    'Cell therapy — target-directed CAR': 'CAR-T',
    'Cell therapy — bispecific CAR': 'Bispecific CAR',
    'Cell therapy — ligand-based CAR': 'Ligand CAR',
    'Bispecific / T-cell engager': 'Bispecific',
    'ADC — payload delivery': 'ADC',
    'Oligonucleotide knockdown': 'Oligo',
  };
  const clean = (label || 'Unclassified').replace(' [model]', '');
  if (map[clean]) return map[clean];
  if (clean.includes('—')) return clean.split('—')[1].trim().slice(0, 18);
  return clean.slice(0, 20);
}

// Where the field is concentrated, in ten rows above the asset table.
//
// This replaced a tab: an indication x mechanism grid, badged with every row
// it held -- 161 on ERBB2, 558 on PD-1. It was the largest source of wrong
// numbers on the site, and what it added over the asset table (which carries
// each programme's own indications) was one thing: where the work is piled up.
// Ten rows say that. A five-hundred-row grid needs the tail to be right; a top
// ten does not, and the tail is exactly the part free data gets wrong.
function renderWhereDeveloped(assets, host) {
  const matrix = matrixOf(assets);
  const rows = matrix.rows.slice(0, 10);
  if (!rows.length) return;
  const body = el('tbody');
  for (const row of rows) {
    const best = Math.max.apply(null, row.cells);
    body.appendChild(el('tr', {}, [
      el('td', { text: row.indication }),
      el('td', { class: 'num', text: String(row.n) }),
      el('td', { class: 'who', text: PHASE_LABEL[best] || 'Unknown' }),
    ]));
  }
  host.appendChild(el('h3', { class: 'panel-h', text: 'Where it is being developed' }));
  host.appendChild(el('div', { class: 'tablewrap' }, [el('table', {}, [
    el('thead', {}, [el('tr', {}, ['Disease', 'Programmes', 'Furthest phase']
      .map((label, i) => el('th', { class: i === 1 ? 'num' : '', text: label })))]),
    body])]));
  const rest = matrix.rows.length - rows.length;
  const omitted = (state.data.crowding || {}).indications_omitted || 0;
  host.appendChild(el('p', { class: 'hint', style: 'margin:8px 0 20px', text:
    'Counted from each programme\u2019s own indications, one row per disease. '
    + (rest > 0 ? rest + ' more ' + (rest === 1 ? 'disease is' : 'diseases are')
        + ' held by at least one programme' : '')
    + (omitted ? (rest > 0 ? ', and ' : '') + omitted + ' more '
        + (omitted === 1 ? 'is' : 'are') + ' held by a single programme with no trial '
        + 'naming that disease' : '')
    + ((rest > 0 || omitted) ? '. The download carries every row.' : '') }));
}

function trialsOf(assets) {
  const wanted = new Set();
  for (const asset of assets) for (const nct of asset.trials || []) wanted.add(nct);
  return state.data.trials.filter((t) => wanted.has(t.nct_id));
}

function renderTrials(assets, host) {
  const r = state.data.readouts || {};

  // The verdict first. A table of trials is a list of things that exist; the
  // question a reader actually has is whether any of them can settle
  // anything, and that answer is one sentence long.
  if (r.verdict) {
    host.appendChild(el('p', { class: 'panel-verdict', text: r.verdict }));
  }

  const catalysts = (r.catalysts || []).slice(0, 4);
  if (catalysts.length) {
    host.appendChild(el('h3', { class: 'panel-h', text: 'What reads out next' }));
    const list = el('ol', { class: 'catalysts' });
    for (const c of catalysts) {
      const strong = c.level === 'confirmatory' || c.level === 'controlled';
      list.appendChild(el('li', { class: 'catalyst' + (strong ? ' strong' : '') }, [
        el('div', { class: 'cat-when' }, [
          el('b', { text: c.date }),
          el('span', { class: 'hint', text: c.estimated ? 'sponsor estimate' : 'actual' }),
        ]),
        el('div', { class: 'cat-what' }, [
          el('div', {}, [
            el('span', { class: 'pill p' + Math.max(c.phase, 0), text: c.phase_label }),
            el('span', { class: 'cat-level' + (strong ? ' strong' : ''), text: c.level_label }),
          ]),
          el('a', { class: 'cat-title', href: c.url, target: '_blank', rel: 'noopener',
                    text: c.title || c.nct_id }),
          el('div', { class: 'who', text: c.sponsor || '' }),
          el('p', { class: 'cat-note', text: c.note || '' }),
        ]),
      ]));
    }
    host.appendChild(list);
  }

  const trials = trialsOf(assets).slice().sort((a, b) =>
    b.phase - a.phase || String(a.status).localeCompare(String(b.status)));
  if (!trials.length) { host.appendChild(emptyState()); return; }

  // Everything else is reference material, and it is behind a disclosure for
  // that reason. ClinicalTrials.gov does this better than this page can.
  const details = el('details', { class: 'disclose' });
  details.appendChild(el('summary', { text: 'All ' + trials.length + ' registered trials' }));
  details.appendChild(el('p', { class: 'panel-intro', text:
    'Only ClinicalTrials.gov is swept, so China- and Japan-only registrations are '
    + 'under-represented. Rows open on the registry.' }));

  const body = el('tbody');
  for (const trial of trials) {
    body.appendChild(clickableRow(
      () => window.open('https://clinicaltrials.gov/study/' + trial.nct_id, '_blank', 'noopener'), [
      el('td', {}, [el('span', { class: 'trial-id', text: trial.nct_id })]),
      el('td', { text: trial.title || '—' }),
      el('td', {}, [el('span', { class: 'pill p' + Math.max(trial.phase, 0), text: PHASE_LABEL[trial.phase] || 'Unknown' })]),
      el('td', { class: 'who', text: prettyStatus(trial.status) }),
      el('td', { class: 'who', text: trial.evidence_level ? EVIDENCE_LABEL[trial.evidence_level] || '—' : '—' }),
      el('td', { class: 'who', text: trial.sponsor || '—' }),
      el('td', { class: 'num', text: trial.enrollment ?? '—' }),
    ]));
  }
  details.appendChild(el('div', { class: 'tablewrap' }, [el('table', {}, [
    el('thead', {}, [el('tr', {}, ['NCT', 'Title', 'Phase', 'Status', 'Can show', 'Sponsor', 'N']
      .map((label, i) => el('th', { class: i === 6 ? 'num' : '', text: label })))]),
    body])]));
  host.appendChild(details);
}

const EVIDENCE_LABEL = {
  confirmatory: 'Confirmatory', controlled: 'Controlled', signal: 'Signal only',
  dose: 'Safety / dose', mechanistic: 'Mechanism only', unclear: 'Not stated',
};

function prettyStatus(status) {
  return String(status || '').replace(/_/g, ' ').toLowerCase()
    .replace(/^\w/, (ch) => ch.toUpperCase());
}

// ── Tab: terminations ────────────────────────────────────────────────────

function stopsOf(assets) {
  const STOPPED = new Set(['TERMINATED', 'WITHDRAWN', 'SUSPENDED']);
  return trialsOf(assets).filter((t) => STOPPED.has(t.status));
}

function renderStops(assets, host) {
  const stopped = stopsOf(assets);
  const stated = stopped.filter((t) => t.why_stopped);
  const failures = state.data.failures || {};

  host.appendChild(el('p', { class: 'panel-intro', text:
    'The question a termination count cannot answer: did these programmes die of '
    + 'the science or of the business? A trial stopped after a merger says nothing '
    + 'about the target, and counting it as evidence against the biology is how a '
    + 'team walks away from something that never failed.' }));

  if (!stopped.length) {
    host.appendChild(el('div', { class: 'empty', text:
      'No stopped trials among the assets currently shown.' }));
    return;
  }

  const counts = new Map();
  for (const trial of stated) {
    const label = trial.failure_class || 'unknown';
    counts.set(label, (counts.get(label) || 0) + 1);
  }
  // Four buckets that partition the stopped trials, so the row adds up to the
  // number beside it. It used to read "45 stopped, 45 gave a reason, 5
  // science-driven, 10 business-driven": the middle two counted a sponsor who
  // typed "Other" as having given a reason, and the last two came from the
  // whole target while the first two came from the filtered view, so filtering
  // pulled them apart. All four are counted here, from one list.
  const SCIENCE = new Set(['efficacy', 'safety', 'pk_pd']);
  const BUSINESS = new Set(['business', 'funding']);
  const OPERATIONAL = new Set(['recruitment', 'operational', 'regulatory', 'covid']);
  // Whether the material can be made is neither the science nor the sponsor's
  // appetite. It used to sit inside "operational", beside slow recruitment.
  const CMC = new Set(['cmc']);
  let nScience = 0, nBusiness = 0, nOperational = 0, nCmc = 0;
  for (const trial of stopped) {
    const key = trial.failure_class || 'unknown';
    if (SCIENCE.has(key)) nScience += 1;
    else if (CMC.has(key)) nCmc += 1;
    else if (BUSINESS.has(key)) nBusiness += 1;
    else if (OPERATIONAL.has(key)) nOperational += 1;
  }
  const nExplained = nScience + nBusiness + nOperational + nCmc;
  const nUnexplained = stopped.length - nExplained;
  const stat = (value, label, cls) => el('div', { class: cls || 'stat' }, [
    el('div', { class: 'stat-v', text: String(value) }),
    el('div', { class: 'stat-l', text: label })]);
  const strip = el('div', { class: 'summary', style: 'margin-bottom:8px' }, [
    stat(stopped.length, 'Trials stopped'),
    stat(nScience, 'Science-driven'),
    stat(nCmc, 'Manufacturing'),
    stat(nBusiness, 'Business-driven'),
    stat(nOperational, 'Operational'),
    stat(nUnexplained, 'No reason on record'),
  ]);
  host.appendChild(strip);
  host.appendChild(el('p', { class: 'hint', style: 'margin:0 0 22px', text:
    'The five add up to the total. Business means the sponsor decided to stop, '
    + 'operational means the study could not be run as designed, manufacturing means '
    + 'the material was the problem. "No reason on record" covers both an empty '
    + 'field and a sponsor who filled it with "Other" \u2014 and it is the limit on '
    + 'everything above it: ' + (stopped.length
      ? Math.round(100 * nExplained / stopped.length) + '% of these terminations say why.'
      : 'nothing here to read.') }));

  if (!stated.length) {
    host.appendChild(el('div', { class: 'empty', text:
      'None of the stopped trials stated a reason. That is common, and it is the '
      + 'main limit on this section.' }));
    return;
  }

  const byNct = new Map((failures.cases || []).map((c) => [c.nct_id, c]));
  const ordered = stated.slice().sort((a, b) => {
    const sa = /Science/.test((byNct.get(a.nct_id) || {}).class || '') ? 0 : 1;
    const sb = /Science/.test((byNct.get(b.nct_id) || {}).class || '') ? 0 : 1;
    return sa - sb || b.phase - a.phase;
  });

  for (const trial of ordered) {
    const record = byNct.get(trial.nct_id) || {};
    const klass = /Science/.test(record.class || '') ? 'sci' : (/Business/.test(record.class || '') ? 'biz' : '');
    host.appendChild(el('div', { class: 'term ' + klass }, [
      el('q', { text: trial.why_stopped }),
      el('div', { class: 'term-meta' }, [
        el('span', { class: 'pill ' + klass, text: record.class || 'Not classified' }),
        document.createTextNode(' '),
        el('strong', { text: PHASE_LABEL[trial.phase] || 'Unknown' }),
        document.createTextNode(' · ' + (trial.sponsor || '—') + ' · '),
        el('a', { href: 'https://clinicaltrials.gov/study/' + trial.nct_id, target: '_blank', rel: 'noopener', text: trial.nct_id }),
        record.evidence ? el('div', { text: 'classifier: ' + record.evidence }) : null,
      ]),
    ]));
  }
}

// ── Tab: whitespace ──────────────────────────────────────────────────────

function untriedModalities() {
  return (state.data.modalities || []).filter(
    (m) => !m.in_use && m.fit === 'available' && !m.speculative);
}

function renderWhitespace(assets, host) {
  const rows = state.data.whitespace || [];
  host.appendChild(el('p', { class: 'panel-intro', text:
    'What has nobody tried? Two ways of not having been tried, and they are '
    + 'different questions: a disease nobody has taken a drug to, and a way of '
    + 'drugging the target that nobody has used. Both are lists to check, not '
    + 'openings — the page cannot tell you why nobody has done it.' }));
  host.appendChild(el('h3', { class: 'panel-h', text:
    'Diseases with evidence and no clinical programme (' + rows.length + ')' }));
  host.appendChild(el('p', { class: 'hint', style: 'margin:-8px 0 18px' , text:
    'Read it as a list to check, not a list of openings. A gene that causes a '
    + 'congenital syndrome scores at the top of this screen and is not a market — '
    + 'on KRAS the strongest rows are Noonan and the other RASopathies. And the '
    + 'disease names come from an ontology on one side and sponsor free text on the '
    + 'other, so a row can be here because the two failed to match.' }));

  if (!rows.length) {
    host.appendChild(el('div', { class: 'empty', text:
      'Nothing passes the screen. On a well-worked target that is the expected '
      + 'answer and it is worth saying: every disease with genetic evidence behind '
      + 'it already carries a clinical programme.' }));
    return;
  }

  const top = Math.max.apply(null, rows.map((r) => r.genetic_score)) || 1;
  const body = el('tbody');
  for (const row of rows) {
    body.appendChild(el('tr', {}, [
      el('td', { text: row.disease }),
      el('td', { class: 'num', text: String(row.association_score) }),
      el('td', {}, [el('span', { class: 'ws-score' }, [
        el('span', { class: 'ws-bar' }, [
          el('span', { class: 'ws-fill', style: 'width:' + (100 * row.genetic_score / top) + '%' })]),
        el('span', { class: 'card-stat', text: String(row.genetic_score) }),
      ])]),
      el('td', { class: 'who', text: row.highest_phase }),
    ]));
  }
  host.appendChild(el('div', { class: 'tablewrap' }, [el('table', {}, [
    el('thead', {}, [el('tr', {}, ['Indication', 'Association', 'Genetic evidence', 'Furthest reached']
      .map((label, i) => el('th', { class: i === 1 ? 'num' : '', text: label })))]),
    body])]));
  renderUntriedModalities(host);
}

// The second half of the same question. These rows are also in the Mechanisms
// tab, where every modality is scored whether or not anyone has used it; here
// only the ones nobody has used on this target, because that is the list a
// reader of this tab came for.
function renderUntriedModalities(host) {
  const untried = untriedModalities();
  host.appendChild(el('h3', { class: 'panel-h', style: 'margin-top:22px', text:
    'Ways of drugging this target that nobody has used (' + untried.length + ')' }));
  if (!untried.length) {
    host.appendChild(el('div', { class: 'empty', text:
      'Every modality the rules judge available for this target is already in use.' }));
    return;
  }
  const list = el('ul', { class: 'untried-list' });
  for (const row of untried) {
    list.appendChild(el('li', {}, [
      el('b', { text: row.key }),
      document.createTextNode(' — ' + (row.fit_reason || row.what || '')),
    ]));
  }
  host.appendChild(list);
  host.appendChild(el('p', { class: 'hint', style: 'margin:10px 0 0', text:
    'Availability is a rule over where the protein sits and what class it is, '
    + 'not a statement that the chemistry works. Open the Mechanisms tab for how '
    + 'each one was judged.' }));
}

// ── Drawer ───────────────────────────────────────────────────────────────

function openDrawer(asset) {
  const host = $('#drawer-content');
  host.innerHTML = '';
  host.appendChild(el('h2', { id: 'd-name', text: asset.name }));
  if (asset.synonyms && asset.synonyms.length) {
    host.appendChild(el('p', { class: 'prov', text: asset.synonyms.join(' · ') }));
  }

  const kv = el('dl', { class: 'kv' });
  const pairs = [
    ['Sponsor', asset.sponsor || '—'],
    ['Phase', asset.phase_label + (asset.is_active ? '' : ' (dormant)')],
    ['Mechanism', asset.mechanism_class || '—'],
    ['Modality', asset.modality || '—'],
    ['Action type', asset.action_type || '—'],
    ['ChEMBL', asset.chembl_id || '—'],
    ['First approval', asset.first_approval || '—'],
  ];
  for (const [key, value] of pairs) {
    kv.appendChild(el('dt', { text: key }));
    kv.appendChild(el('dd', { text: String(value) }));
  }
  host.appendChild(kv);

  if (asset.mechanism_text) {
    host.appendChild(el('h3', { text: 'Mechanism, as recorded' }));
    host.appendChild(el('p', { style: 'font-size:13.5px;line-height:1.6', text: asset.mechanism_text }));
  }

  if (asset.indications && asset.indications.length) {
    host.appendChild(el('h3', { text: 'Indications' }));
    host.appendChild(el('div', { class: 'chips' },
      asset.indications.map((i) => el('span', { class: 'chip', text: i }))));
  }

  const trials = (asset.trials || []).map((n) => state.trialsByNct.get(n)).filter(Boolean);
  host.appendChild(el('h3', { text: 'Trials (' + trials.length + ')' }));
  if (!trials.length) {
    host.appendChild(el('p', { class: 'hint', text:
      'No registered trial is linked to this asset in the sources swept. For a '
      + 'preclinical or recently disclosed programme that is expected.' }));
  }
  for (const trial of trials.sort((a, b) => b.phase - a.phase)) {
    host.appendChild(el('div', { class: 'trial' }, [
      el('div', {}, [
        el('a', { class: 'trial-id', href: 'https://clinicaltrials.gov/study/' + trial.nct_id,
          target: '_blank', rel: 'noopener', text: trial.nct_id }),
        document.createTextNode(' · ' + (PHASE_LABEL[trial.phase] || 'Unknown') + ' · ' + prettyStatus(trial.status)),
      ]),
      el('div', { class: 'who', style: 'margin-top:3px', text: trial.title || '' }),
      trial.why_stopped ? el('div', { class: 'prov', style: 'margin-top:4px',
        text: 'Stopped: ' + trial.why_stopped }) : null,
    ]));
  }

  if (asset.provenance && asset.provenance.length) {
    host.appendChild(el('h3', { text: 'Provenance' }));
    const list = el('div', { class: 'prov' });
    const seen = new Set();
    for (const p of asset.provenance) {
      const key = p.source + p.identifier;
      if (seen.has(key)) continue;
      seen.add(key);
      const line = el('div');
      // "manual" is the field's value, not a word to show a reader. What it
      // means is that a person put this row in, which is the one provenance
      // that has to say so plainly.
      line.appendChild(document.createTextNode(
        (p.source === 'manual' ? 'entered by hand' : p.source) + ' · '));
      if (p.url) line.appendChild(el('a', { href: p.url, target: '_blank', rel: 'noopener', text: p.identifier }));
      else line.appendChild(document.createTextNode(p.identifier));
      list.appendChild(line);
    }
    host.appendChild(list);
  }

  $('#drawer').hidden = false;
  document.body.style.overflow = 'hidden';
}

function closeDrawer() {
  $('#drawer').hidden = true;
  document.body.style.overflow = '';
}
$$('[data-close-drawer]').forEach((node) => node.addEventListener('click', closeDrawer));
document.addEventListener('keydown', (event) => { if (event.key === 'Escape') closeDrawer(); });

// ── Boot ─────────────────────────────────────────────────────────────────

document.addEventListener('click', (event) => {
  const link = event.target.closest('a[data-nav]');
  if (!link) return;
  event.preventDefault();
  navigate(link.getAttribute('href'));
});

route();
