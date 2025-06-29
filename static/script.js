document.addEventListener('DOMContentLoaded', function() {
    const analyzeBtn = document.getElementById('analyzeBtn');
    const chatFileInput = document.getElementById('chatFile');
    const loadingDiv = document.getElementById('loading');
    const resultsDiv = document.getElementById('results');
    const errorDiv = document.getElementById('error');
    
    analyzeBtn.addEventListener('click', analyzeChat);
    
    function analyzeChat() {
        const file = chatFileInput.files[0];
        
        if (!file) {
            showError('Please select a WhatsApp chat file first.');
            return;
        }
        
        if (!file.name.endsWith('.txt')) {
            showError('Please upload a .txt file exported from WhatsApp');
            return;
        }
        
        loadingDiv.classList.remove('hidden');
        resultsDiv.classList.add('hidden');
        errorDiv.classList.add('hidden');
        
        const formData = new FormData();
        formData.append('file', file);
        
        fetch('/analyze', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { 
                    throw new Error(err.error || 'Analysis failed'); 
                });
            }
            return response.json();
        })
        .then(data => {
            if (!data.stats || Object.keys(data.stats).length === 0) {
                throw new Error('No analyzable messages found in the chat');
            }
            displayResults(data);
            loadingDiv.classList.add('hidden');
            resultsDiv.classList.remove('hidden');
        })
        .catch(error => {
            console.error('Error:', error);
            loadingDiv.classList.add('hidden');
            showError(error.message);
        });
    }
    
    function displayResults(data) {
        document.getElementById('totalMessages').textContent = data.stats.total_messages;
        document.getElementById('totalParticipants').textContent = data.stats.total_participants;
        document.getElementById('duration').textContent = `${data.stats.duration_days} days (${data.stats.start_date} to ${data.stats.end_date})`;
        document.getElementById('mediaShared').textContent = data.stats.media_messages || 0;
        
        if (data.charts.messages_per_sender) {
            document.getElementById('messagesChart').src = `data:image/png;base64,${data.charts.messages_per_sender}`;
            document.getElementById('messagesChart').style.display = 'block';
        } else {
            document.getElementById('messagesChart').style.display = 'none';
        }
        
        if (data.charts.active_hours) {
            document.getElementById('hoursChart').src = `data:image/png;base64,${data.charts.active_hours}`;
            document.getElementById('hoursChart').style.display = 'block';
        } else {
            document.getElementById('hoursChart').style.display = 'none';
        }
        
        if (data.charts.active_days) {
            document.getElementById('daysChart').src = `data:image/png;base64,${data.charts.active_days}`;
            document.getElementById('daysChart').style.display = 'block';
        } else {
            document.getElementById('daysChart').style.display = 'none';
        }
        
        if (data.charts.media_per_sender) {
            document.getElementById('mediaChart').src = `data:image/png;base64,${data.charts.media_per_sender}`;
            document.getElementById('mediaChart').style.display = 'block';
        } else {
            document.getElementById('mediaChart').style.display = 'none';
        }
        
        const emojisContainer = document.getElementById('emojisContainer');
        emojisContainer.innerHTML = '';
        
        if (data.stats.top_emojis && Object.keys(data.stats.top_emojis).length > 0) {
            for (const [emojiChar, count] of Object.entries(data.stats.top_emojis)) {
                const emojiItem = document.createElement('div');
                emojiItem.className = 'emoji-item';
                emojiItem.innerHTML = `
                    <span>${emojiChar}</span>
                    <span class="emoji-count">${count}</span>
                `;
                emojisContainer.appendChild(emojiItem);
            }
        } else {
            emojisContainer.innerHTML = '<p>No emojis found in this chat.</p>';
        }
    }
    
    function showError(message) {
        errorDiv.innerHTML = `<strong>Error:</strong> ${message}<br>
        <small>Make sure you exported the chat correctly: Open WhatsApp → Group → More → Export chat (without media)</small>`;
        errorDiv.classList.remove('hidden');
    }
});