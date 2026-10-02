const Executive = (() => {
  let conversationId = null;
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
          throw new Error(`API error: ${response.status} ${response.statusText}`);
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

  function showError(message) {
    const container = document.getElementById('provider-errors');
    if (container) {
      container.textContent = normalizeErrors(message);
    }
  }

  function clearError() {
    const container = document.getElementById('provider-errors');
    if (container) {
      container.textContent = '';
    }
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
      return Object.assign({}, raw, { id: raw.id || token });
    }
    return { id: token, title: 'Pending action', content: String(raw) };
  }

  function handleActResult(response, actionId) {
    if (!response) return;
    if (response.message) addChatMessage('agent', response.message);
    const compose = findCompose(response);
    if (compose) showCompose(compose);
    const preview = findPreview(response);
    if (preview) showPreview(preview, actionId);
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
        handleActResult(response, actionId);
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
      const name = applicant.name || applicant.display_name || applicant.id || 'Applicant';
      row.appendChild(el('span', 'applicant-name', name));
      const bits = [];
      if (applicant.rank !== undefined && applicant.rank !== null) bits.push('#' + applicant.rank);
      if (applicant.score !== undefined && applicant.score !== null) bits.push('score ' + applicant.score);
      if (applicant.suggestion) bits.push(applicant.suggestion);
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
    const params = { applicant_id: applicant.id };
    runAction(item, 'applicant.review', params)
      .then(response => {
        const result = (response && response.result) || response || {};
        const review = result.review || result;
        const fields = review.fields || result.fields || applicant.fields || {};
        const decisions = review.decisions || result.decisions || applicant.decisions || [];
        panel.innerHTML = '';
        panel.classList.remove('hidden');
        panel.appendChild(el('div', 'review-title', applicant.name || applicant.id || 'Applicant'));
        const list = el('dl', 'review-fields');
        Object.keys(fields).forEach(key => {
          const value = fields[key];
          list.appendChild(el('dt', null, key));
          list.appendChild(el('dd', null, value === null || value === undefined ? '' :
            (typeof value === 'object' ? JSON.stringify(value) : String(value))));
        });
        panel.appendChild(list);
        const buttons = el('div', 'item-options');
        decisions.forEach(decision => {
          const actionId = decision.action_id || decision.id;
          if (!actionId) return;
          const btn = el('button', decision.consequential ? 'option-consequential' : '', decision.label || actionId);
          btn.type = 'button';
          btn.addEventListener('click', () => {
            btn.disabled = true;
            runAction(item, actionId, Object.assign({ applicant_id: applicant.id }, decision.params || {}))
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

    let fromSelect = null;
    const accounts = compose.accounts || compose.from_accounts || [];
    if (accounts.length > 0) {
      fromSelect = document.createElement('select');
      fromSelect.id = 'compose-from';
      accounts.forEach(account => {
        const value = typeof account === 'string' ? account : (account.id || account.address);
        const label = typeof account === 'string' ? account : (account.label || account.address || value);
        const option = el('option', null, label);
        option.value = value;
        if (value === compose.from || value === compose.from_account) option.selected = true;
        fromSelect.appendChild(option);
      });
      field('From', fromSelect);
    }

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
        to: toInput.value.split(/[;,]/).map(s => s.trim()).filter(Boolean),
        subject: subjectInput.value,
        body: bodyInput.value,
      });
      delete payload.accounts;
      delete payload.from_accounts;
      if (fromSelect) payload.from = fromSelect.value;
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
    cancelBtn.addEventListener('click', closeCompose);
    actions.appendChild(cancelBtn);
    panel.appendChild(actions);

    document.body.appendChild(panel);
    toInput.focus();
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

    const meta = document.createElement('div');
    meta.className = 'item-meta';
    if (item.source) {
      const source = document.createElement('span');
      source.textContent = 'Source: ' + item.source;
      meta.appendChild(source);
    }
    if (item.age || item.due) {
      const timing = document.createElement('span');
      timing.textContent = item.age || item.due || '—';
      meta.appendChild(timing);
    }
    if (meta.children.length > 0) {
      card.appendChild(meta);
    }

    if (item.kind === 'county_openings') {
      card.appendChild(renderCountyOpenings(item, card));
    }

    if (item.options && item.options.length > 0) {
      const optionsDiv = document.createElement('div');
      optionsDiv.className = 'item-options';
      item.options.forEach(option => {
        const btn = document.createElement('button');
        btn.className = option.consequential ? 'option-consequential' : '';
        btn.textContent = option.label;
        btn.addEventListener('click', () => handleOptionClick(item, option));
        optionsDiv.appendChild(btn);
      });
      card.appendChild(optionsDiv);
    }

    return card;
  }

  function renderItems(items) {
    const workItems = items.filter(i => i.tab === 'work');
    const personalItems = items.filter(i => i.tab === 'personal');

    const workList = document.getElementById('work-items');
    const personalList = document.getElementById('personal-items');

    workList.innerHTML = '';
    personalList.innerHTML = '';

    if (workItems.length === 0) {
      workList.innerHTML = '<div class="muted" style="padding: 16px;">No work items</div>';
    } else {
      workItems.forEach(item => {
        workList.appendChild(renderItem(item));
      });
    }

    if (personalItems.length === 0) {
      personalList.innerHTML = '<div class="muted" style="padding: 16px;">No personal items</div>';
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

    showBusy(true);
    clearError();
    apiCall('POST', '/api/option', payload)
      .then(response => {
        showBusy(false);
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
        showBusy(false);
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
    showBusy(true);

    input.value = '';
    addChatMessage('you', text);

    const convId = getOrCreateConversationId();
    apiCall('POST', '/api/chat', {
      conversation_id: convId,
      message: text,
    }, false)
      .then(response => {
        if (response.message) {
          addChatMessage('agent', response.message);
        }
        const compose = findCompose(response);
        if (compose) showCompose(compose);
        const preview = findPreview(response);
        if (preview) showPreview(preview, 'chat');
        if (response.refresh || compose || preview) loadItems();
      })
      .catch(() => {
        /* error already shown */
      })
      .finally(() => {
        chatInFlight = false;
        input.disabled = false;
        send.disabled = false;
        showBusy(false);
        input.focus();
      });
  }

  function showPreview(preview, actionId) {
    const container = document.getElementById('pending-previews');
    const card = document.createElement('div');
    card.className = 'preview-card';
    card.id = 'preview-' + (preview.id || actionId + '_' + Date.now());

    const title = document.createElement('div');
    title.className = 'preview-title';
    title.textContent = 'Preview: ' + (preview.title || 'Pending action');
    card.appendChild(title);

    if (preview.content) {
      const content = document.createElement('div');
      content.className = 'preview-content';
      content.textContent = preview.content;
      card.appendChild(content);
    }

    const actions = document.createElement('div');
    actions.className = 'preview-actions';

    const confirmBtn = document.createElement('button');
    confirmBtn.className = 'primary';
    confirmBtn.textContent = 'Confirm';
    confirmBtn.addEventListener('click', () => {
      handleConfirm(preview, card);
    });
    actions.appendChild(confirmBtn);

    const cancelBtn = document.createElement('button');
    cancelBtn.className = 'ghost';
    cancelBtn.textContent = 'Cancel';
    cancelBtn.addEventListener('click', () => {
      handleDismiss(preview, card);
    });
    actions.appendChild(cancelBtn);

    card.appendChild(actions);
    container.appendChild(card);
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
        if (response.message) {
          addChatMessage('agent', response.message);
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

  function loadItems() {
    showBusy(true);
    apiCall('GET', '/api/items')
      .then(response => {
        showBusy(false);
        if (response.items) {
          renderItems(response.items);
        }
        if (response.errors) {
          showError(response.errors);
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

    tabWork.addEventListener('click', () => {
      tabWork.classList.add('on');
      tabPersonal.classList.remove('on');
      tabWork.setAttribute('aria-selected', 'true');
      tabPersonal.setAttribute('aria-selected', 'false');
      workTab.classList.add('on');
      personalTab.classList.remove('on');
    });

    tabPersonal.addEventListener('click', () => {
      tabPersonal.classList.add('on');
      tabWork.classList.remove('on');
      tabPersonal.setAttribute('aria-selected', 'true');
      tabWork.setAttribute('aria-selected', 'false');
      personalTab.classList.add('on');
      workTab.classList.remove('on');
    });
  }

  function setupChat() {
    const chatInput = document.getElementById('chat-input');
    const chatSend = document.getElementById('chat-send');

    chatSend.addEventListener('click', handleChatSend);
    chatInput.addEventListener('keypress', event => {
      if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        handleChatSend();
      }
    });
  }

  function init() {
    initToken();
    setupTabs();
    setupChat();
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
