from flask import Flask, render_template, request, jsonify
from datetime import datetime
import re
import pandas as pd
from collections import defaultdict
import emoji
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import base64
from io import BytesIO

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def parse_whatsapp_file(file_path):
    # WhatsApp chat format patterns
    message_pattern = r'^(\d{1,2}/\d{1,2}/\d{2,4}, \d{1,2}:\d{2}\s*[ap]m)\s*-\s*([^:]+):\s*(.+)$'
    system_pattern = r'^(\d{1,2}/\d{1,2}/\d{2,4}, \d{1,2}:\d{2}\s*[ap]m)\s*-\s*(.+)$'
    
    messages = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
                
            # Try to match regular message first
            message_match = re.match(message_pattern, line)
            if message_match:
                date_time, sender, message = message_match.groups()
                try:
                    messages.append({
                        'datetime': datetime.strptime(date_time, '%m/%d/%y, %I:%M %p'),
                        'sender': sender.strip(),
                        'message': message.strip(),
                        'is_system': False
                    })
                except ValueError:
                    continue
                continue
                
            # Try to match system message
            system_match = re.match(system_pattern, line)
            if system_match:
                date_time, message = system_match.groups()
                try:
                    messages.append({
                        'datetime': datetime.strptime(date_time, '%m/%d/%y, %I:%M %p'),
                        'sender': 'System',
                        'message': message.strip(),
                        'is_system': True
                    })
                except ValueError:
                    continue
    
    return pd.DataFrame(messages)

def analyze_chat(df):
    if df.empty:
        return {}
    
    # Filter out system messages
    df = df[~df['is_system']]
    
    if df.empty:
        return {}
    
    # Basic stats
    stats = {
        'total_messages': len(df),
        'start_date': df['datetime'].min().strftime('%Y-%m-%d'),
        'end_date': df['datetime'].max().strftime('%Y-%m-%d'),
        'duration_days': (df['datetime'].max() - df['datetime'].min()).days,
        'total_participants': df['sender'].nunique()
    }
    
    # Messages per participant
    messages_per_sender = df['sender'].value_counts().to_dict()
    stats['messages_per_sender'] = messages_per_sender
    
    # Active hours
    df['hour'] = df['datetime'].dt.hour
    active_hours = df['hour'].value_counts().sort_index().to_dict()
    stats['active_hours'] = active_hours
    
    # Active days
    df['day_name'] = df['datetime'].dt.day_name()
    active_days = df['day_name'].value_counts().to_dict()
    stats['active_days'] = active_days
    
    # Emoji analysis
    emoji_counter = defaultdict(int)
    for msg in df['message']:
        for char in msg:
            if char in emoji.EMOJI_DATA:
                emoji_counter[char] += 1
    
    stats['top_emojis'] = dict(sorted(emoji_counter.items(), key=lambda item: item[1], reverse=True)[:5])
    
    # Media messages
    media_messages = df[df['message'].str.contains('<Media omitted>', na=False)]
    stats['media_messages'] = len(media_messages)
    stats['media_per_sender'] = media_messages['sender'].value_counts().to_dict()
    
    return stats

def generate_chart(data, title, xlabel, ylabel, chart_type='bar'):
    plt.figure(figsize=(10, 6))
    
    if chart_type == 'bar':
        plt.bar(data.keys(), data.values())
    elif chart_type == 'line':
        plt.plot(list(data.keys()), list(data.values()))
    
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save plot to a bytes buffer
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    
    # Encode plot to base64
    chart_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    plt.close()
    
    return chart_base64

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if not file.filename.endswith('.txt'):
        return jsonify({'error': 'Please upload a .txt file exported from WhatsApp'}), 400
    
    if file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_chat.txt')
        file.save(file_path)
        
        try:
            df = parse_whatsapp_file(file_path)
            if df.empty:
                return jsonify({'error': 'No valid messages found in the chat file'}), 400
                
            stats = analyze_chat(df)
            
            if not stats:
                return jsonify({'error': 'No regular messages found (only system messages)'}), 400
            
            # Generate charts
            charts = {}
            if 'messages_per_sender' in stats:
                charts['messages_per_sender'] = generate_chart(
                    stats['messages_per_sender'],
                    'Messages per Participant',
                    'Participant',
                    'Number of Messages'
                )
            
            if 'active_hours' in stats:
                charts['active_hours'] = generate_chart(
                    stats['active_hours'],
                    'Activity by Hour of Day',
                    'Hour',
                    'Number of Messages',
                    'line'
                )
            
            if 'active_days' in stats:
                charts['active_days'] = generate_chart(
                    stats['active_days'],
                    'Activity by Day of Week',
                    'Day',
                    'Number of Messages'
                )
            
            if 'media_per_sender' in stats and stats['media_per_sender']:
                charts['media_per_sender'] = generate_chart(
                    stats['media_per_sender'],
                    'Media Shared per Participant',
                    'Participant',
                    'Number of Media Files'
                )
            
            # Clean up
            os.remove(file_path)
            
            return jsonify({
                'stats': stats,
                'charts': charts
            })
        
        except Exception as e:
            return jsonify({'error': f'Error processing file: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)