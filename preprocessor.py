import re
import pandas as pd

def preprocess(data):
    pattern = r'\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}\s[ap]m\s-\s'
    messages = re.split(pattern, data)[1:]
    dates = re.findall(pattern, data)
    cleaned_dates = [d.strip() for d in dates]

    users = []
    messages_clean = []

    for message in messages:
        parts = message.split(': ', 1)
        if len(parts) == 2:
            users.append(parts[0])
            messages_clean.append(parts[1])
        else:
            users.append('group_notification')
            messages_clean.append(parts[0])

    df = pd.DataFrame({'user': users, 'message': messages_clean, 'date': cleaned_dates})
    df['date'] = pd.to_datetime(df['date'], errors='coerce')

    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month_name()
    df['month_num'] = df['date'].dt.month
    df['day'] = df['date'].dt.day
    df['day_name'] = df['date'].dt.day_name()
    df['hour'] = df['date'].dt.hour
    df['minute'] = df['date'].dt.minute
    df['only_date'] = df['date'].dt.date
    df['period'] = df['hour'].apply(lambda x: f"{x}-{x+1}" if x < 23 else "23-00")

    return df
