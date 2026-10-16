const Executive = (() => {
  let conversationId = null;
  let rescueMode = false;
  let token = null;
  let pendingPolling = null;
  let chatInFlight = false;

  function initToken() {
    const meta = document.querySelector('meta[name="agent-os-token"]');
    if (meta) {
      token = meta.getAttribute('content');
    }
    if (!token || token === '{{TOKEN}}') {
      console.warn('No valid token found; API calls may fail');
    }
  }

  function getOrCreateConversationId() {
    if (!conversationId) {
      conversationId = sessionStorage.getItem('executive_conversation_id');
      if (!conversationId) {
        conversationId = 'conv_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
        sessionStorage.setItem('executive_conversation_id', conversationId);
      }
    }
    return conversationId;
  }

  function apiCall(method, endpoint, data = null, quiet = false) {
    const headers = {
      'Content-Type': 'application/json',
    };
    if (token && token !== '{{TOKEN}}') {
      headers['X-Agent-OS-Token'] = token;
    }

    const options = {
      method,
      headers,
    };

    if (data) {
      options.body = JSON.stringify(data);
    }

    return fetch(endpoint, options)
      .then(response => {
        if (!response.ok) {
          return response.json().catch(() => ({})).then(body => {
            const reason = body && (body.error || body.message);
            throw new Error(reason ? normalizeErrors(reason) : `API error: ${response.status} ${response.statusText}`);
          });
        }
        return response.json();
      })
      .catch(error => {
        console.error('API call failed:', error);
        if (!quiet) {
          showError(error.message);
        }
        throw error;
      });
  }

  function apiCallQuiet(method, endpoint, data = null) {
    return apiCall(method, endpoint, data, true);
  }

  function showBusy(show = true) {
    const busy = document.getElementById('busy');
    if (show) {
      busy.classList.remove('hidden');
    } else {
      busy.classList.add('hidden');
    }
  }

  function normalizeErrors(errors) {
    if (!errors) return '';
    return [].concat(errors).map(e =>
      typeof e === 'string' ? e : (e.provider ? e.provider + ': ' : '') + (e.error || e.message || JSON.stringify(e))
    ).join('; ');
  }

  const LOAD_NAMES = {
    applicants: 'applicants', mail: 'mail', documents: 'documents', projects: 'projects',
    calendar: 'your calendar', orchestrator: 'running work', brain_dump: 'quick notes',
  };
  let retryAction = null;

  // Plain-English summary of a failed load; the raw text only ever goes under Details.
  function friendlyLoadError(errors) {
    const list = [].concat(errors || []);
    const names = [];
    list.forEach(e => {
      const key = e && typeof e === 'object' ? (e.provider || e.source || e.name) : null;
      const label = key ? (LOAD_NAMES[key] || null) : null;
      if (label && !names.includes(label)) names.push(label);
    });
    const raw = normalizeErrors(errors);
    const what = names.length ? names.join(' and ') : 'some of your items';
    const missing = /not found|no such file|FileNotFound/i.test(raw);
    return `Couldn't load ${what}.` + (missing ? " A file this needs wasn't found." : ' Please try again.');
  }

  function showError(message, options) {
    const opts = options || {};
    const banner = document.getElementById('error-banner');
    if (!banner) return;
    const raw = normalizeErrors(message);
    banner.replaceChildren();
    banner.classList.remove('hidden');
    banner.appendChild(el('span', 'error-text', opts.text || "Something didn't work. Please try again."));
    retryAction = opts.retry === undefined ? loadItems : opts.retry;
    if (retryAction) {
      const retry = el('button', 'small', 'Retry');
      retry.type = 'button';
      retry.addEventListener('click', () => {
        const again = retryAction;
        clearError();
        if (again) again();
      });
      banner.appendChild(retry);
    }
    const close = el('button', 'small ghost', 'Dismiss');
    close.type = 'button';
    close.addEventListener('click', clearError);
    banner.appendChild(close);
    if (raw) {
      const details = el('details', 'error-details');
      details.appendChild(el('summary', null, 'Details'));
      details.appendChild(el('pre', null, raw));
      banner.appendChild(details);
    }
  }

  function clearError() {
    const banner = document.getElementById('error-banner');
    if (banner) {
      banner.replaceChildren();
      banner.classList.add('hidden');
    }
    retryAction = null;
  }

  function markAsks(btn) {
    btn.setAttribute('aria-label', btn.textContent + ' (asks before doing)');
    btn.title = 'Asks you to confirm first';
    return btn;
  }

  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = text;
    return node;
  }

  function findCompose(response) {
    if (!response || typeof response !== 'object') return null;
    if (response.compose && typeof response.compose === 'object') return response.compose;
    if (response.result && response.result.compose && typeof response.result.compose === 'object') {
      return response.result.compose;
    }
    return null;
  }

  function findPreview(response) {
    if (!response || typeof response !== 'object') return null;
    const raw = response.preview || (response.result && response.result.preview);
    if (!raw) return null;
    const token = response.confirm_token || (response.result && response.result.confirm_token);
    if (typeof raw === 'object') {
      return Object.assign({}, raw, { id: raw.id || token, data: raw });
    }
    return { id: token, title: 'Pending action', content: String(raw), data: {} };
  }

  function handleActResult(response, actionId, item) {
    if (!response) return;
    if (response.message) addChatMessage('agent', response.message);
    if (actionId === 'project.resume' && response.result && response.result.packet) renderResume(response.result.packet);
    const compose = findCompose(response);
    if (compose) showCompose(compose);
    const preview = findPreview(response);
    if (preview) {
      preview.action_id = preview.action_id || actionId;
      if (item && !preview.county) preview.county = (item.context && item.context.county) || null;
      showPreview(preview, actionId);
    }
    if (response.error) showError(response.error);
  }

  function runAction(item, actionId, params) {
    showBusy(true);
    clearError();
    return apiCall('POST', '/api/act', {
      conversation_id: getOrCreateConversationId(),
      item_id: item.id,
      action_id: actionId,
      params: params || {},
    })
      .then(response => {
        showBusy(false);
        handleActResult(response, actionId, item);
        return response;
      })
      .catch(error => {
        showBusy(false);
        throw error;
      });
  }

  function renderCountyOpenings(item, card) {
    const context = item.context || {};
    const applicants = context.applicants || [];
    const group = el('div', 'county-group');
    if (applicants.length === 0) {
      group.appendChild(el('div', 'muted', 'No applicants to review'));
    }
    applicants.forEach(applicant => {
      const row = el('button', 'applicant-row');
      row.type = 'button';
      const name = applicant.name || applicant.display_name || 'Applicant';
      row.appendChild(el('span', 'applicant-name', name));
      const bits = [];
      if (applicant.score !== undefined && applicant.score !== null) bits.push('score ' + applicant.score);
      if (applicant.recommendation) bits.push(applicant.recommendation);
      if (bits.length) row.appendChild(el('span', 'applicant-meta', bits.join(' · ')));
      row.addEventListener('click', () => openApplicantReview(item, applicant, card));
      group.appendChild(row);
    });
    const panel = el('div', 'review-panel hidden');
    panel.id = 'review-' + item.id;
    group.appendChild(panel);
    return group;
  }

  function openApplicantReview(item, applicant, card) {
    const panel = card.querySelector('.review-panel');
    if (!panel) return;
    const params = { applicant_ref: applicant.applicant_ref };
    runAction(item, 'applicant.review', params)
      .then(response => {
        const review = (response && response.result) || response || {};
        const decisions = review.available_decisions || [];
        panel.innerHTML = '';
        panel.classList.remove('hidden');
        panel.appendChild(el('div', 'review-title', review.name || applicant.name || 'Applicant'));
        panel.appendChild(el('div', 'review-label', 'AI suggestion - you decide'));
        const list = el('dl', 'review-fields');
        const addRow = (label, value) => {
          const items = [].concat(value === undefined || value === null ? [] : value).filter(v => v !== '');
          if (!items.length) return;
          list.appendChild(el('dt', null, label));
          const dd = el('dd');
          if (items.length > 1) {
            const ul = el('ul');
            items.forEach(v => ul.appendChild(el('li', null, String(v))));
            dd.appendChild(ul);
          } else {
            dd.textContent = String(items[0]);
          }
          list.appendChild(dd);
        };
        addRow('Score', review.score);
        addRow('AI suggestion', review.recommendation);
        addRow('Summary', review.summary);
        addRow('Strengths', review.strengths);
        addRow('Concerns', review.concerns);
        panel.appendChild(list);
        const buttons = el('div', 'item-options');
        decisions.forEach(decision => {
          const actionId = decision.action_id;
          if (!actionId) return;
          const btn = el('button', '', decision.label || actionId);
          btn.type = 'button';
          if (['decline', 'hold'].includes(decision.decision)) {
            btn.classList.add('option-consequential');
            markAsks(btn);
          }
          btn.addEventListener('click', () => {
            btn.disabled = true;
            runAction(item, actionId, { applicant_ref: applicant.applicant_ref })
              .then(() => loadItems())
              .catch(() => { /* error already shown */ })
              .finally(() => { btn.disabled = false; });
          });
          buttons.appendChild(btn);
        });
        panel.appendChild(buttons);
      })
      .catch(() => { /* error already shown */ });
  }

  function closeCompose() {
    const existing = document.getElementById('compose-panel');
    if (existing) existing.remove();
  }

  function showCompose(compose) {
    closeCompose();
    const panel = el('div', 'compose-panel');
    panel.id = 'compose-panel';
    panel.appendChild(el('div', 'compose-title', 'Compose email'));

    const status = el('div', 'compose-status');
    status.id = 'compose-status';

    function field(label, control) {
      const wrap = el('label', 'compose-field');
      wrap.appendChild(el('span', null, label));
      wrap.appendChild(control);
      panel.appendChild(wrap);
      return control;
    }

    if (compose.compose_id) panel.dataset.composeId = compose.compose_id;

    const fromSelect = document.createElement('select');
    fromSelect.id = 'compose-from';
    field('From', fromSelect);
    apiCallQuiet('GET', '/api/send/accounts')
      .then(response => {
        const accounts = (response && response.accounts) || [];
        accounts.forEach(account => {
          const option = el('option', null, account.label || account.account_id);
          option.value = account.account_id;
          if (compose.from_account ? account.account_id === compose.from_account : account.default) {
            option.selected = true;
          }
          fromSelect.appendChild(option);
        });
      })
      .catch(() => { /* From list unavailable; server default applies */ });

    const toInput = document.createElement('input');
    toInput.id = 'compose-to';
    toInput.value = [].concat(compose.to || []).join(', ');
    field('To', toInput);

    const subjectInput = document.createElement('input');
    subjectInput.id = 'compose-subject';
    subjectInput.value = compose.subject || '';
    field('Subject', subjectInput);

    const bodyInput = document.createElement('textarea');
    bodyInput.id = 'compose-body';
    bodyInput.rows = 12;
    bodyInput.value = compose.body || '';
    field('Body', bodyInput);

    panel.appendChild(status);

    const actions = el('div', 'compose-actions');
    const sendBtn = el('button', 'primary', 'Send');
    sendBtn.id = 'compose-send';
    sendBtn.type = 'button';
    sendBtn.addEventListener('click', () => {
      sendBtn.disabled = true;
      status.className = 'compose-status';
      status.textContent = 'Sending…';
      const payload = Object.assign({}, compose, {
        conversation_id: getOrCreateConversationId(),
        to: toInput.value.split(/[;,]/).map(s => s.trim()).filter(Boolean).join(', '),
        subject: subjectInput.value,
        body: bodyInput.value,
      });
      if (fromSelect.value) payload.from_account = fromSelect.value;
      apiCallQuiet('POST', '/api/send', payload)
        .then(response => {
          const failed = response && (response.error || response.sent === false ||
            response.status === 'error' || response.status === 'not_sent');
          if (failed) {
            status.className = 'compose-status compose-error';
            status.textContent = 'NOT SENT: ' + normalizeErrors(response.error || response.message || 'send failed');
            sendBtn.disabled = false;
            return;
          }
          status.className = 'compose-status compose-ok';
          status.textContent = 'Sent';
          addChatMessage('agent', 'Sent: ' + (payload.subject || '(no subject)'));
          if (response && response.record_error) {
            showError(response.record_error, { text: 'The email was sent, but the applicant’s status was not updated in the Dashboard.', retry: null });
            addChatMessage('agent', 'The email was sent, but the applicant’s status was not updated in the Dashboard.');
          }
          if (response && response.warning) {
            showError(response.warning, { text: 'The email was sent, with a warning.', retry: null });
            addChatMessage('agent', 'The email was sent, with a warning. See the banner at the top for details.');
          }
          closeCompose();
          loadItems();
        })
        .catch(error => {
          status.className = 'compose-status compose-error';
          status.textContent = 'NOT SENT: ' + error.message;
          sendBtn.disabled = false;
        });
    });
    actions.appendChild(sendBtn);

    const cancelBtn = el('button', 'ghost', 'Discard');
    cancelBtn.type = 'button';
    cancelBtn.addEventListener('click', () => {
      if (!compose.compose_id) {
        closeCompose();
        return;
      }
      apiCallQuiet('POST', '/api/dismiss', { compose_id: compose.compose_id })
        .catch(() => { /* still close locally */ })
        .then(closeCompose);
    });
    actions.appendChild(cancelBtn);
    panel.appendChild(actions);

    document.body.appendChild(panel);
    toInput.focus();
  }

  function textEl(tag, className, text) {
    const el = document.createElement(tag);
    if (className) el.className = className;
    el.textContent = text;
    return el;
  }

  function countsText(counts) {
    const entries = Object.entries(counts || {});
    if (entries.length === 0) return 'none';
    return entries.map(([k, v]) => k + ': ' + v).join(', ');
  }

  function renderMailCleanup(item) {
    const group = document.createElement('div');
    group.className = 'mail-cleanup';
    const context = item.context || {};
    const plan = context.plan;
    const spamFiltered = context.spam_filtered || {};
    const byAccount = spamFiltered.by_account || {};
    const spamFilteredCounts = Object.fromEntries(
      Object.entries(spamFiltered).filter(([k]) => k !== 'by_account')
    );
    if (!plan || Object.keys(plan).length === 0) {
      group.appendChild(textEl('div', 'muted', 'No plan yet'));
    } else {
      Object.keys(plan).forEach(account => {
        const acct = plan[account] || {};
        const categories = acct.categories || {};
        group.appendChild(textEl('div', 'mail-cleanup-account', account));
        if (byAccount[account]) {
          group.appendChild(textEl('div', 'mail-cleanup-account-filtered', 'Filtered: ' + countsText(byAccount[account])));
        }
        const table = document.createElement('table');
        table.className = 'mail-cleanup-table';
        const head = document.createElement('tr');
        ['Category', 'Count', 'Sample subjects', 'Target folder', ''].forEach(h => head.appendChild(textEl('th', '', h)));
        table.appendChild(head);
        Object.keys(categories).forEach(category => {
          const entry = categories[category] || {};
          const row = document.createElement('tr');
          row.appendChild(textEl('td', '', category));
          row.appendChild(textEl('td', '', String(entry.count || 0)));
          row.appendChild(textEl('td', '', (entry.samples || []).join(' | ')));
          row.appendChild(textEl('td', '', entry.target_folder || ''));
          const actionCell = document.createElement('td');
          if (entry.target_folder) {
            const btn = textEl('button', 'option-consequential mail-cleanup-apply', 'Apply ' + category);
            markAsks(btn);
            btn.addEventListener('click', () => handleMailOrganizeApply(item, account, category, btn));
            actionCell.appendChild(btn);
          }
          row.appendChild(actionCell);
          table.appendChild(row);
        });
        group.appendChild(table);
      });
    }
    group.appendChild(textEl('div', 'mail-cleanup-filtered', 'Spam filtered: ' + countsText(spamFilteredCounts)));
    return group;
  }

  function renderMailFiltered(item) {
    const group = document.createElement('div');
    group.className = 'mail-filtered';
    const context = item.context || {};
    const filtered = context.filtered || [];
    const counts = context.counts || {};
    group.appendChild(textEl('div', 'mail-filtered-counts', 'By reason: ' + countsText(counts)));
    const details = document.createElement('details');
    details.appendChild(textEl('summary', '', 'Filtered subjects (' + filtered.length + ')'));
    const list = document.createElement('ul');
    filtered.forEach(f => {
      const reasons = (f.reasons || []).join(', ');
      list.appendChild(textEl('li', '', (f.subject || '(no subject)') + ' — ' + reasons));
    });
    details.appendChild(list);
    group.appendChild(details);
    return group;
  }

  function renderBrainDumpClarification(item) {
    const group = document.createElement('div');
    group.className = 'item-options';
    const candidates = (item.context && item.context.candidates) || [];
    candidates.forEach(candidate => {
      const button = document.createElement('button');
      button.type = 'button';
      button.textContent = candidate;
      button.addEventListener('click', () => runAction(item, 'brain_dump.clarify', { project: candidate }).then(loadItems).catch(() => { /* error already shown */ }));
      group.appendChild(button);
    });
    const projectInput = document.createElement('input');
    projectInput.type = 'text';
    projectInput.placeholder = 'Project name';
    const setProject = document.createElement('button');
    setProject.type = 'button';
    setProject.textContent = 'Set project';
    setProject.addEventListener('click', () => {
      const project = projectInput.value.trim();
      if (project) runAction(item, 'brain_dump.clarify', { project }).then(loadItems).catch(() => { /* error already shown */ });
    });
    group.appendChild(projectInput);
    group.appendChild(setProject);
    return group;
  }

  function handleMailOrganizeApply(item, account, category, btn) {
    const payload = {
      item_id: item.id,
      action_id: 'mail.organize_apply',
      params: { account: account, category: category },
    };
    btn.disabled = true;
    showBusy(true);
    clearError();
    apiCall('POST', '/api/act', payload)
      .then(response => {
        showBusy(false);
        btn.disabled = false;
        if (response.confirm_token && response.preview) {
          const previewObj = {
            id: response.confirm_token,
            action_id: 'mail.organize_apply',
            title: 'Move ' + category + ' emails in ' + account + '?',
            content: JSON.stringify(response.preview, null, 2),
          };
          showPreview(previewObj, 'mail.organize_apply');
        } else if (response.message) {
          addChatMessage('agent', response.message);
        }
        loadItems();
      })
      .catch(() => {
        showBusy(false);
        btn.disabled = false;
      });
  }

  const documentDrafts = {};

  function renderDocumentQuestion(item) {
    const group = document.createElement('div');
    group.className = 'item-options';
    const input = document.createElement('textarea');
    input.rows = 2;
    input.placeholder = 'Your answer';
    input.setAttribute('aria-label', 'Your answer');
    const answer = document.createElement('button');
    answer.type = 'button';
    answer.textContent = 'Answer';
    answer.addEventListener('click', () => {
      const text = input.value.trim();
      if (!text) return;
      answer.disabled = true;
      runAction(item, 'document.answer', { answer: text })
        .then(loadItems)
        .catch(() => { answer.disabled = false; });
    });
    group.appendChild(input);
    group.appendChild(answer);
    return group;
  }

  function renderDocumentTask(item) {
    const docId = item.context && item.context.doc_id;
    const group = document.createElement('div');
    const draft = document.createElement('pre');
    draft.className = 'document-draft';
    draft.style.whiteSpace = 'pre-wrap';
    draft.textContent = documentDrafts[docId] || 'Press Save to see the full text before anything is written.';
    group.appendChild(draft);

    const changes = document.createElement('textarea');
    changes.rows = 2;
    changes.placeholder = 'What should change in this draft?';
    changes.setAttribute('aria-label', 'Requested changes');
    group.appendChild(changes);

    const buttons = document.createElement('div');
    buttons.className = 'item-options';
    const makeButton = (label, onClick, consequential) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.textContent = label;
      if (consequential) {
        btn.className = 'option-consequential';
        markAsks(btn);
      }
      btn.addEventListener('click', onClick);
      buttons.appendChild(btn);
    };
    makeButton('Propose changes', () => {
      const text = changes.value.trim();
      if (!text) {
        // No changes typed: preview the current draft and ask for confirmation.
        runAction(item, 'document.propose', {}).then(loadItems).catch(() => { /* error already shown */ });
        return;
      }
      runAction(item, 'document.answer', { changes: text })
        .then(response => {
          const result = response && response.result;
          if (result && result.draft) documentDrafts[docId] = result.draft;
          loadItems();
        })
        .catch(() => { /* error already shown */ });
    });
    makeButton('Save', () => {
      runAction(item, 'document.save', {}).catch(() => { /* error already shown */ });
    }, true);
    makeButton('Discard', () => {
      if (!window.confirm('Discard this draft without saving?')) return;
      runAction(item, 'document.discard', {}).then(loadItems).catch(() => { /* error already shown */ });
    });
    group.appendChild(buttons);
    return group;
  }

  const APPLICANT_KINDS = ['applicant_group', 'county_openings', 'openings_console'];

  // Applicant and county actions only make sense on applicant/county items; per-applicant
  // actions live in the review panel instead of on the card.
  function optionShownOnCard(item, option) {
    const id = option.action_id || '';
    if (id.startsWith('applicant.')) return false;
    if (id === 'coding.pause') return !(item.context && item.context.paused);
    if (id === 'coding.resume') return !!(item.context && item.context.paused);
    if (id === 'openings.event' || id.startsWith('county.')) return APPLICANT_KINDS.includes(item.kind);
    return true;
  }

  function renderItem(item) {
    const card = document.createElement('div');
    card.className = 'item-card';
    card.id = 'item-' + item.id;

    const title = document.createElement('div');
    title.className = 'item-title';
    title.textContent = item.title;
    card.appendChild(title);

    if (item.why) {
      const why = document.createElement('div');
      why.className = 'item-why';
      why.textContent = item.why;
      card.appendChild(why);
    }

    if (item.rank && item.rank.position) {
      const rank = document.createElement('div');
      rank.className = 'item-rank';
      rank.textContent = 'Priority ' + item.rank.position + ' of ' + item.rank.of;
      card.appendChild(rank);
    }

    const meta = document.createElement('div');
    meta.className = 'item-meta';
    if (item.age || item.due) {
      const timing = document.createElement('span');
      timing.textContent = item.age || item.due || '—';
      meta.appendChild(timing);
    }
    if (meta.children.length > 0) {
      card.appendChild(meta);
    }

    if (item.kind === 'coding_run' && item.context && item.context.total) {
      const bar = el('progress');
      bar.max = item.context.total;
      bar.value = item.context.passed || 0;
      bar.setAttribute('aria-label', (item.context.passed || 0) + ' of ' + item.context.total + ' tasks done');
      card.appendChild(bar);
    }

    if (item.kind === 'county_openings') {
      card.appendChild(renderCountyOpenings(item, card));
    } else if (item.kind === 'mail_cleanup') {
      card.appendChild(renderMailCleanup(item));
    } else if (item.kind === 'mail_filtered') {
      card.appendChild(renderMailFiltered(item));
    } else if (item.kind === 'brain_dump_clarification') {
      card.appendChild(renderBrainDumpClarification(item));
    } else if (item.kind === 'document_question') {
      card.appendChild(renderDocumentQuestion(item));
    } else if (item.kind === 'document_task') {
      card.appendChild(renderDocumentTask(item));
    }

    const ownsOptions = item.kind === 'document_question' || item.kind === 'document_task';
    if (!ownsOptions && item.options && item.options.length > 0) {
      const optionsDiv = document.createElement('div');
      optionsDiv.className = 'item-options';
      item.options.forEach(option => {
        if (item.kind === 'mail_cleanup' && option.action_id === 'mail.organize_apply') {
          return;
        }
        if (option.action_id === 'brain_dump.clarify') return;
        if (!optionShownOnCard(item, option)) return;
        const btn = document.createElement('button');
        btn.className = option.consequential ? 'option-consequential' : '';
        btn.textContent = option.action_id === 'item.snooze' ? 'Snooze until tomorrow' : option.label;
        if (option.consequential) markAsks(btn);
        btn.addEventListener('click', () => {
          if (option.action_id === 'item.dismiss' || option.action_id === 'item.snooze') {
            const snooze = option.action_id === 'item.snooze';
            btn.disabled = true;
            runAction(item, option.action_id, snooze ? { hours: 24 } : {})
              .then(() => {
                addChatMessage('agent', (snooze ? 'Snoozed until tomorrow: ' : 'Dismissed: ') + item.title);
                loadItems();
              })
              .catch(() => { btn.disabled = false; });
          } else if (option.action_id === 'brain_dump.stage_candidate' || option.action_id === 'project.resume'
              || option.action_id.startsWith('coding.')) {
            runAction(item, option.action_id, {}).then(loadItems).catch(() => { /* error already shown */ });
          } else {
            handleOptionClick(item, option);
          }
        });
        optionsDiv.appendChild(btn);
      });
      card.appendChild(optionsDiv);
    }

    return card;
  }

  function renderItems(items, quiet) {
    const workItems = items.filter(i => i.tab === 'work');
    const personalItems = items.filter(i => i.tab === 'personal');

    const workList = document.getElementById('work-items');
    const personalList = document.getElementById('personal-items');

    workList.innerHTML = '';
    personalList.innerHTML = '';

    if (workItems.length === 0) {
      if (!quiet) workList.innerHTML = '<div class="muted" style="padding: 16px;">Nothing waiting on you here</div>';
    } else {
      workItems.forEach(item => {
        workList.appendChild(renderItem(item));
      });
    }

    if (personalItems.length === 0) {
      if (!quiet) personalList.innerHTML = '<div class="muted" style="padding: 16px;">Nothing waiting on you here</div>';
    } else {
      personalItems.forEach(item => {
        personalList.appendChild(renderItem(item));
      });
    }
  }

  function handleOptionClick(item, option) {
    const convId = getOrCreateConversationId();
    const payload = {
      conversation_id: convId,
      item_id: item.id,
      action_id: option.action_id,
    };

    const buttons = document.querySelectorAll('.item-options button');
    buttons.forEach(btn => btn.disabled = true);

    showChatBusy(true);
    clearError();
    apiCall('POST', '/api/option', payload)
      .then(response => {
        showChatBusy(false);
        if (response.message) {
          addChatMessage('agent', response.message);
        }
        const compose = findCompose(response);
        if (compose) showCompose(compose);
        const preview = findPreview(response);
        if (preview) {
          showPreview(preview, option.action_id);
        }
        loadItems();
      })
      .catch(() => {
        showChatBusy(false);
        buttons.forEach(btn => btn.disabled = false);
      });
  }

  function addChatMessage(role, text) {
    const log = document.getElementById('chat-log');
    const bubble = document.createElement('div');
    bubble.className = 'bubble ' + role;
    bubble.textContent = text;
    log.appendChild(bubble);
    log.scrollTop = log.scrollHeight;
    const examples = document.getElementById('chat-examples');
    if (examples) examples.classList.add('hidden');
    return bubble;
  }

  function addChatError(text, details, retry) {
    const bubble = addChatMessage('agent error', text + ' ');
    bubble.setAttribute('role', 'alert');
    if (retry) {
      const again = el('button', 'small', 'Try again');
      again.type = 'button';
      again.addEventListener('click', () => { again.disabled = true; retry(); });
      bubble.appendChild(again);
    }
    if (details) {
      const more = el('details', 'error-details');
      more.appendChild(el('summary', null, 'Details'));
      more.appendChild(el('pre', null, details));
      bubble.appendChild(more);
    }
  }

  function showChatBusy(show) {
    const node = document.getElementById('chat-busy');
    if (node) node.classList.toggle('hidden', !show);
  }

  function setTodayCount(items) {
    const node = document.getElementById('today-count');
    if (!node) return;
    const n = items.length;
    node.textContent = n === 0 ? 'Nothing needs you right now.' :
      (n === 1 ? '1 thing needs you today.' : n + ' things need you today.');
  }

  function handleChatSend() {
    if (chatInFlight) return;

    const input = document.getElementById('chat-input');
    const send = document.getElementById('chat-send');
    const text = input.value.trim();
    if (!text) return;

    chatInFlight = true;
    input.disabled = true;
    send.disabled = true;
    showChatBusy(true);
    clearError();

    input.value = '';
    addChatMessage('you', text);

    const convId = getOrCreateConversationId();
    const retry = () => { input.value = text; handleChatSend(); };
    const unavailable = "The assistant isn't available right now. Your message wasn't lost —";
    apiCallQuiet('POST', '/api/chat', {
      conversation_id: convId,
      message: text,
    })
      .then(response => {
        if (response.error && !response.reply) {
          addChatError(unavailable, normalizeErrors(response.error), retry);
        } else if (response.message) {
          addChatMessage('agent', response.message);
        }
        const compose = findCompose(response);
        if (compose) showCompose(compose);
        const preview = findPreview(response);
        if (preview) showPreview(preview, 'chat');
        if (response.refresh || compose || preview) loadItems();
      })
      .catch(error => {
        addChatError(unavailable, error.message, retry);
      })
      .finally(() => {
        chatInFlight = false;
        input.disabled = false;
        send.disabled = false;
        showChatBusy(false);
        input.focus();
      });
  }

  function handleBrainDumpSend() {
    const input = document.getElementById('brain-dump-input');
    const send = document.getElementById('brain-dump-send');
    const text = input.value.trim();
    if (!text) return;
    const tab = activeTab();
    send.disabled = true;
    apiCall('POST', '/api/brain-dump', { text: text, tab: tab })
      .then(response => {
        if (response.message) addChatMessage('agent', response.message);
        input.value = '';
        loadItems();
      })
      .catch(() => { /* error already shown */ })
      .finally(() => { send.disabled = false; });
  }

  // Plain-English wording for a pending action: question, one-sentence consequence,
  // the button label and what to say once it is done.
  function describePreview(preview, actionId) {
    const data = (preview.data && typeof preview.data === 'object') ? preview.data : preview;
    const action = preview.action_id || actionId || '';
    const name = data.name || 'this applicant';
    const county = preview.county || data.county;
    const where = county ? ' (' + county + ')' : '';
    const text = preview.title && !/^[a-z_.-]+:/.test(preview.title) ? preview.title : '';
    switch (action) {
      case 'applicant.decline':
        return {
          title: 'Decline ' + name + where + '?',
          body: 'Their status will change to Denied in the Applicant Dashboard. No email is sent.',
          confirm: 'Decline applicant', success: name + ' declined.',
        };
      case 'applicant.hold':
        return {
          title: 'Put ' + name + where + ' on hold?',
          body: 'A hold note is added to the Applicant Dashboard. Their status does not change.',
          confirm: 'Put on hold', success: name + ' put on hold.',
        };
      case 'openings.event':
      case 'county.opening_change':
        return {
          title: 'Update openings' + (county ? ' for ' + county : '') + '?',
          body: 'This changes the number of open positions recorded in the Applicant Dashboard.',
          confirm: 'Update openings', success: 'Openings updated' + (county ? ' for ' + county : '') + '.',
        };
      case 'document.save':
        return {
          title: text || 'Save this document?',
          body: 'A new file is saved with exactly the text under Details. Nothing existing is overwritten.',
          confirm: 'Save document', success: 'Document saved.',
        };
      case 'document.propose':
        return {
          title: text || 'Mark this draft as ready?',
          body: 'The draft is marked as ready for saving. Nothing is written to disk yet.',
          confirm: 'Mark as ready', success: 'Draft marked as ready.',
        };
      case 'mail.organize_apply':
        return {
          title: text || 'Move these emails?',
          body: 'The matching emails are moved to their folder.',
          confirm: 'Move emails', success: 'Emails moved.',
        };
      case 'orchestrator.approve_gate':
        return { title: 'Approve this step?', body: 'The paused work carries on.', confirm: 'Approve', success: 'Approved.' };
      case 'orchestrator.decline_gate':
        return { title: 'Decline this step?', body: 'The paused work does not carry on.', confirm: 'Decline', success: 'Declined.' };
      case 'coding.start':
        return {
          title: 'Start this coding run?',
          body: 'Starts an orchestrator run that plans, codes, tests and reviews on its own branch; nothing is merged without you.',
          confirm: 'Start coding', success: 'Coding run started. Follow it on the Today list or the Runs tab.',
        };
      case 'coding.stop':
        return { title: 'Stop this coding run?', body: 'The run stops and its workers are cancelled.', confirm: 'Stop run', success: 'Run stopped.' };
      case 'command-center.cloud':
        return {
          title: text || 'Start this task in the cloud?',
          body: 'The task is sent to Claude in the cloud and starts running.',
          confirm: 'Start task', success: 'Task started.',
        };
      default:
        return {
          title: text || 'Go ahead with this change?',
          body: 'Nothing changes until you say so. Open Details to see exactly what will happen.',
          confirm: 'Go ahead', success: 'Done.',
        };
    }
  }

  function showPreview(preview, actionId) {
    const container = document.getElementById('pending-previews');
    const card = document.createElement('div');
    card.className = 'preview-card';
    card.id = 'preview-' + (preview.id || actionId + '_' + Date.now());
    const copy = describePreview(preview, actionId);
    preview.copy = copy;
    card.setAttribute('role', 'alertdialog');
    card.setAttribute('aria-labelledby', card.id + '-title');
    card.setAttribute('aria-describedby', card.id + '-body');

    const title = document.createElement('div');
    title.className = 'preview-title';
    title.id = card.id + '-title';
    title.textContent = copy.title;
    card.appendChild(title);

    const body = document.createElement('div');
    body.className = 'preview-body';
    body.id = card.id + '-body';
    body.textContent = copy.body;
    card.appendChild(body);

    const detailText = preview.content ||
      (preview.data && Object.keys(preview.data).length ? JSON.stringify(preview.data, null, 2) : '');
    if (detailText) {
      const details = document.createElement('details');
      details.className = 'preview-details';
      details.appendChild(el('summary', null, 'Details'));
      details.appendChild(el('div', 'preview-content', detailText));
      card.appendChild(details);
    }

    const actions = document.createElement('div');
    actions.className = 'preview-actions';

    const confirmBtn = document.createElement('button');
    confirmBtn.className = 'primary';
    confirmBtn.textContent = copy.confirm;
    confirmBtn.addEventListener('click', () => {
      handleConfirm(preview, card);
    });
    actions.appendChild(confirmBtn);

    const cancelBtn = document.createElement('button');
    cancelBtn.className = 'ghost';
    cancelBtn.textContent = 'Keep as is';
    cancelBtn.addEventListener('click', () => {
      handleDismiss(preview, card);
    });
    actions.appendChild(cancelBtn);

    card.appendChild(actions);
    container.appendChild(card);
    const active = document.activeElement;
    if (!active || !['INPUT', 'TEXTAREA'].includes(active.tagName)) confirmBtn.focus();
  }

  function handleConfirm(preview, cardElement) {
    const buttons = cardElement.querySelectorAll('.preview-actions button');
    buttons.forEach(btn => btn.disabled = true);

    const convId = getOrCreateConversationId();
    apiCall('POST', '/api/confirm', {
      conversation_id: convId,
      preview_id: preview.id,
    })
      .then(response => {
        cardElement.remove();
        const success = preview.copy && preview.copy.success;
        const message = (success && success !== 'Done.') ? success : (response.message || success);
        if (message) {
          addChatMessage('agent', message);
        }
        loadItems();
      })
      .catch(() => {
        buttons.forEach(btn => btn.disabled = false);
      });
  }

  function handleDismiss(preview, cardElement) {
    const buttons = cardElement.querySelectorAll('.preview-actions button');
    buttons.forEach(btn => btn.disabled = true);

    const convId = getOrCreateConversationId();
    apiCall('POST', '/api/dismiss', {
      conversation_id: convId,
      preview_id: preview.id,
    })
      .then(() => {
        cardElement.remove();
        loadItems();
      })
      .catch(() => {
        buttons.forEach(btn => btn.disabled = false);
      });
  }

  function pollPending() {
    const convId = getOrCreateConversationId();
    apiCallQuiet('POST', '/api/pending', {
      conversation_id: convId,
    })
      .then(response => {
        const container = document.getElementById('pending-previews');
        const currentIds = new Set();

        if (response.previews && Array.isArray(response.previews)) {
          response.previews.forEach(preview => {
            currentIds.add('preview-' + preview.id);
            const existing = document.getElementById('preview-' + preview.id);
            if (!existing) {
              showPreview(preview, 'pending');
            }
          });
        }

        if (response.composes && Array.isArray(response.composes) &&
            !document.getElementById('compose-panel')) {
          const next = response.composes.find(c => c && c.compose_id);
          if (next) showCompose(next);
        }

        const allCards = container.querySelectorAll('.preview-card');
        allCards.forEach(card => {
          if (!currentIds.has(card.id)) {
            card.remove();
          }
        });
      })
      .catch(() => {
        /* fail silently on connection issues */
      });
  }

  function startPolling() {
    if (pendingPolling) {
      clearInterval(pendingPolling);
    }
    pendingPolling = setInterval(pollPending, 3000);
  }

  function activeTab() {
    return document.getElementById('tab-personal').getAttribute('aria-selected') === 'true' ? 'personal' : 'work';
  }

  function renderResume(packet) {
    const lines = [];
    const addField = (label, value) => {
      if (value !== null && value !== undefined && value !== '') lines.push(label + value);
    };
    const project = packet.project;
    const status = packet.status;
    if (project !== null && project !== undefined && project !== '' && status !== null && status !== undefined && status !== '') {
      lines.push('Resume ' + project + ' (' + status + ')');
    } else if (project !== null && project !== undefined && project !== '') {
      lines.push('Resume ' + project);
    }
    addField('Goal: ', packet.goal);
    addField('Where you left off: ', packet.where_you_left_off);
    if (packet.next_action !== null && packet.next_action !== undefined && packet.next_action !== '') {
      const source = packet.next_action_source;
      const hasSource = source !== null && source !== undefined && source !== '';
      lines.push('Next action: ' + packet.next_action + (hasSource ? ' [' + source + ']' : ''));
    }
    const loops = packet.open_loops || {};
    [['blockers', 'Blockers: '], ['waiting_on', 'Waiting on: '], ['decisions_needed', 'Decisions: ']].forEach(([key, label]) => {
      const values = Array.isArray(loops[key]) ? loops[key].filter(value => value !== null && value !== undefined && value !== '') : [];
      if (values.length) lines.push(label + values.join('; '));
    });
    if (typeof packet.age_days === 'number') lines.push('Age: ' + packet.age_days + ' days');
    if (packet.truncated === true) lines.push('(truncated)');
    if (lines.length) addChatMessage('agent', lines.join('\n'));
  }

  function renderRescue(result, items) {
    const panel = document.getElementById('rescue-panel');
    panel.textContent = '';
    panel.classList.remove('hidden');
    const action = result.action;
    panel.appendChild(textEl('div', 'item-title', action ? action.title : 'Nothing urgent right now'));
    if (action && action.project) panel.appendChild(textEl('div', 'item-meta', 'Project: ' + action.project));
    if (action && action.due) panel.appendChild(textEl('div', 'item-meta', 'Due: ' + action.due));
    if (result.why) panel.appendChild(textEl('div', 'item-why', result.why));
    if (result.then) panel.appendChild(textEl('div', 'item-why', result.then));
    const others = result.suppressed || 0;
    if (others > 0) {
      panel.appendChild(textEl('div', 'muted', others === 1
        ? '1 other thing is waiting — showing just one.'
        : `${others} other things are waiting — showing just one.`));
    }
    const shown = (result.item_id !== undefined && result.item_id !== null)
      ? items.filter(i => String(i.id) === String(result.item_id)) : [];
    // Nothing to list means no empty-list message either; the panel above says it all.
    renderItems(shown, true);
    if (result.errors && [].concat(result.errors).length) {
      showError(result.errors, { text: friendlyLoadError(result.errors) });
    }
  }

  function loadItems() {
    showBusy(true);
    if (rescueMode) {
      Promise.all([
        apiCall('GET', '/api/items'),
        apiCall('GET', '/api/rescue?tab=' + encodeURIComponent(activeTab())),
      ]).then(([itemsResponse, result]) => {
        showBusy(false);
        setTodayCount(itemsResponse.items || []);
        renderRescue(result, itemsResponse.items || []);
      }).catch(() => { showBusy(false); });
      return;
    }
    document.getElementById('rescue-panel').classList.add('hidden');
    apiCall('GET', '/api/items')
      .then(response => {
        showBusy(false);
        if (response.items) {
          setTodayCount(response.items);
          renderItems(response.items);
        }
        if (response.errors && [].concat(response.errors).length) {
          showError(response.errors, { text: friendlyLoadError(response.errors) });
        } else {
          clearError();
        }
      })
      .catch(() => {
        showBusy(false);
      });
  }

  function setupTabs() {
    const tabWork = document.getElementById('tab-work');
    const tabPersonal = document.getElementById('tab-personal');
    const workTab = document.getElementById('work-tab');
    const personalTab = document.getElementById('personal-tab');
    const rescueToggle = document.getElementById('rescue-toggle');
    rescueToggle.addEventListener('click', () => {
      rescueMode = !rescueMode;
      rescueToggle.setAttribute('aria-pressed', String(rescueMode));
      rescueToggle.classList.toggle('on', rescueMode);
      loadItems();
    });

    function selectTab(personal) {
      const [on, off, onPanel, offPanel] = personal
        ? [tabPersonal, tabWork, personalTab, workTab] : [tabWork, tabPersonal, workTab, personalTab];
      on.classList.add('on');
      off.classList.remove('on');
      on.setAttribute('aria-selected', 'true');
      off.setAttribute('aria-selected', 'false');
      on.tabIndex = 0;
      off.tabIndex = -1;
      onPanel.classList.add('on');
      offPanel.classList.remove('on');
      if (rescueMode) loadItems();
    }

    tabWork.addEventListener('click', () => selectTab(false));
    tabPersonal.addEventListener('click', () => selectTab(true));
    [tabWork, tabPersonal].forEach(tab => {
      tab.addEventListener('keydown', event => {
        const keys = { ArrowRight: 'next', ArrowLeft: 'next', Home: 'work', End: 'personal' };
        const move = keys[event.key];
        if (!move) return;
        event.preventDefault();
        const personal = move === 'next' ? tab === tabWork : move === 'personal';
        selectTab(personal);
        (personal ? tabPersonal : tabWork).focus();
      });
    });
  }

  function setupExamples() {
    document.querySelectorAll('#chat-examples button').forEach(chip => {
      chip.addEventListener('click', () => {
        const input = document.getElementById('chat-input');
        input.value = chip.dataset.fill
          || (/^start a coding task$/i.test(chip.textContent.trim()) ? 'Start a coding task: ' : chip.textContent);
        input.focus();
      });
    });
  }

  function setupChat() {
    const chatInput = document.getElementById('chat-input');
    const chatSend = document.getElementById('chat-send');

    chatSend.addEventListener('click', handleChatSend);
    document.getElementById('brain-dump-send').addEventListener('click', handleBrainDumpSend);
    chatInput.addEventListener('keypress', event => {
      if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        handleChatSend();
      }
    });
  }

  const hub = { providers: [], projects: [], id: null, record: null, sending: new Set() };
  const byId = id => document.getElementById(id);

  function button(label, action, className) {
    const node = el('button', className || '', label);
    node.type = 'button';
    node.addEventListener('click', () => Promise.resolve().then(action).catch(error => showError(error.message)));
    return node;
  }

  function vendorLink(url, label) {
    const node = el('a', '', label || url);
    try {
      const parsed = new URL(url);
      if (parsed.protocol === 'https:' && ['claude.ai', 'chatgpt.com', 'nano-gpt.com', 'openrouter.ai', 'github.com'].includes(parsed.hostname)
          && !parsed.username && !parsed.password) {
        node.href = parsed.href;
        node.target = '_blank';
        node.rel = 'noopener noreferrer';
      }
    } catch (_) { /* Invalid saved links remain plain text. */ }
    return node;
  }

  function projectChoices() {
    const select = byId('hub-project');
    const current = select.value;
    select.replaceChildren(el('option', '', 'No project'));
    select.firstChild.value = '';
    hub.projects.forEach(project => {
      const option = el('option', '', project.name + (project.sensitive ? ' (sensitive)' : ''));
      option.value = project.id;
      select.appendChild(option);
    });
    select.value = current;
  }

  function providerChoices() {
    const project = hub.projects.find(p => p.id === byId('hub-project').value);
    const select = byId('hub-provider');
    const current = select.value;
    select.replaceChildren();
    hub.providers.forEach(provider => {
      const option = el('option', '', provider.label + ' · ' + provider.headroom);
      option.value = provider.id;
      option.disabled = Boolean(project && project.sensitive && !provider.sensitive_ok);
      if (option.disabled) option.title = 'Sensitive projects stay on approved subscription or local providers';
      select.appendChild(option);
    });
    const available = Array.from(select.options).find(p => p.value === current && !p.disabled)
      || Array.from(select.options).find(p => !p.disabled);
    select.value = available ? available.value : '';
    modelChoices();
  }

  function modelChoices() {
    const provider = hub.providers.find(p => p.id === byId('hub-provider').value);
    const select = byId('hub-model');
    const current = select.value;
    select.replaceChildren();
    ((provider && provider.models) || []).forEach(model => {
      const option = el('option', '', model);
      option.value = model;
      select.appendChild(option);
    });
    select.value = provider && provider.models.includes(current) ? current : ((provider && provider.default_model) || '');
    hubControls();
  }

  function hubControls() {
    const busy = hub.sending.has(hub.id);
    const provider = byId('hub-provider').selectedOptions[0];
    ['hub-project', 'hub-provider', 'hub-model'].forEach(id => { byId(id).disabled = Boolean(hub.record) || busy; });
    byId('hub-send').disabled = busy || !byId('hub-model').value || !provider || provider.disabled;
    byId('hub-delete').disabled = !hub.record || busy;
    byId('hub-status').textContent = busy ? 'Waiting for reply…' : '';
  }

  function renderHubLog(turns) {
    const log = byId('hub-log');
    log.replaceChildren();
    (turns || []).forEach(turn => {
      const message = el('div', 'hub-message ' + (turn.role === 'user' ? 'user' : 'assistant'));
      message.appendChild(el('strong', '', turn.role === 'user' ? 'You' : 'Model'));
      message.appendChild(el('div', '', turn.text));
      if (turn.at) message.appendChild(el('div', 'muted', new Date(turn.at).toLocaleString()));
      log.appendChild(message);
    });
    log.scrollTop = log.scrollHeight;
  }

  async function hubConversations() {
    const rows = await apiCall('GET', '/api/chat/conversations');
    const list = byId('hub-conversations');
    list.replaceChildren();
    rows.forEach(row => list.appendChild(button(row.title + ' · ' + row.provider, async () => {
      const record = await apiCall('GET', '/api/chat/conversation?id=' + encodeURIComponent(row.id));
      hub.id = row.id;
      hub.record = record;
      byId('hub-project').value = record.project || '';
      providerChoices();
      byId('hub-provider').value = record.provider;
      modelChoices();
      byId('hub-model').value = record.model;
      renderHubLog(record.turns);
      hubControls();
      await hubConversations();
    }, row.id === hub.id ? 'on' : '')));
    if (!rows.length) list.appendChild(el('p', 'muted', 'No saved conversations yet.'));
  }

  function newHubConversation() {
    hub.id = 'chat_' + crypto.randomUUID();
    hub.record = null;
    byId('hub-input').value = '';
    renderHubLog([]);
    providerChoices();
    hubConversations().catch(() => {});
  }

  async function loadHub() {
    const [providers, projects] = await Promise.all([
      apiCall('GET', '/api/chat/providers'), apiCall('GET', '/api/projects'),
    ]);
    hub.providers = providers;
    hub.projects = projects;
    projectChoices();
    if (!hub.id) newHubConversation();
    else if (!hub.record) providerChoices();
    await hubConversations();
    hubControls();
  }

  async function hubSend() {
    const text = byId('hub-input').value.trim();
    const id = hub.id;
    if (!text || hub.sending.has(id)) return;
    const body = { conversation_id: id, text, provider: byId('hub-provider').value,
      model: byId('hub-model').value, project: byId('hub-project').value || null };
    hub.sending.add(id);
    byId('hub-input').value = '';
    hubControls();
    renderHubLog([...(hub.record ? hub.record.turns : []), {role: 'user', text}]);
    try {
      const result = await apiCall('POST', '/api/chat/send', body);
      if (result.error) throw new Error(result.error);
      if (hub.id === id) {
        hub.record = await apiCall('GET', '/api/chat/conversation?id=' + encodeURIComponent(id));
        renderHubLog(hub.record.turns);
      }
      await hubConversations();
      await pollPending();
    } catch (error) {
      if (hub.id === id) byId('hub-input').value = text;
      showError(error.message);
    } finally {
      hub.sending.delete(id);
      hubControls();
    }
  }

  async function loadProjects() {
    hub.projects = await apiCall('GET', '/api/projects');
    const list = byId('projects-list');
    list.replaceChildren();
    hub.projects.forEach(project => {
      const card = el('section', 'card');
      card.appendChild(el('h2', '', project.name + (project.sensitive ? ' · sensitive' : '')));
      card.appendChild(el('div', 'muted', project.path || 'Local checkout missing'));
      if (project.git) {
        const git = project.git;
        card.appendChild(el('div', '', `${git.branch || 'No branch'} · ${git.dirty} dirty · ahead ${git.ahead ?? '?'} / behind ${git.behind ?? '?'}`));
      }
      if (project.handoff) {
        const summary = el('details', 'project-handoff');
        summary.appendChild(el('summary', '', 'Latest handoff · ' + (project.handoff.created_at || '')));
        ['completed', 'remaining', 'decisions', 'validation'].forEach(key => {
          if (project.handoff[key]) summary.appendChild(el('p', '', key + ':\n' + [].concat(project.handoff[key]).join('\n')));
        });
        card.appendChild(summary);
      }
      [['claude', 'claude_sessions'], ['codex', 'codex_sessions'], ['cloud', 'cloud_sessions']].forEach(([kind, field]) => {
        card.appendChild(el('strong', '', kind === 'cloud' ? 'Claude cloud' : kind === 'claude' ? 'Claude' : 'Codex'));
        if (!project[field].length) card.appendChild(el('div', 'muted', 'No sessions'));
        project[field].forEach(session => {
          const id = session.id || session.session_id;
          const row = el('div', 'session-row');
          row.appendChild(el('span', '', id + ' · ' + (session.modified_at || session.at || '')));
          const resume = button(kind === 'cloud' ? 'Teleport' : 'Resume', () => apiCall('POST', '/api/projects/resume',
            {kind, session_id: id, project: project.id}));
          resume.disabled = !project.path;
          row.appendChild(resume);
          if (session.url) row.appendChild(vendorLink(session.url, 'Open session'));
          card.appendChild(row);
        });
      });
      const compose = el('div', 'cloud-task');
      const label = el('label', '', 'Task for Claude cloud');
      const input = el('textarea');
      input.rows = 2;
      label.appendChild(input);
      compose.appendChild(label);
      const preview = button('Preview cloud task', async () => {
        if (!input.value.trim()) return;
        preview.disabled = true;
        try {
          const result = await apiCall('POST', '/api/cloud/preview', {project: project.id, task: input.value.trim()});
          showPreview({id: result.confirm_token, title: 'Claude cloud · ' + project.name,
            content: JSON.stringify(result.preview, null, 2)}, 'command-center.cloud');
        } finally { preview.disabled = project.sensitive || !project.path; }
      });
      preview.disabled = project.sensitive || !project.path;
      if (project.sensitive) preview.title = 'Sensitive projects cannot use cloud sessions';
      compose.appendChild(preview);
      card.appendChild(compose);
      const coding = el('div', 'cloud-task');
      const goalLabel = el('label', '', 'Goal for an orchestrator coding run');
      const goalInput = el('textarea');
      goalInput.rows = 2;
      goalLabel.appendChild(goalInput);
      coding.appendChild(goalLabel);
      const startCoding = button('Start coding task', async () => {
        if (!goalInput.value.trim()) return;
        startCoding.disabled = true;
        try {
          const result = await apiCall('POST', '/api/coding/start', {project: project.id, repo: project.id, goal: goalInput.value.trim()});
          showPreview({...result.preview, id: result.confirm_token, action_id: 'coding.start',
            title: 'Coding run · ' + project.name}, 'coding.start');
        } finally { startCoding.disabled = !project.path; }
      });
      startCoding.disabled = !project.path;
      coding.appendChild(startCoding);
      card.appendChild(coding);
      list.appendChild(card);
    });
    if (!hub.projects.length) list.appendChild(el('p', 'muted', 'No registered projects.'));
  }

  async function loadUsage() {
    const usage = await apiCall('GET', '/api/usage');
    const plans = byId('usage-plans');
    plans.replaceChildren();
    (usage.plans || []).forEach(plan => {
      const card = el('section', 'card');
      card.appendChild(el('h2', '', plan.label));
      card.appendChild(el('strong', 'state-' + plan.state, plan.state || 'unknown'));
      if (plan.detail) card.appendChild(el('p', 'muted', plan.detail));
      (plan.windows || []).forEach(window => {
        const used = typeof window.used === 'number' ? Math.max(0, Math.min(1, window.used)) : null;
        const label = el('label', '', (window.name || window.id || window.window || 'Usage window') +
          (used === null ? ' · unknown' : ` · ${Math.round(used * 100)}% used`));
        if (used !== null) {
          const bar = el('progress', 'usage-meter');
          bar.max = 1;
          bar.value = used;
          bar.setAttribute('aria-label', label.textContent);
          label.appendChild(bar);
        }
        card.appendChild(label);
        if (window.resets_at) card.appendChild(el('div', 'muted', 'Resets ' + new Date(window.resets_at).toLocaleString()));
      });
      plans.appendChild(card);
    });
    const free = usage.free || {};
    byId('usage-free').textContent = free.error || `${free.daily_left ?? '?'} / ${free.daily_allowance ?? '?'} requests left today · ` +
      `${free.minute_left ?? '?'} left this minute · resets ${free.reset_at ? new Date(free.reset_at).toLocaleString() : '?'}`;
    const extras = byId('usage-extras');
    extras.replaceChildren();
    (usage.extras || []).forEach(extra => {
      const card = el('div', 'card');
      card.appendChild(el('strong', '', extra.title));
      card.appendChild(el('div', 'muted', extra.status + (extra.expires ? ' · expires ' + new Date(extra.expires).toLocaleString() : '')));
      card.appendChild(el('div', '', extra.applies_to));
      const redeem = extra.redeem || {};
      const open = button('Open', () => apiCall('POST', '/api/open-url', {url: redeem.target}));
      open.disabled = redeem.kind !== 'url';
      open.title = redeem.label || '';
      card.appendChild(open);
      if (redeem.kind === 'terminal') card.appendChild(el('div', 'muted', redeem.label));
      const mark = button('Mark used', async () => {
        await apiCall('POST', '/api/extras', {id: extra.id, status: 'used'});
        await loadUsage();
      });
      mark.disabled = extra.status === 'used';
      card.appendChild(mark);
      extras.appendChild(card);
    });
    const advice = byId('usage-advice');
    advice.replaceChildren();
    (usage.advice || []).forEach(tip => advice.appendChild(el('p', '', tip.message)));
    if (!(usage.advice || []).length) advice.appendChild(el('p', 'muted', 'No advice right now.'));
    const clouds = byId('usage-cloud');
    clouds.replaceChildren();
    (usage.cloud_sessions || []).forEach(session => {
      const row = el('div', 'session-row');
      row.appendChild(vendorLink(session.url, session.session_id));
      row.appendChild(el('span', 'muted', session.branch + ' · ' + (session.at || '')));
      clouds.appendChild(row);
    });
    if (!(usage.cloud_sessions || []).length) clouds.appendChild(el('p', 'muted', 'No cloud sessions yet.'));
  }

  function setupCommandCenter() {
    const names = ['today', 'projects', 'runs', 'chat', 'usage'];
    function select(name) {
      names.forEach(key => {
        byId('cc-' + key).classList.toggle('hidden', key !== name);
        const tab = byId('cc-tab-' + key);
        tab.classList.toggle('on', key === name);
        tab.setAttribute('aria-selected', String(key === name));
        tab.tabIndex = key === name ? 0 : -1;
      });
      clearError();
      const loader = {projects: loadProjects, chat: loadHub, usage: loadUsage}[name];
      if (loader) loader().catch(() => {});
    }
    names.forEach((name, index) => {
      const tab = byId('cc-tab-' + name);
      tab.addEventListener('click', () => select(name));
      tab.addEventListener('keydown', event => {
        const moves = {ArrowRight: (index + 1) % names.length, ArrowLeft: (index + names.length - 1) % names.length, Home: 0, End: names.length - 1};
        if (moves[event.key] !== undefined) {
          event.preventDefault();
          const next = names[moves[event.key]];
          select(next);
          byId('cc-tab-' + next).focus();
        }
      });
    });
    byId('projects-refresh').addEventListener('click', () => loadProjects().catch(() => {}));
    byId('usage-refresh').addEventListener('click', () => loadUsage().catch(() => {}));
    byId('hub-project').addEventListener('change', providerChoices);
    byId('hub-provider').addEventListener('change', modelChoices);
    byId('hub-new').addEventListener('click', newHubConversation);
    byId('hub-send').addEventListener('click', hubSend);
    byId('hub-input').addEventListener('keydown', event => {
      if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); hubSend(); }
    });
    byId('hub-delete').addEventListener('click', () => {
      apiCall('POST', '/api/chat/delete', {id: hub.id}).then(newHubConversation).catch(() => {});
    });
    byId('keep-awake').addEventListener('change', async () => {
      const checkbox = byId('keep-awake');
      try { await apiCall('POST', '/api/config', {keep_awake: checkbox.checked}); }
      catch (_) { checkbox.checked = !checkbox.checked; }
    });
    apiCall('GET', '/api/config').then(config => {
      byId('keep-awake').checked = config.keep_awake;
      if (config.orchestrator_url) {
        const url = new URL(config.orchestrator_url);
        if (url.protocol === 'http:' && ['127.0.0.1', 'localhost', '[::1]'].includes(url.hostname)) {
          byId('runs-frame').src = url.href;
          byId('runs-frame').classList.remove('hidden');
          byId('runs-notice').classList.add('hidden');
        }
      }
    }).catch(() => {});
  }

  function init() {
    initToken();
    setupTabs();
    setupChat();
    setupExamples();
    setupCommandCenter();
    loadItems();
    startPolling();
  }

  return {
    init,
  };
})();

document.addEventListener('DOMContentLoaded', () => {
  Executive.init();
});
