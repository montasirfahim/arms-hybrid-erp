// Navigation and Authentication logic
function checkLoginStatus() {
    const accessToken = localStorage.getItem('access_token');
    const dashboardBtn = document.getElementById('dashboardBtn');
    const logoutBtn = document.getElementById('logoutBtn');
    const loginLink = document.getElementById('loginLink');

    if (accessToken) {
        if (dashboardBtn) dashboardBtn.style.display = 'block';
        if (logoutBtn) logoutBtn.style.display = 'block';
        if (loginLink) loginLink.style.display = 'none';
    } else {
        if (dashboardBtn) dashboardBtn.style.display = 'none';
        if (logoutBtn) logoutBtn.style.display = 'none';
        if (loginLink) loginLink.style.display = 'block';
    }
}

function initLogout(logoutUrl, loginUrl) {
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async () => {
            const refreshToken = localStorage.getItem('refresh_token');

            try {
                await fetch(logoutUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        refresh: refreshToken,
                    }),
                });
            } catch (error) {
                console.error('Logout error:', error);
            }

            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('user_data');

            window.location.href = loginUrl;
        });
    }
}

// AI Chat logic
function initAIChat(chatApiUrl) {
    const floatingChatBtn = document.getElementById('floating-chat-btn');
    const closeChatBtn = document.getElementById('close-chat-btn');
    const minimizeChatBtn = document.getElementById('minimize-chat-btn');
    const floatingChatPanel = document.getElementById('floating-chat-panel');
    const floatingChatDialog = document.getElementById('floating-chat-dialog');
    const floatingChatForm = document.getElementById('floating-chat-form');
    const floatingChatInput = document.getElementById('floating-chat-input');
    const floatingChatStatus = document.getElementById('floating-chat-status');

    if (!floatingChatBtn) return;

    const CHAT_STORAGE_KEY = 'arms_ai_chat_history';
    const CHAT_STATE_KEY = 'arms_ai_chat_state';

    function loadChatHistory() {
        const stored = localStorage.getItem(CHAT_STORAGE_KEY);
        return stored ? JSON.parse(stored) : [];
    }

    function saveChatHistory(history) {
        localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(history));
    }

    function loadChatState() {
        return localStorage.getItem(CHAT_STATE_KEY) || 'closed';
    }

    function saveChatState(state) {
        localStorage.setItem(CHAT_STATE_KEY, state);
    }

    function appendFloatingMessage(sender, text, isLoader = false) {
        const container = document.createElement('div');
        container.className = sender === 'user' ? 'flex justify-end' : 'flex justify-start';
        
        const item = document.createElement('div');
        item.className = sender === 'user' 
            ? 'max-w-[85%] bg-indigo-600 text-white rounded-2xl rounded-tr-none px-4 py-2 shadow-lg' 
            : 'max-w-[85%] bg-slate-700 text-slate-100 border border-slate-600 rounded-2xl rounded-tl-none px-4 py-2 shadow-lg';
        
        if (isLoader) {
            item.id = 'chat-loader';
            item.className = 'max-w-[80%] bg-slate-700 text-slate-300 border border-slate-600 rounded-2xl rounded-tl-none px-4 py-2 shadow-lg';
            item.innerHTML = `<div class="flex gap-1.5 items-center py-1"><span class="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce"></span><span class="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce [animation-delay:0.2s]"></span><span class="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce [animation-delay:0.4s]"></span></div>`;
        } else {
            item.innerHTML = `<div class="text-[10px] font-bold opacity-60 mb-1 tracking-wider uppercase">${sender === 'user' ? 'You' : 'AI Assistant'}</div><div class="leading-relaxed">${text}</div>`;
        }
        
        container.appendChild(item);
        floatingChatDialog.appendChild(container);
        floatingChatDialog.scrollTop = floatingChatDialog.scrollHeight;
    }

    function restoreChatUI() {
        const history = loadChatHistory();
        const state = loadChatState();

        floatingChatDialog.innerHTML = '';
        history.forEach(msg => {
            appendFloatingMessage(msg.role === 'user' ? 'user' : 'ai', msg.content);
        });

        if (state === 'open') {
            floatingChatPanel.classList.remove('hidden');
            floatingChatInput.focus();
        } else if (state === 'minimized') {
            floatingChatPanel.classList.add('hidden');
        }
    }

    let chatHistory = loadChatHistory();

    floatingChatBtn.addEventListener('click', () => {
        const isHidden = floatingChatPanel.classList.toggle('hidden');
        saveChatState(isHidden ? 'minimized' : 'open');
        if (!isHidden) {
            floatingChatInput.focus();
        }
    });

    minimizeChatBtn.addEventListener('click', () => {
        floatingChatPanel.classList.add('hidden');
        saveChatState('minimized');
    });

    closeChatBtn.addEventListener('click', () => {
        floatingChatPanel.classList.add('hidden');
        chatHistory = [];
        floatingChatDialog.innerHTML = '';
        localStorage.removeItem(CHAT_STORAGE_KEY);
        saveChatState('closed');
        floatingChatStatus.textContent = 'Chat cleared. Ready to chat. (Beta)';
    });

    floatingChatForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const message = floatingChatInput.value.trim();
        if (!message) return;

        floatingChatInput.disabled = true;
        floatingChatForm.querySelector('button').disabled = true;

        appendFloatingMessage('user', message);
        chatHistory.push({ role: 'user', content: message });
        saveChatHistory(chatHistory);
        
        floatingChatInput.value = '';
        floatingChatStatus.textContent = 'Generating response...';
        
        appendFloatingMessage('ai', '', true);

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 60000);

            const token = localStorage.getItem('access_token');
            const res = await fetch(chatApiUrl, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ messages: chatHistory }),
                signal: controller.signal
            });
            clearTimeout(timeoutId);

            const loader = document.getElementById('chat-loader');
            if (loader) loader.remove();

            if (!res.ok) throw new Error(`HTTP ${res.status}`);

            const data = await res.json();
            const reply = data?.content || 'No response from AI yet.';
            appendFloatingMessage('ai', reply);
            chatHistory.push({ role: 'assistant', content: reply });
            saveChatHistory(chatHistory);
            
            floatingChatStatus.textContent = 'Response received.';
        } catch (err) {
            console.error('AI Chat Error:', err);
            const loader = document.getElementById('chat-loader');
            if (loader) loader.remove();
            appendFloatingMessage('ai', 'The ARMS AI Assistant is currently unavailable. Please ensure the GROQ_API_KEY is correctly configured in the server environment.');
            floatingChatStatus.textContent = 'AI Service Error.';
        } finally {
            floatingChatInput.disabled = false;
            floatingChatForm.querySelector('button').disabled = false;
            floatingChatInput.focus();
        }
    });

    restoreChatUI();
}

// Initialize everything on window load
window.addEventListener('load', () => {
    checkLoginStatus();
    if (typeof BASE_URLS !== 'undefined') {
        initLogout(BASE_URLS.logout, BASE_URLS.login);
        initAIChat(BASE_URLS.chatApi);
    }
});
