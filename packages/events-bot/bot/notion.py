import os
from notion_client import Client
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

NOTION_TOKEN = os.getenv('NOTION_TOKEN')
DATABASE_ID = os.getenv('DATABASE_ID')
ACTIONS_DATABASE_ID = os.getenv('ACTIONS_DATABASE_ID')

# Инициализация клиента Notion
notion = Client(auth=NOTION_TOKEN)

# Получение списка идей мероприятий (только статус "Идея")
def get_ideas():
    try:
        response = notion.databases.query(
            database_id=DATABASE_ID,
            filter={
                "property": "Статус",
                "select": {
                    "equals": "Идея"
                }
            }
        )
        return response['results']
    except Exception as e:
        print(f"Ошибка при получении идей: {e}")
        return None

# Получение списка запланированных мероприятий (только статус "Запланировано")
def get_events():
    try:
        response = notion.databases.query(
            database_id=DATABASE_ID,
            filter={
                "property": "Статус",
                "select": {
                    "equals": "Запланировано"
                }
            }
        )
        return response['results']
    except Exception as e:
        print(f"Ошибка при получении запланированных мероприятий: {e}")
        return None

# Добавление действия пользователя (лайк или регистрация)
def add_user_action(user_id, event_id, action_type):
    try:
        new_action = {
            "parent": {"database_id": ACTIONS_DATABASE_ID},
            "properties": {
                "Пользователь": {
                    "rich_text": [
                        {"text": {"content": str(user_id)}}
                    ]
                },
                "Мероприятие": {
                    "relation": [{"id": event_id}]
                },
                "Тип действия": {
                    "multi_select": [{"name": action_type}]
                }
            }
        }
        notion.pages.create(**new_action)
    except Exception as e:
        print(f"Ошибка при добавлении действия: {e}")

# Проверка, есть ли действие пользователя (лайк или регистрация)
def check_user_action(user_id, event_id, action_type):
    try:
        response = notion.databases.query(
            database_id=ACTIONS_DATABASE_ID,
            filter={
                "and": [
                    {"property": "Пользователь", "rich_text": {"equals": str(user_id)}},
                    {"property": "Мероприятие", "relation": {"contains": event_id}},
                    {"property": "Тип действия", "multi_select": {"contains": action_type}}
                ]
            }
        )
        return len(response['results']) > 0
    except Exception as e:
        print(f"Ошибка при проверке действия: {e}")
        return False

# Удаление действия (лайка или регистрации)
def remove_user_action(user_id, event_id, action_type):
    try:
        response = notion.databases.query(
            database_id=ACTIONS_DATABASE_ID,
            filter={
                "and": [
                    {"property": "Пользователь", "rich_text": {"equals": str(user_id)}},
                    {"property": "Мероприятие", "relation": {"contains": event_id}},
                    {"property": "Тип действия", "multi_select": {"contains": action_type}}
                ]
            }
        )
        if response['results']:
            notion.pages.update(page_id=response['results'][0]['id'], archived=True)
    except Exception as e:
        print(f"Ошибка при удалении действия: {e}")
