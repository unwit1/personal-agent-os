// Shopping tab for the Executive window. All data comes from the Shopping Agent through POST /api/shopping
// (agent_os.shopping_adapter). Nothing here scores, matches or prices anything; it only shows what Shopping returned.
// Retailer text is untrusted: it is only ever put into the page with textContent, and links are limited to http(s).
"use strict";

const ShoppingTab = (() => {
  const VIEWS = [
    ['overview', 'Overview'], ['research', 'Research & Add'], ['wishlist', 'Wishlist'], ['deals', 'Deals'],
    ['cart', 'Cart & Checkout'], ['orders', 'Orders'], ['diagnostics', 'Diagnostics'],
  ];
  const state = { view: 'overview', token: null, selected: new Set(), research: null, pollTimer: null, snapshot: null,
                  handoff: null, notice: null };
  let root = null;

  // ---------------------------------------------------------------- plumbing
  function token() {
    if (!state.token) {
      const meta = document.querySelector('meta[name="agent-os-token"]');
      state.token = meta ? meta.getAttribute('content') : '';
    }
    return state.token;
  }

  function requestId() { return 'ui_' + Math.random().toString(36).slice(2) + Date.now().toString(36); }

  async function call(op, args) {
    const response = await fetch('/api/shopping', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Agent-OS-Token': token() },
      body: JSON.stringify({ op, args: args || {}, request_id: requestId() }),
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(body.error || ('Request failed: ' + response.status));
    if (op === 'health') return body;
    if (!body.ok) {
      const e = body.error || {};
      const err = new Error(e.message || 'Shopping reported an error');
      err.hint = e.hint || '';
      err.code = e.code || '';
      throw err;
    }
    return body.result;
  }

  function h(tag, attrs, ...kids) {
    const node = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (v === null || v === undefined || v === false) continue;
      if (k === 'class') node.className = v;
      else if (k.startsWith('on')) node.addEventListener(k.slice(2), v);
      else node.setAttribute(k, v === true ? '' : String(v));
    }
    for (const kid of kids.flat()) {
      if (kid === null || kid === undefined || kid === false) continue;
      node.appendChild(typeof kid === 'string' || typeof kid === 'number' ? document.createTextNode(String(kid)) : kid);
    }
    return node;
  }

  const money = m => (m && typeof m.amount_minor === 'number') ? '$' + (m.amount_minor / 100).toFixed(2) : '—';
  const when = iso => { if (!iso) return 'never'; const d = new Date(iso); return isNaN(d) ? String(iso) : d.toLocaleString(); };
  function safeLink(url, label) {
    if (typeof url === 'string' && /^https?:\/\//i.test(url)) {
      return h('a', { href: url, target: '_blank', rel: 'noopener noreferrer' }, label || 'Open at retailer');
    }
    return h('span', { class: 'sp-muted' }, 'no link');
  }
  const badge = (text, kind) => h('span', { class: 'sp-badge sp-' + kind }, text);

  function originBadges(option) {
    const out = [];
    out.push(option.data_origin === 'fixture' ? badge('DEMO DATA - not a real store', 'demo') : badge('live source', 'ok'));
    const status = option.price_status;
    if (status === 'verified') out.push(badge('delivered cost complete', 'ok'));
    else if (status === 'incomplete') out.push(badge('cost incomplete: ' + (option.cost_missing || []).join(', '), 'warn'));
    else if (status === 'stale') out.push(badge('stale (' + Math.round((option.age_minutes || 0) / 60) + ' h old)', 'warn'));
    if (option.tax_basis && option.tax_basis !== 'quoted') out.push(badge('tax: ' + option.tax_basis, 'muted'));
    return out;
  }

  function showError(err) {
    const box = root.querySelector('.sp-notice');
    box.replaceChildren(h('div', { class: 'sp-error', role: 'alert' }, err.message || String(err)),
      err.hint ? h('div', { class: 'sp-muted' }, err.hint) : null);
  }
  function showOk(text) { root.querySelector('.sp-notice').replaceChildren(h('div', { class: 'sp-okmsg', role: 'status' }, text)); }
  function clearNotice() { root.querySelector('.sp-notice').replaceChildren(); }

  async function guarded(button, fn) {
    if (button) button.disabled = true;
    clearNotice();
    try { return await fn(); } catch (err) { showError(err); return null; } finally { if (button) button.disabled = false; }
  }

  // ------------------------------------------------------------------- views
  async function overview(body) {
    const [health, wishlist, opportunities, research] = await Promise.all([
      call('health'), call('shopping.wishlist.list').catch(() => []),
      call('shopping.opportunities').catch(() => []), call('shopping.research.list').catch(() => [])]);
    body.appendChild(statusBanner(health));
    const d = health.doctor;
    if (d) {
      body.appendChild(h('div', { class: 'sp-cards' },
        card('Wants', String(wishlist.length)), card('Watched', String(d.watching.watched)),
        card('Due now', String(d.watching.due_now)), card('Real sources', String(d.real_sources.length)),
        card('Last price check', when(d.watching.last_checked_at))));
    }
    body.appendChild(h('h3', null, 'Opportunities'));
    body.appendChild(opportunities.length ? opportunityList(opportunities.slice(0, 5))
      : h('p', { class: 'sp-muted' }, 'No opportunities yet. Add a want, turn on watching, and run the watcher.'));
    body.appendChild(h('h3', null, 'Recent research'));
    body.appendChild(research.length ? h('ul', null, research.slice(0, 5).map(r =>
      h('li', null, r.input + ' - ' + r.status + ' (' + r.items + ' item(s))')))
      : h('p', { class: 'sp-muted' }, 'No research yet.'));
  }

  function card(label, value) { return h('div', { class: 'sp-card' }, h('div', { class: 'sp-muted' }, label), h('div', { class: 'sp-big' }, value)); }

  function statusBanner(health) {
    if (!health.connected) {
      const e = health.error || {};
      return h('div', { class: 'sp-banner sp-bad', role: 'alert' }, h('strong', null, 'Shopping Agent is not connected. '),
        e.message || '', h('div', { class: 'sp-muted' }, e.hint || ''));
    }
    const d = health.doctor;
    if (!d) return h('div', { class: 'sp-banner sp-bad', role: 'alert' }, (health.error && health.error.message) || 'No diagnostics');
    const kids = [h('strong', null, d.ok ? 'Shopping Agent is working. ' : 'Shopping Agent needs attention. '),
      'Data: ' + d.data_mode + '. Live purchasing: ' + (d.live_purchases_active ? 'ON (unexpected)' : 'off - you check out manually.')];
    if (d.data_mode === 'demo') kids.push(h('div', null, badge('DEMO DATA', 'demo'), ' Results below are invented test data.'));
    (d.problems || []).forEach(p => kids.push(h('div', { class: 'sp-problem' }, 'Problem: ' + p)));
    (d.actions || []).forEach(a => kids.push(h('div', { class: 'sp-todo' }, 'To do: ' + a)));
    return h('div', { class: 'sp-banner ' + (d.ok ? 'sp-good' : 'sp-warnbox') }, kids);
  }

  function opportunityList(items) {
    return h('ul', { class: 'sp-list' }, items.map(o => h('li', null,
      h('div', null, h('strong', null, o.headline || o.opportunity_id)),
      h('div', { class: 'sp-muted' }, 'Quality ' + o.deal_quality + ' | timing ' + o.timing + ' | ' + String(o.trigger || '').replace(/_/g, ' ')
        + ' | ' + money(o.delivered_per_unit) + ' | detected ' + when(o.detected_at)),
      h('ul', null, (o.why || []).slice(0, 4).map(w => h('li', null, w))),
      h('div', { class: 'sp-muted' }, 'Sources: ' + ((o.provenance || []).map(p => p.source + (p.source_ref ? ' (' + p.source_ref + ')' : '')).join('; ') || 'none')))));
  }

  function researchView(body) {
    const text = h('textarea', { id: 'sp-text', rows: 3, placeholder: 'e.g. "Sonix WH-100 headphones, black, under $140" or paste a product link. One item per line for a project.' });
    const run = h('button', { class: 'primary', onclick: e => guarded(e.target, () => startResearch(text.value)) }, 'Research');
    body.appendChild(h('h3', null, 'Describe what you want'));
    body.appendChild(text);
    body.appendChild(h('div', null, run, h('span', { class: 'sp-muted' }, ' Searches your connected sources and compares delivered cost.')));
    body.appendChild(h('div', { id: 'sp-research-out', 'aria-live': 'polite' }));

    const f = {};
    const field = (key, label, ph) => h('label', null, label, f[key] = h('input', { placeholder: ph || '', id: 'sp-f-' + key }));
    body.appendChild(h('h3', null, 'Or add an exact item to the wishlist'));
    body.appendChild(h('div', { class: 'sp-form' },
      field('description', 'What', 'Sonix WH-100 headphones'), field('url', 'Product link (optional)', 'https://...'),
      field('target', 'Target price', '90'), field('max', 'Hard maximum, delivered', '110'),
      field('quantity', 'Quantity', '1'), field('variant', 'Variant (key=value, comma separated)', 'color=black'),
      h('label', null, 'Condition', f.cond = h('select', { id: 'sp-f-cond' },
        h('option', { value: 'new' }, 'New'), h('option', { value: 'new,open_box,refurbished' }, 'New or refurbished'),
        h('option', { value: 'new,open_box,refurbished,used' }, 'Anything incl. used'))),
      h('button', { class: 'primary', onclick: e => guarded(e.target, async () => {
        if (!f.description.value.trim()) throw new Error('Say what you want first.');
        const want = { description: f.description.value.trim(), search_query: f.description.value.trim() };
        if (f.url.value.trim()) want.links = [f.url.value.trim()];
        if (f.target.value.trim()) want.target_price = f.target.value.trim();
        if (f.max.value.trim()) want.max_delivered_price = f.max.value.trim();
        if (f.quantity.value.trim()) want.quantity = parseInt(f.quantity.value, 10) || 1;
        const variant = {};
        f.variant.value.split(',').map(s => s.trim()).filter(Boolean).forEach(pair => { const [k, v] = pair.split('='); if (k && v) variant[k.trim()] = v.trim(); });
        if (Object.keys(variant).length) want.desired_variant = variant;
        want.allowed_conditions = f.cond.value.split(',');
        await call('shopping.wishlist.add', { want });
        showOk('Added to your wishlist.');
        state.view = 'wishlist'; render();
      }) }, 'Add to wishlist')));
    if (state.research) renderResearch(state.research);
  }

  async function startResearch(text) {
    if (!text.trim()) throw new Error('Describe what you want first.');
    const started = await call('shopping.research.start', { text });
    state.research = { research_id: started.research_id, status: 'running' };
    renderResearch(state.research);
    pollResearch(started.research_id);
  }

  function pollResearch(id) {
    clearTimeout(state.pollTimer);
    state.pollTimer = setTimeout(async () => {
      try {
        const report = await call('shopping.research.get', { research_id: id });
        state.research = report;
        if (state.view === 'research') renderResearch(report);
        if (report.status === 'running') pollResearch(id);
      } catch (err) { showError(err); }
    }, 1500);
  }

  function renderResearch(report) {
    const out = root.querySelector('#sp-research-out');
    if (!out) return;
    if (report.status === 'running') { out.replaceChildren(h('p', null, 'Researching... checking your sources. This page updates by itself.')); return; }
    if (report.status === 'failed' || report.status === 'interrupted') {
      out.replaceChildren(h('div', { class: 'sp-error' }, 'Research ' + report.status + '. ' + (report.notes || []).join(' ')));
      return;
    }
    const kids = [h('h3', null, 'Results'), h('p', { class: 'sp-muted' }, 'Sources queried: ' + ((report.providers || []).join(', ') || 'none configured'))];
    (report.notes || []).forEach(n => kids.push(h('p', { class: 'sp-muted' }, n)));
    (report.questions || []).forEach(q => kids.push(h('p', null, 'Question: ' + q)));
    (report.items || []).forEach(entry => {
      kids.push(h('h4', null, entry.item.label));
      if (entry.summary) kids.push(h('p', null, entry.summary));
      if (!entry.options.length) kids.push(h('p', { class: 'sp-muted' }, 'Nothing found. Check Diagnostics for connected sources.'));
      entry.options.forEach(o => kids.push(optionCard(report, entry, o)));
    });
    out.replaceChildren(...kids);
  }

  function optionCard(report, entry, o) {
    return h('div', { class: 'sp-option' + (o.data_origin === 'fixture' ? ' sp-fixture' : '') },
      h('div', null, h('strong', null, o.title), ' ', h('span', { class: 'sp-muted' }, '(' + o.role.replace(/_/g, ' ') + ')')),
      h('div', null, o.retailer + ' | ' + o.condition + ' | delivered ' + o.delivered + ' | seller ' + o.seller),
      h('div', { class: 'sp-badges' }, originBadges(o)),
      h('div', { class: 'sp-muted' }, 'Observed ' + when(o.observed_at) + ' via ' + o.source),
      h('ul', null, (o.why || []).map(w => h('li', null, w))),
      h('div', null, safeLink(o.url), ' ',
        h('button', { onclick: e => guarded(e.target, async () => {
          await call('shopping.research.adopt', { research_id: report.research_id, item_id: entry.item.item_id, offer_id: o.offer_id });
          showOk('Saved to your wishlist.');
        }) }, 'Save to wishlist')));
  }

  async function wishlistView(body) {
    const wants = await call('shopping.wishlist.list');
    const watches = await call('shopping.watch.list').catch(() => []);
    const watched = new Set(watches.map(w => w.want_id));
    if (!wants.length) { body.appendChild(h('p', { class: 'sp-muted' }, 'Your wishlist is empty. Use Research & Add.')); return; }
    const table = h('table', { class: 'sp-table' }, h('thead', null, h('tr', null,
      ['', 'Item', 'Target / max', 'Best price', 'Last checked', 'Timing', ''].map(t => h('th', null, t)))));
    const tbody = h('tbody');
    wants.forEach(w => {
      const box = h('input', { type: 'checkbox', 'aria-label': 'Select ' + w.description, onchange: e => {
        e.target.checked ? state.selected.add(w.want_id) : state.selected.delete(w.want_id); } });
      box.checked = state.selected.has(w.want_id);
      const best = w.best_price ? (w.best_price + (w.best_offer && w.best_offer.retailer ? ' at ' + w.best_offer.retailer : '')) : 'not found yet';
      const isWatched = watched.has(w.want_id);
      tbody.appendChild(h('tr', null,
        h('td', null, box),
        h('td', null, h('strong', null, w.description), h('div', { class: 'sp-muted' }, (w.origin && w.origin.headline) || '')),
        h('td', null, (w.target || '—') + ' / ' + (w.hard_max || '—')),
        h('td', null, best, w.below_target ? badge('below target', 'ok') : null),
        h('td', null, w.last_checked ? when(w.last_checked) : 'never'),
        h('td', { class: 'sp-muted' }, (w.timing && w.timing.advice) || ''),
        h('td', null,
          h('button', { onclick: e => guarded(e.target, async () => { const r = await call('shopping.search', { want_id: w.want_id });
            showOk('Searched: ' + r.offers_found + ' offer(s) from ' + r.providers.length + ' source(s)' + (r.degraded ? ' - some sources failed, see Diagnostics' : '') + '.'); render(); }) }, 'Search now'),
          h('button', { onclick: e => guarded(e.target, async () => {
            await call(isWatched ? 'shopping.watch.update' : 'shopping.watch.add', { want_id: w.want_id, config: { enabled: !isWatched } });
            showOk(isWatched ? 'Watching paused.' : 'Watching on.'); render(); }) }, isWatched ? 'Pause watch' : 'Watch'),
          h('button', { onclick: e => guarded(e.target, async () => { const r = await call('shopping.price_history', { want_id: w.want_id });
            showHistory(w, r); }) }, 'Price history'),
          h('button', { onclick: e => guarded(e.target, async () => { await call('shopping.wishlist.remove', { want_id: w.want_id });
            state.selected.delete(w.want_id); render(); }) }, 'Remove'))));
    });
    table.appendChild(tbody);
    body.appendChild(table);
    body.appendChild(h('div', null,
      h('button', { onclick: e => guarded(e.target, async () => { const r = await call('shopping.watch.run');
        showOk('Watcher ran.' + (Array.isArray(r.opportunities) ? ' New opportunities: ' + r.opportunities.length + '.' : '')); render(); }) }, 'Run watcher now'),
      h('button', { class: 'primary', onclick: () => { if (!state.selected.size) { showError(new Error('Select at least one item first.')); return; } state.view = 'cart'; render(); } }, 'Build cart from selected')));
    body.appendChild(h('div', { id: 'sp-history' }));
  }

  function showHistory(want, hist) {
    const out = root.querySelector('#sp-history');
    const kids = [h('h3', null, 'Price history: ' + want.description)];
    if (!hist.variants || !hist.variants.length) kids.push(h('p', { class: 'sp-muted' }, 'No observations yet. Search or run the watcher first.'));
    (hist.variants || []).forEach(v => {
      const s = v.stats || {};
      kids.push(h('p', null, v.condition + ': ' + (s.sample_count || 0) + ' observation(s); low ' + money(s.historical_low)
        + ', high ' + money(s.historical_high) + ', recent median ' + money(s.recent_median)
        + (s.sample_count < 5 ? ' (thin history: treat deal quality with caution)' : '')));
      kids.push(h('ul', null, (v.series || []).slice(-10).map(p => h('li', null, p.day + ': ' + money({ amount_minor: p.value_minor }) + ' at ' + p.retailer + (p.in_stock ? '' : ' (out of stock)')))));
    });
    out.replaceChildren(...kids);
  }

  async function dealsView(body) {
    const items = await call('shopping.opportunities');
    body.appendChild(h('p', { class: 'sp-muted' }, 'Opportunities come from the watcher. Each one lists its evidence and source. Unverified promotions are not counted in the price.'));
    body.appendChild(items.length ? opportunityList(items.slice(0, 30)) : h('p', { class: 'sp-muted' }, 'Nothing yet. Watch an item and run the watcher.'));
  }

  async function cartView(body) {
    const ids = Array.from(state.selected);
    body.appendChild(h('p', { class: 'sp-muted' }, 'Nothing is bought here. You get retailer links and totals, check out yourself, then record the order.'));
    body.appendChild(h('button', { class: 'primary', onclick: e => guarded(e.target, async () => {
      if (!ids.length) throw new Error('Select items on the Wishlist tab first.');
      state.snapshot = await call('shopping.cart.create', { want_ids: ids });
      state.handoff = await call('shopping.checkout.handoff', { snapshot_id: state.snapshot.snapshot_id });
      render(); }) }, ids.length ? 'Build cart (' + ids.length + ' item(s))' : 'Build cart'));
    if (state.handoff) {
      const hf = state.handoff;
      body.appendChild(h('h3', null, 'Manual checkout - total ' + hf.delivered_total + (hf.expired ? ' (EXPIRED)' : '')));
      hf.caveats.forEach(c => body.appendChild(h('p', { class: 'sp-muted' }, c)));
      hf.retailers.forEach(r => body.appendChild(h('div', { class: 'sp-option' },
        h('strong', null, r.retailer), h('div', null, 'Subtotal ' + r.subtotal + ' + shipping ' + r.shipping + ' + est. tax ' + r.estimated_tax + ' = ' + r.total),
        r.notes.map(n => h('div', { class: 'sp-muted' }, n)),
        r.links.map(l => h('div', null, l.quantity + ' x ' + l.title + ' @ ' + l.unit_price + ' ', safeLink(l.url, 'Open checkout page'),
          l.stale ? badge('stale price', 'warn') : null, ' ', l.provider && /demo/.test(l.provider) ? badge('DEMO', 'demo') : null)))));
      body.appendChild(h('p', null, 'After you buy, record it on the Orders tab.'));
    }
  }

  async function ordersView(body) {
    const orders = await call('shopping.order.list');
    const f = {};
    const field = (k, l, p) => h('label', null, l, f[k] = h('input', { placeholder: p || '' }));
    body.appendChild(h('h3', null, 'Record a purchase you made yourself'));
    body.appendChild(h('div', { class: 'sp-form' }, field('retailer', 'Retailer', 'amazon.com'), field('title', 'Item', 'Sonix WH-100'),
      field('price', 'Unit price paid', '84.00'), field('qty', 'Quantity', '1'), field('ref', 'Order number (optional)', ''),
      h('button', { class: 'primary', onclick: e => guarded(e.target, async () => {
        if (!f.retailer.value.trim() || !f.title.value.trim() || !f.price.value.trim()) throw new Error('Retailer, item and price are required.');
        const wantId = state.selected.size === 1 ? Array.from(state.selected)[0] : undefined;
        await call('shopping.order.record', { order: { retailer: f.retailer.value.trim(), merchant_order_ref: f.ref.value.trim(),
          lines: [{ want_id: wantId, title: f.title.value.trim(), quantity: parseInt(f.qty.value, 10) || 1, unit_price: f.price.value.trim() }] } });
        showOk('Order recorded.'); render(); }) }, 'Record order')));
    body.appendChild(h('h3', null, 'Orders'));
    body.appendChild(orders.length ? h('ul', { class: 'sp-list' }, orders.map(o => h('li', null,
      h('strong', null, (o.retailer || 'unknown') + ' - ' + o.status), h('div', { class: 'sp-muted' }, 'Placed ' + when(o.placed_at) + ' | source ' + (o.source || 'unknown')),
      h('ul', null, (o.lines || []).map(l => h('li', null, l.quantity + ' x ' + l.title + ' @ ' + money(l.unit_price))))))) : h('p', { class: 'sp-muted' }, 'No orders recorded.'));
  }

  async function diagnosticsView(body) {
    const health = await call('health');
    body.appendChild(statusBanner(health));
    const d = health.doctor;
    if (!d) return;
    body.appendChild(h('p', { class: 'sp-muted' }, 'Contract ' + d.version + ' | home ' + d.home + ' | database ' + (d.database.readable ? 'readable' : 'NOT readable')
      + ' | audit chain ' + (d.audit_chain_valid ? 'valid' : 'INVALID')));
    const table = h('table', { class: 'sp-table' }, h('thead', null, h('tr', null,
      ['Source', 'Kind', 'Configured', 'Cost rule', 'Last success', 'Last error'].map(t => h('th', null, t)))));
    const tb = h('tbody');
    d.providers.forEach(p => tb.appendChild(h('tr', null, h('td', null, p.provider_id),
      h('td', null, p.simulated ? badge('DEMO', 'demo') : badge('real', 'ok')),
      h('td', null, p.configured ? 'yes' : (p.requires_credentials ? 'needs free API key' : 'no')),
      h('td', null, p.cost_gate_open ? 'open' : 'closed: ' + p.gate),
      h('td', null, when(p.last_success_at)), h('td', null, p.last_error || ''))));
    table.appendChild(tb);
    body.appendChild(d.providers.length ? table : h('p', { class: 'sp-muted' }, 'No sources are connected.'));
    if (d.last_research_problem) body.appendChild(h('p', { class: 'sp-error' }, 'Last research problem (' + d.last_research_problem.status + '): ' + (d.last_research_problem.notes || []).join(' ')));
    body.appendChild(h('h3', null, 'Repair'));
    body.appendChild(h('ul', null,
      h('li', null, 'Re-check: reload this tab.'),
      h('li', null, 'Command line: agent-shopping doctor   (add --live to probe each real source from your computer)'),
      h('li', null, 'Back up: agent-shopping backup     Restore: agent-shopping restore <file.zip> --force'),
      h('li', null, 'Restart: close this window and run Start-Shopping.ps1 again. Your data is kept.')));
  }

  // ------------------------------------------------------------------ shell
  async function render() {
    clearTimeout(state.pollTimer);
    const nav = root.querySelector('.sp-nav');
    nav.replaceChildren(...VIEWS.map(([key, label]) => h('button', {
      class: 'sp-navbtn' + (state.view === key ? ' on' : ''), 'aria-current': state.view === key ? 'page' : null,
      onclick: () => { state.view = key; clearNotice(); render(); } }, label)));
    const body = root.querySelector('.sp-body');
    body.replaceChildren(h('p', { class: 'sp-muted' }, 'Loading...'));
    const fresh = h('div');
    try {
      await ({ overview, research: researchView, wishlist: wishlistView, deals: dealsView, cart: cartView,
               orders: ordersView, diagnostics: diagnosticsView }[state.view])(fresh);
    } catch (err) {
      fresh.appendChild(h('div', { class: 'sp-error', role: 'alert' }, err.message || String(err)));
      if (err.hint) fresh.appendChild(h('div', { class: 'sp-muted' }, err.hint));
      if (err.code === 'not_installed' || err.code === 'contract_mismatch') fresh.appendChild(h('p', null, 'Open Diagnostics for repair steps.'));
    }
    body.replaceChildren(...fresh.childNodes);
    if (state.view === 'research' && state.research && state.research.status === 'running') pollResearch(state.research.research_id);
  }

  function activate() {
    document.querySelectorAll('.tab').forEach(t => { t.classList.remove('on'); t.setAttribute('aria-selected', 'false'); });
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('on'));
    const tab = document.getElementById('tab-shopping');
    tab.classList.add('on'); tab.setAttribute('aria-selected', 'true');
    document.getElementById('shopping-tab').classList.add('on');
    try { history.replaceState(null, '', '#shopping'); } catch (e) { /* cosmetic */ }
    render();
  }

  function deactivate() {
    document.getElementById('shopping-tab').classList.remove('on');
    const tab = document.getElementById('tab-shopping');
    tab.classList.remove('on'); tab.setAttribute('aria-selected', 'false');
    clearTimeout(state.pollTimer);
  }

  function init() {
    root = document.getElementById('shopping-tab');
    if (!root) return;
    root.append(h('div', { class: 'sp-nav', role: 'navigation', 'aria-label': 'Shopping sections' }),
                h('div', { class: 'sp-notice', 'aria-live': 'polite' }), h('div', { class: 'sp-body' }));
    document.getElementById('tab-shopping').addEventListener('click', activate);
    ['tab-work', 'tab-personal'].forEach(id => document.getElementById(id).addEventListener('click', deactivate));
    if (location.hash === '#shopping') activate();
  }

  return { init };
})();

document.addEventListener('DOMContentLoaded', () => ShoppingTab.init());
