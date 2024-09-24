# Модуль для работы со скипнутыми людьми
import json
import os


def save_skip_user_id(skip_user_id):
    with open('skip_user_id.txt', 'w') as f:
        json.dump(skip_user_id, f)


def load_skip_user_id():
    if not os.path.exists('skip_user_id.txt'):
        with open('skip_user_id.txt', 'w') as f:
            json.dump([], f)
    with open('skip_user_id.txt', 'r') as f:
        content = f.read()
        if not content:
            return []
        skip_user_id = json.loads(content)
        return skip_user_id


