/**
 * Omnichannel Inbox Logic
 */

let activeContactId = null;
let activeChannel = null;

document.addEventListener('DOMContentLoaded', () => {
    loadContacts();

    // Set up reply form listener
    document.getElementById('reply-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const textInput = document.getElementById('reply-text');
        const text = textInput.value.trim();
        if (!text || !activeContactId || !activeChannel) return;

        const btn = document.getElementById('send-btn');
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

        try {
            const response = await fetchAPI('/api/inbox/reply', {
                method: 'POST',
                body: JSON.stringify({
                    contact_id: activeContactId,
                    channel: activeChannel,
                    text: text
                })
            });

            if (response && !response.error) {
                textInput.value = '';
                // Optimistically append the message to the view
                appendMessage(response);
                scrollToBottom();

                // Refresh contacts list quietly in background to update snippets
                loadContacts(true);
            } else {
                alert('Failed to send message: ' + (response?.detail || 'Unknown error'));
            }
        } catch (err) {
            console.error(err);
            alert('Error sending reply.');
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-paper-plane"></i>';
        }
    });
});

async function loadContacts(quiet = false) {
    const container = document.getElementById('contacts-container');
    if (!quiet) {
        container.innerHTML = `
            <div class="p-8 text-center text-slate-500">
                <div class="spinner inline-block mb-3"></div>
                <p>Loading messages...</p>
            </div>
        `;
    }

    try {
        const contacts = await fetchAPI('/api/inbox/contacts');

        if (!contacts || contacts.error) {
            if (!quiet) container.innerHTML = `<div class="p-6 text-center text-red-400">Failed to load contacts.</div>`;
            return;
        }

        if (contacts.length === 0) {
            container.innerHTML = `
                <div class="p-8 text-center text-slate-500 flex flex-col items-center">
                    <i class="fas fa-inbox text-4xl mb-3 opacity-50"></i>
                    <p>No conversations yet.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = '';
        contacts.forEach(c => {
            const iso = c.last_timestamp;
            const d = new Date(iso && !iso.endsWith('Z') && !iso.includes('+') ? iso + 'Z' : iso);
            const time = d.toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit' });

            let icon = '';
            let color = '';
            if (c.channel === 'whatsapp') { icon = 'fab fa-whatsapp'; color = 'text-green-400'; }
            else if (c.channel === 'instagram') { icon = 'fab fa-instagram'; color = 'text-pink-400'; }
            else if (c.channel === 'facebook') { icon = 'fab fa-facebook-messenger'; color = 'text-blue-400'; }
            else { icon = 'fas fa-comment'; color = 'text-slate-400'; }

            const isActive = (c.contact_id === activeContactId && c.channel === activeChannel) ? 'active' : '';

            const div = document.createElement('div');
            div.className = `contact-item flex items-center gap-3 ${isActive}`;
            div.onclick = () => loadChatHistory(c.contact_id, c.channel);

            let humanBadge = c.requires_human ? `<span class="human-req-badge">Needs Human</span>` : '';

            // Format phone numbers nicely if it looks like one
            let displayId = c.contact_id;
            if (displayId.length > 8 && !isNaN(displayId)) {
                displayId = '+' + displayId;
            }

            div.innerHTML = `
                <div class="w-10 h-10 rounded-full bg-slate-800 flex items-center justify-center text-lg ${color}">
                    <i class="${icon}"></i>
                </div>
                <div class="flex-grow min-w-0">
                    <div class="flex justify-between items-baseline mb-1">
                        <h4 class="font-semibold text-sm text-slate-200 truncate">${displayId}</h4>
                        <span class="text-xs text-slate-500 flex-shrink-0 ml-2">${time}</span>
                    </div>
                    <div class="flex items-center gap-2">
                        <p class="text-xs text-slate-400 truncate flex-grow">${c.last_message}</p>
                        ${humanBadge}
                    </div>
                </div>
            `;
            container.appendChild(div);
        });

    } catch (e) {
        console.error(e);
        if (!quiet) container.innerHTML = `<div class="p-6 text-center text-red-400">Network error.</div>`;
    }
}

async function loadChatHistory(contactId, channel) {
    activeContactId = contactId;
    activeChannel = channel;

    // UI Updates
    document.getElementById('chat-empty-state').style.display = 'none';
    document.getElementById('chat-header').classList.remove('invisible');
    document.getElementById('chat-input-area').classList.remove('invisible');

    // Format Display ID
    let displayId = contactId;
    if (displayId.length > 8 && !isNaN(displayId)) displayId = '+' + displayId;
    document.getElementById('chat-contact-id').textContent = displayId;

    // Badges
    const badge = document.getElementById('chat-channel-badge');
    if (channel === 'whatsapp') badge.innerHTML = `<i class="fab fa-whatsapp text-green-400"></i> WhatsApp`;
    else if (channel === 'instagram') badge.innerHTML = `<i class="fab fa-instagram text-pink-400"></i> Instagram`;
    else if (channel === 'facebook') badge.innerHTML = `<i class="fab fa-facebook-messenger text-blue-400"></i> Messenger`;
    else badge.innerHTML = `<i class="fas fa-comment text-slate-400"></i> Local Chat`;

    // Highlight active contact in list
    document.querySelectorAll('.contact-item').forEach(el => el.classList.remove('active'));
    // (Note: finding the exact element requires more robust matching, but loading contacts again handles it)
    loadContacts(true);

    const msgContainer = document.getElementById('chat-messages');
    msgContainer.innerHTML = `
        <div class="w-full flex justify-center py-10 opacity-50">
            <div class="spinner"></div>
        </div>
    `;

    try {
        const messages = await fetchAPI(`/api/inbox/${contactId}/messages?channel=${channel}`);
        msgContainer.innerHTML = '';

        if (messages && messages.length > 0) {
            messages.forEach(msg => appendMessage(msg));
            scrollToBottom();
        } else {
            msgContainer.innerHTML = `
                <div class="w-full h-full flex flex-col items-center justify-center text-slate-500 opacity-50">
                    <p>No messages found in history.</p>
                </div>
            `;
        }
    } catch (e) {
        console.error(e);
        msgContainer.innerHTML = `<div class="text-center text-red-500 p-4">Error loading messages.</div>`;
    }
}

function appendMessage(msg) {
    const msgContainer = document.getElementById('chat-messages');

    // Remove empty state if present
    if (msgContainer.querySelector('p')?.textContent.includes('No messages')) {
        msgContainer.innerHTML = '';
    }

    const div = document.createElement('div');
    const iso = msg.timestamp;
    const d = new Date(iso && !iso.endsWith('Z') && !iso.includes('+') ? iso + 'Z' : iso);
    const time = iso ? d.toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : 'Just now';

    if (msg.is_inbound) {
        div.className = 'msg-bubble msg-inbound';
        div.innerHTML = `
            <div>${msg.text}</div>
            <div class="text-[0.65rem] text-slate-400 mt-1 text-right">${time}</div>
        `;
    } else {
        div.className = `msg-bubble msg-outbound ${msg.is_ai_reply ? 'msg-ai' : ''}`;

        let aiBadge = msg.is_ai_reply ? `<div class="ai-badge"><i class="fas fa-robot"></i> AI</div>` : `<div class="ai-badge bg-indigo-500"><i class="fas fa-user"></i> You</div>`;

        div.innerHTML = `
            <div>${msg.text}</div>
            <div class="text-[0.65rem] text-slate-400 mt-1 text-right">${time}</div>
            ${aiBadge}
        `;
    }

    msgContainer.appendChild(div);
}

function scrollToBottom() {
    const msgContainer = document.getElementById('chat-messages');
    setTimeout(() => {
        msgContainer.scrollTop = msgContainer.scrollHeight;
    }, 50);
}
