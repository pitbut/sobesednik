from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import os
import requests
from gtts import gTTS
import tempfile
import base64
import re

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app)

# Личности
PERSONALITIES = {
    "Друг": "Ты дружелюбный собеседник, говоришь простым языком.",
    "Пьяный": "Ты немного пьяный, используй 'бррат', 'слушай', пиши с ошибками.",
    "Священник": "Ты мудрый священник, обращайся 'чадо', 'сын мой'.",
    "Веселый": "Ты позитивный, шутишь, много эмодзи! 😄",
    "Алиса": "Ты умный голосовой ассистент, вежливая.",
    "Философ": "Ты глубокий философ, говоришь мудро.",
    "Учитель": "Ты опытный учитель. Объясняешь просто и понятно, приводишь примеры. Говоришь: 'Давай разберем', 'Понятно?'"
}

def clean_text_for_speech(text):
    """Очистить текст от эмодзи и знаков"""
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    text = emoji_pattern.sub('', text)
    text = re.sub(r'\*+', '', text)
    text = re.sub(r'_+', '', text)
    text = re.sub(r'#+\s*', '', text)
    text = re.sub(r'^\s*[-•]\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\.{2,}', '.', text)
    text = re.sub(r'!{2,}', '!', text)
    text = re.sub(r'\?{2,}', '?', text)
    text = re.sub(r'\([^)]*\)', '', text)
    text = re.sub(r'["""«»]', '', text)
    return text.strip()

def chat_groq(message, role, api_key, history):
    """Groq API"""
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    messages = [{"role": "system", "content": role}] + history[-10:]
    messages.append({"role": "user", "content": message})
    
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "max_tokens": 500,
        "temperature": 0.7
    }
    
    response = requests.post(url, headers=headers, json=data, timeout=30)
    result = response.json()
    
    return result["choices"][0]["message"]["content"]

def chat_google(message, role, api_key):
    """Google Gemini API"""
    from google import genai
    
    client = genai.Client(api_key=api_key)
    
    full_msg = f"Роль: {role}\n\nОтвечай кратко.\n\n{message}"
    
    response = client.models.generate_content(
        model='gemini-2.0-flash-exp',
        contents=full_msg
    )
    
    return response.text

def chat_openai(message, role, api_key, history):
    """OpenAI API"""
    url = "https://api.openai.com/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    messages = [{"role": "system", "content": role}] + history[-10:]
    messages.append({"role": "user", "content": message})
    
    data = {
        "model": "gpt-3.5-turbo",
        "messages": messages,
        "max_tokens": 500,
        "temperature": 0.7
    }
    
    response = requests.post(url, headers=headers, json=data, timeout=30)
    result = response.json()
    
    return result["choices"][0]["message"]["content"]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/info.json')
def info():
    """Endpoint для портфолио"""
    return jsonify({
        "title": "🎙️ Свободный Чат",
        "description": "AI собеседник с голосовым управлением и анимированным аватаром. Поддержка Groq, Google Gemini, OpenAI. 7 личностей включая Учителя. Голосовой ввод/вывод на русском языке.",
        "image": "https://sobesednik.robutpit.com/static/preview.jpg",
        "link": "https://sobesednik.robutpit.com",
        "date": "2026-01-10",
        "tags": ["AI", "Голос", "Python", "Flask"]
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        message = data.get('message')
        provider = data.get('provider')
        api_key = data.get('api_key')
        personality = data.get('personality', 'Друг')
        history = data.get('history', [])
        
        role = PERSONALITIES.get(personality, PERSONALITIES['Друг'])
        
        # Получаем ответ от AI
        if provider == 'groq':
            reply = chat_groq(message, role, api_key, history)
        elif provider == 'google':
            reply = chat_google(message, role, api_key)
        elif provider == 'openai':
            reply = chat_openai(message, role, api_key, history)
        else:
            return jsonify({'error': 'Unknown provider'}), 400
        
        return jsonify({
            'reply': reply,
            'success': True
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@app.route('/api/tts', methods=['POST'])
def text_to_speech():
    try:
        data = request.json
        text = data.get('text', '')
        
        # Очищаем текст
        clean = clean_text_for_speech(text)
        
        if not clean:
            return jsonify({'error': 'Empty text'}), 400
        
        # Генерируем речь
        tts = gTTS(text=clean, lang='ru', slow=False)
        
        # Сохраняем во временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
            tts.save(fp.name)
            
            # Читаем и конвертируем в base64
            with open(fp.name, 'rb') as audio_file:
                audio_data = base64.b64encode(audio_file.read()).decode('utf-8')
            
            os.unlink(fp.name)
        
        return jsonify({
            'audio': audio_data,
            'success': True
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
