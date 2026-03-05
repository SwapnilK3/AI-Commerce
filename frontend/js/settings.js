/**
 * Settings page — displays current API key config status
 */
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('settings-form');
    form?.addEventListener('submit', handleSaveSettings);
    checkApiStatus();
});

async function checkApiStatus() {
    // Check which API keys are configured by testing the simulate endpoint
    const indicators = {
        'twilio-status': false,
        'elevenlabs-status': false,
        'whatsapp-status': false,
    };

    // We just show a note that keys need to be set in .env
    document.querySelectorAll('.api-status').forEach(el => {
        el.innerHTML = `<span class="badge badge-warning"><i class="fas fa-key" style="font-size:0.6rem"></i> Set in .env file</span>`;
    });
}

function handleSaveSettings(e) {
    e.preventDefault();
    showToast('Settings are managed via the .env file in the project root. Please edit that file directly and restart the server.', 'info');
}
