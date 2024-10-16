import logging
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.router import Router
from aiogram import F
from notion import get_ideas, get_events, add_user_action, check_user_action, remove_user_action
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Configure logging
log = logging.getLogger(__name__)
log.setLevel(os.environ.get('LOGGING_LEVEL', 'INFO').upper())

API_TOKEN = os.getenv('API_TOKEN')

router = Router()

# Команда /start
@router.message(F.text == "/start")
async def send_welcome(message: types.Message):
    await message.reply("Привет! Я бот для лайков идей мероприятий и регистрации на запланированные мероприятия.")

# Команда /view_ideas — просмотр списка идей мероприятий
@router.message(F.text == "/view_ideas")
async def list_ideas(message: types.Message):
    ideas = get_ideas()
    if not ideas:
        await message.reply("На данный момент нет доступных идей.")
        return

    for idea in ideas:
        event_title = idea['properties']['Название']['title'][0]['plain_text']
        event_id = idea['id']
        likes = idea['properties']['Лайки']['rollup']['number']

        text = f"Идея: {event_title}\nЛайков: {likes}\n"
        text += f"Лайк: /like_{event_id}"
        await message.reply(text)

# Команда /view_events — просмотр списка запланированных мероприятий
@router.message(F.text == "/view_events")
async def list_events(message: types.Message):
    events = get_events()
    if not events:
        await message.reply("На данный момент нет запланированных мероприятий.")
        return

    for event in events:
        event_title = event['properties']['Название']['title'][0]['plain_text']
        event_id = event['id']
        registrations = event['properties']['Регистрации']['rollup']['number']
        event_date = event['properties']['Дата']['date']['start']

        text = f"Мероприятие: {event_title}\nДата: {event_date}\nЗарегистрированы: {registrations}\n"
        text += f"Регистрация: /register_{event_id}"
        await message.reply(text)

# Обработка лайков
@router.message(F.text.startswith('/like_'))
async def like_event(message: types.Message):
    user_id = message.from_user.id
    event_id = message.text.split('_')[1]

    if check_user_action(user_id, event_id, "Лайк"):
        await message.reply(f"Вы уже лайкнули эту идею. Отменить лайк? /unlike_{event_id}")
    else:
        add_user_action(user_id, event_id, "Лайк")
        await message.reply("Вы лайкнули идею!")

# Обработка отмены лайков
@router.message(F.text.startswith('/unlike_'))
async def unlike_event(message: types.Message):
    user_id = message.from_user.id
    event_id = message.text.split('_')[1]

    if check_user_action(user_id, event_id, "Лайк"):
        remove_user_action(user_id, event_id, "Лайк")
        await message.reply("Лайк отменён.")
    else:
        await message.reply("Вы ещё не лайкнули эту идею.")

# Обработка регистрации
@router.message(F.text.startswith('/register_'))
async def register_event(message: types.Message):
    user_id = message.from_user.id
    event_id = message.text.split('_')[1]

    if check_user_action(user_id, event_id, "Регистрация"):
        await message.reply(f"Вы уже зарегистрированы на это мероприятие. Отменить регистрацию? /unregister_{event_id}")
    else:
        add_user_action(user_id, event_id, "Регистрация")
        await message.reply("Вы успешно зарегистрировались на мероприятие!")

# Обработка отмены регистрации
@router.message(F.text.startswith('/unregister_'))
async def unregister_event(message: types.Message):
    user_id = message.from_user.id
    event_id = message.text.split('_')[1]

    if check_user_action(user_id, event_id, "Регистрация"):
        remove_user_action(user_id, event_id, "Регистрация")
        await message.reply("Регистрация отменена.")
    else:
        await message.reply("Вы ещё не зарегистрировались на это мероприятие.")

# Functions for Yandex.Cloud
import json

async def process_event(event):
    """
    Converting an Yandex.Cloud functions event to an update and
    handling tha update.
    """
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    update = json.loads(event['body'])
    log.debug('Update: ' + str(update))
    await dp.feed_raw_update(bot, update)

async def handler(event, context):
    """Yandex.Cloud functions handler."""
    if event['httpMethod'] == 'POST':
        await process_event(event)
        return {'statusCode': 200, 'body': 'ok'}
    return {'statusCode': 405}