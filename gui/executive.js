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
            btn.addEventListener('click', () => handleMailOrganizeApply(item, account, category, btn));
            actionCell.appendChild(btn);
          }
          row.appendChild(actionCell);
          table.appendChild(row);
        });
        group.appendChild(table);
      });
    }
    const spamFiltered = context.spam_filtered || {};
    const byAccount = spamFiltered.by_account || {};
    const spamFilteredCounts = Object.fromEntries(
      Object.entries(spamFiltered).filter(([k]) => k !== 'by_account')
    );
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
            title: 'mail.organize_apply: ' + account + '/' + category,
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

    if (item.kind === 'mail_cleanup') {
      card.appendChild(renderMailCleanup(item));
    } else if (item.kind === 'mail_filtered') {
      card.appendChild(renderMailFiltered(item));
    }

    if (item.options && item.options.length > 0) {
      const optionsDiv = document.createElement('div');
      optionsDiv.className = 'item-options';
      item.options.forEach(option => {
        if (item.kind === 'mail_cleanup' && option.action_id === 'mail.organize_apply') {
          return;
        }
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
        if (response.preview) {
          showPreview(response.preview, option.action_id);
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
