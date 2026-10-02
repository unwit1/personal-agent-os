const Executive = (() => {
  let conversationId = null;
  let token = null;
  let pendingPolling = null;

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

  function apiCall(method, endpoint, data = null) {
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
        showError(error.message);
        throw error;
      });
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
    const input = document.getElementById('chat-input');
    const text = input.value.trim();
    if (!text) return;

    input.value = '';
    addChatMessage('you', text);

    const convId = getOrCreateConversationId();
    apiCall('POST', '/api/chat', {
      conversation_id: convId,
      message: text,
    })
      .then(response => {
        if (response.message) {
          addChatMessage('agent', response.message);
        }
      })
      .catch(() => {
        /* error already shown */
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
    apiCall('POST', '/api/pending', {
      conversation_id: convId,
    })
      .then(response => {
        if (response.previews && Array.isArray(response.previews)) {
          response.previews.forEach(preview => {
            const existing = document.getElementById('preview-' + preview.id);
            if (!existing) {
              showPreview(preview, 'pending');
            }
          });
        }
      })
      .catch(() => {
        /* error already shown */
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
