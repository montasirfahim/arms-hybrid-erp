
// Wait for DOM to be ready before accessing elements
document.addEventListener('DOMContentLoaded', function() {
    const floatingChatBtn = document.getElementById('floating-chat-btn');
    const closeChatBtn = document.getElementById('close-chat-btn');
    const minimizeChatBtn = document.getElementById('minimize-chat-btn');
    const floatingChatPanel = document.getElementById('floating-chat-panel');
    const floatingChatDialog = document.getElementById('floating-chat-dialog');
    const floatingChatForm = document.getElementById('floating-chat-form');
    const floatingChatInput = document.getElementById('floating-chat-input');
    const floatingChatStatus = document.getElementById('floating-chat-status');

const CHAT_STORAGE_KEY = 'arms_ai_chat_history';
const CHAT_STATE_KEY = 'arms_ai_chat_state'; // 'open' or 'minimized'

// Load chat history from localStorage
function loadChatHistory() {
    const stored = localStorage.getItem(CHAT_STORAGE_KEY);
    return stored ? JSON.parse(stored) : [];
}

// Save chat history to localStorage
function saveChatHistory(history) {
    localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(history));
}

// Load chat state from localStorage
function loadChatState() {
    return localStorage.getItem(CHAT_STATE_KEY) || 'closed';
}

// Save chat state to localStorage
function saveChatState(state) {
    localStorage.setItem(CHAT_STATE_KEY, state);
}

// Restore chat history on page load
function restoreChatUI() {
    const history = loadChatHistory();
    const state = loadChatState();

    // Clear dialog
    floatingChatDialog.innerHTML = '';

    // Repopulate messages
    history.forEach(msg => {
        appendFloatingMessage(msg.role === 'user' ? 'user' : 'ai', msg.content);
    });

    // Restore panel visibility
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
        // Clear chat history
        chatHistory = [];
        floatingChatDialog.innerHTML = '';
        localStorage.removeItem(CHAT_STORAGE_KEY);
        saveChatState('closed');
        floatingChatStatus.textContent = 'Chat cleared. Ready to chat. (Beta)';
    });

    floatingChatForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        const message = floatingChatInput.value.trim();
        if (!message) return;

        // Disable inputs
        floatingChatInput.disabled = true;
        floatingChatForm.querySelector('button').disabled = true;

        appendFloatingMessage('user', message);
        chatHistory.push({ role: 'user', content: message });
        saveChatHistory(chatHistory); // Persist to localStorage

        floatingChatInput.value = '';
        floatingChatStatus.textContent = 'Generating response...';

        // Show loader
        appendFloatingMessage('ai', '', true);

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 60000); // 60s timeout

            const res = await fetch('http://127.0.0.1:8001/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ messages: chatHistory }),
                signal: controller.signal
            });
            clearTimeout(timeoutId);

            // Remove loader
            const loader = document.getElementById('chat-loader');
            if (loader) loader.remove();

            if (!res.ok) throw new Error(`HTTP ${res.status}`);

            const data = await res.json();
            const reply = data?.content || 'No response from AI yet.';
            console.log(reply);
            appendFloatingMessage('ai', reply);
            chatHistory.push({ role: 'assistant', content: reply });
            saveChatHistory(chatHistory); // Persist to localStorage

            floatingChatStatus.textContent = 'Response received.';
        } catch (err) {
            // Remove loader on error
            const loader = document.getElementById('chat-loader');
            if (loader) loader.remove();

            appendFloatingMessage('ai', 'AI backend is not available yet. Please start the ai_service FastAPI on port 8001.');
            floatingChatStatus.textContent = 'AI backend unreachable.';
        } finally {
            // Re-enable inputs
            floatingChatInput.disabled = false;
            floatingChatForm.querySelector('button').disabled = false;
            floatingChatInput.focus();
        }
    });

    // Initialize on page load
    window.addEventListener('load', restoreChatUI);
});