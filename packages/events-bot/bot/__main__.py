import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.router import Router
from aiogram import F
from notion import get_ideas, get_events, add_user_action, check_user_action, remove_user_action
import os

# Команда /start
async def send_welcome(message: types.Message):
    await message.reply("Привет! Я бот для лайков идей мероприятий и регистрации на запланированные мероприятия.")

# Команда /view_ideas — просмотр списка идей мероприятий
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
async def like_event(message: types.Message):
    user_id = message.from_user.id
    event_id = message.text.split('_')[1]

    if check_user_action(user_id, event_id, "Лайк"):
        await message.reply(f"Вы уже лайкнули эту идею. Отменить лайк? /unlike_{event_id}")
    else:
        add_user_action(user_id, event_id, "Лайк")
        await message.reply("Вы лайкнули идею!")

# Обработка отмены лайков
async def unlike_event(message: types.Message):
    user_id = message.from_user.id
    event_id = message.text.split('_')[1]

    if check_user_action(user_id, event_id, "Лайк"):
        remove_user_action(user_id, event_id, "Лайк")
        await message.reply("Лайк отменён.")
    else:
        await message.reply("Вы ещё не лайкнули эту идею.")

# Обработка регистрации
async def register_event(message: types.Message):
    user_id = message.from_user.id
    event_id = message.text.split('_')[1]

    if check_user_action(user_id, event_id, "Регистрация"):
        await message.reply(f"Вы уже зарегистрированы на это мероприятие. Отменить регистрацию? /unregister_{event_id}")
    else:
        add_user_action(user_id, event_id, "Регистрация")
        await message.reply("Вы успешно зарегистрировались на мероприятие!")

# Обработка отмены регистрации
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

async def process_event(bot, event):
    """
    Converting an DigitalOcean `web: raw` functions event to an update and
    handling the update.
    """
    router = Router()
    router.message.register(send_welcome, F.text == "/start")
    router.message.register(list_ideas, F.text == "/view_ideas")
    router.message.register(list_events, F.text == "/view_events")
    router.message.register(like_event, F.text.startswith('/like_'))
    router.message.register(unlike_event, F.text.startswith('/unlike_'))
    router.message.register(register_event, F.text.startswith('/register_'))
    router.message.register(unregister_event, F.text.startswith('/unregister_'))

    
    dp = Dispatcher()
    dp.include_router(router)
    update = json.loads(event['http']['body'])

    await dp.feed_raw_update(bot, update)

def main(event):
    """DigitalOcean functions handler."""
    API_TOKEN = os.getenv('API_TOKEN')
    LOG_CHAT_ID = os.getenv('LOG_CHAT_ID')
    
    print("i'm alive, event: " + str(event), flush=True)
    bot = Bot(token=API_TOKEN)
    asyncio.run(bot.send_message(chat_id=LOG_CHAT_ID, text="Event: "+str(event)))

    # Configure logging
    log = logging.getLogger(__name__)
    log.setLevel(os.environ.get('LOGGING_LEVEL', 'INFO').upper())

    if event['http']['method'] == 'POST':
        try:
            asyncio.run(process_event(bot, event))
        except Exception as e:
            log.error("Exception: " + str(e))
        return {'statusCode': 200, 'body': 'ok'}
    
    return {'statusCode': 405}