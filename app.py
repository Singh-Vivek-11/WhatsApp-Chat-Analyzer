from flask import Flask, render_template, request
import os
import pandas as pd
import helper
import preprocessor
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    file = request.files['chatfile']
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(filepath)

        with open(filepath, 'r', encoding='utf-8') as f:
            raw_text = f.read()

        df = preprocessor.preprocess(raw_text)

        user_list = df['user'].unique().tolist()
        if 'group_notification' in user_list:
            user_list.remove('group_notification')
        user_list.sort()

        selected_user = request.form.get('selected_user')
        if selected_user not in user_list:
            selected_user = 'Overall'

        stats = helper.fetch_stats(selected_user, df)
        most_common_words = helper.most_common_words(selected_user, df).values.tolist()
        emoji_data = helper.emoji_helper(selected_user, df).head().values.tolist()

        return render_template('result.html',
                               stats=stats,
                               selected_user=selected_user,
                               words=most_common_words,
                               emojis=emoji_data)

    return "No file uploaded."

if __name__ == '__main__':
    app.run(debug=True)
