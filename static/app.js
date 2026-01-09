let conversationHistory = [];
let isListening = false;
let isSpeaking = false;  // Флаг когда AI говорит
let isProcessing = false;  // Флаг когда обрабатывается запрос
let recognition = null;
let currentAudio = null;

// Инициализация Speech Recognition
if ('webkitSpeechRecognition' in window) {
    recognition = new webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;  // ВАЖНО: только финальные результаты
    recognition.lang = 'ru-RU';
    
    let lastTranscript = '';  // Храним последний текст
    let lastSentTime = 0;     // Время последней отправки
    
    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript.trim();
        const currentTime = Date.now();
        
        // Игнорируем дубликаты и быстрые повторы
        if (transcript === lastTranscript || 
            currentTime - lastSentTime < 2000 ||
            transcript.length < 2) {
            return;
        }
        
        lastTranscript = transcript;
        lastSentTime = currentTime;
        
        document.getElementById('messageInput').value = transcript;
        addMessage('user', transcript);
        sendToAI(transcript);
    };
    
    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        if (event.error !== 'no-speech' && event.error !== 'aborted') {
            isListening = false;
            updateVoiceButton();
        }
    };
    
    recognition.onend = () => {
        if (isListening) {
            // Задержка перед новым запуском
            setTimeout(() => {
                if (isListening) {
                    recognition.start();
                }
            }, 500);
        }
    };
}

function addMessage(sender, text) {
    const messages = document.getElementById('messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const senderName = sender === 'user' ? 'Вы' : sender === 'ai' ? 'AI' : 'Система';
    messageDiv.innerHTML = `<div class="sender">${senderName}</div><div>${text}</div>`;
    
    messages.appendChild(messageDiv);
    messages.scrollTop = messages.scrollHeight;
}

function updateStatus(status, color) {
    document.getElementById('status').textContent = status;
    document.getElementById('status').style.background = color;
    document.getElementById('fullscreenStatus').textContent = status;
    document.getElementById('fullscreenStatus').style.color = color;
}

function updateFullscreenText(text) {
    document.getElementById('fullscreenText').textContent = text;
}

async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    input.value = '';
    addMessage('user', message);
    
    await sendToAI(message);
}

async function sendToAI(message) {
    // Игнорируем если уже обрабатывается запрос или AI говорит
    if (isProcessing || isSpeaking) {
        console.log('Запрос игнорирован: уже обрабатывается');
        return;
    }
    
    const provider = document.getElementById('provider').value;
    const apiKey = document.getElementById('apiKey').value;
    const personality = document.getElementById('personality').value;
    
    if (!apiKey) {
        addMessage('system', '⚠️ Введите API ключ!');
        return;
    }
    
    isProcessing = true;
    updateStatus('🤔 Думает...', 'rgba(33, 150, 243, 0.9)');
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                provider: provider,
                api_key: apiKey,
                personality: personality,
                history: conversationHistory
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const reply = data.reply;
            addMessage('ai', reply);
            
            // Добавляем в историю
            conversationHistory.push({role: 'user', content: message});
            conversationHistory.push({role: 'assistant', content: reply});
            
            // Озвучиваем
            await speakText(reply);
        } else {
            addMessage('system', `❌ Ошибка: ${data.error}`);
            updateStatus('😴 Спит', 'rgba(212, 175, 55, 0.9)');
        }
        
    } catch (error) {
        addMessage('system', `❌ Ошибка: ${error.message}`);
        updateStatus('😴 Спит', 'rgba(212, 175, 55, 0.9)');
    } finally {
        isProcessing = false;
    }
}

async function speakText(text) {
    isSpeaking = true;
    updateStatus('🗣️ Говорит', 'rgba(255, 152, 0, 0.9)');
    updateFullscreenText(text);
    
    try {
        // Останавливаем предыдущее аудио
        if (currentAudio) {
            currentAudio.pause();
            currentAudio = null;
        }
        
        const response = await fetch('/api/tts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: text
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Создаем аудио из base64
            const audio = new Audio('data:audio/mp3;base64,' + data.audio);
            currentAudio = audio;
            
            audio.onended = () => {
                isSpeaking = false;
                updateStatus(isListening ? '👂 Слушает' : '😴 Спит', 
                           isListening ? 'rgba(33, 150, 243, 0.9)' : 'rgba(212, 175, 55, 0.9)');
                setTimeout(() => updateFullscreenText(''), 2000);
                currentAudio = null;
            };
            
            await audio.play();
        }
        
    } catch (error) {
        console.error('TTS error:', error);
        isSpeaking = false;
        updateStatus(isListening ? '👂 Слушает' : '😴 Спит', 
                   isListening ? 'rgba(33, 150, 243, 0.9)' : 'rgba(212, 175, 55, 0.9)');
    }
}

function toggleVoice() {
    if (!recognition) {
        alert('Голосовой ввод не поддерживается вашим браузером');
        return;
    }
    
    const apiKey = document.getElementById('apiKey').value;
    if (!apiKey) {
        alert('Введите API ключ!');
        return;
    }
    
    if (isListening) {
        recognition.stop();
        isListening = false;
        updateStatus('😴 Спит', 'rgba(212, 175, 55, 0.9)');
        addMessage('system', 'Микрофон выключен');
    } else {
        recognition.start();
        isListening = true;
        updateStatus('👂 Слушает', 'rgba(33, 150, 243, 0.9)');
        addMessage('system', '🎤 Микрофон включен! Говорите...');
    }
    
    updateVoiceButton();
}

function updateVoiceButton() {
    const btn = document.getElementById('voiceBtn');
    btn.textContent = isListening ? '⏸️' : '🎤';
    btn.style.background = isListening ? 
        'linear-gradient(135deg, #f44336 0%, #da190b 100%)' : 
        'linear-gradient(135deg, #9C27B0 0%, #7B1FA2 100%)';
}

function testVoice() {
    const testText = "Привет! Это тест голоса. Как звучит?";
    addMessage('system', '🔊 ' + testText);
    speakText(testText);
}

function clearChat() {
    document.getElementById('messages').innerHTML = '';
    conversationHistory = [];
    addMessage('system', 'История очищена');
}

function loadAvatar() {
    const url = document.getElementById('gifUrl').value.trim();
    if (!url) {
        alert('Введите URL GIF!');
        return;
    }
    
    document.getElementById('avatarImg').src = url;
    document.getElementById('fullscreenAvatar').src = url;
    addMessage('system', '✓ Аватар загружен!');
}

function toggleFullscreen() {
    const overlay = document.getElementById('fullscreenOverlay');
    overlay.classList.toggle('active');
    
    if (overlay.classList.contains('active')) {
        const avatarUrl = document.getElementById('avatarImg').src;
        document.getElementById('fullscreenAvatar').src = avatarUrl;
    }
}

// Загрузить аватар при старте
window.addEventListener('load', () => {
    loadAvatar();
    addMessage('system', '👋 Добро пожаловать! Введите API ключ и начните общение.');
});

// ESC для выхода из полного экрана
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        const overlay = document.getElementById('fullscreenOverlay');
        if (overlay.classList.contains('active')) {
            toggleFullscreen();
        }
    }
});
