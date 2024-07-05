from itertools import islice
from flask import Flask, request
from pymongo import MongoClient
import requests
import json
import os
# global last_update_id
# only for testing 👆

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN = os.getenv('ADMIN')
USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')

GOOD = ['👍', '🤣', '❤', '🔥', '🥰', '👏', '😁', '🎉', '🙏', '🕊', '🤩', '🐳', '💯', '😍', '❤️', '💋', '😇', '🤗', '💘', '😘', '🏆', '⚡','🤝', '👨‍💻', '🫡', '😘', '😎']
BAD = ['👎', '😱', '🤬', '😢', '🤮', '💩', '😭', '😈', '😴', '😡', '🤔', '🤯', '🎃', '👻', '🥱', '🥴', '🌭', '🤣', '🍌', '💔', '🍓', '🍾','🖕', '😨', '🙄', '🌚', '🤪', '💊']

GOOD_TO_REACT = ['👍', '🔥', '😁', '🙏', '🤩', '💯', '😇', '🤗', '🏆', '⚡','🤝', '🫡', '😎']
BLACK_LIST = [] # Add telegram user IDs for the bot to react negatively
WHITE_LIST = [] # Add telegram user IDs for the bot to react positively

app = Flask(__name__)

@app.route('/', methods=['POST'])
def handle_webhook():
    try:
        process(json.loads(request.get_data()))
        return 'Success!'
    except Exception as e:
        print(e)
        return 'Error'

def testing():
    global last_update_id
    last_update_id = -1
    while True:
        updates = requests.get(
            f'https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={last_update_id}allowed_updates=["message","message_reaction"]').json().get('result', [])
        for update in updates:
            process(update)
            last_update_id = update['update_id'] + 1


def process(update):
    if 'message' in update:
        if 'text' in update['message'] and 'chat' in update['message'] and update['message']['chat']['type'] == 'private':
            private(update['message']['from']['id'])
        elif 'text' in update['message'] and update['message']['from']['id'] in BLACK_LIST:
            print(requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/setMessageReaction',params={'chat_id': update['message']['chat']['id'], 'message_id': update['message']['message_id'], 'is_big': True,'reaction': json.dumps([{'type': 'emoji', 'emoji': BAD[random.randint(0, len(BAD) - 1)]}])}).json())
        elif 'text' in update['message'] and update['message']['from']['id'] in WHITE_LIST:
            print(requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/setMessageReaction',params={'chat_id': update['message']['chat']['id'], 'message_id': update['message']['message_id'], 'is_big': True,'reaction': json.dumps([{'type': 'emoji', 'emoji': GOOD_TO_REACT[random.randint(0, len(GOOD_TO_REACT) - 1)]}])}).json())
        elif 'text' in update['message'] and 'chat' in update['message'] and (update['message']['chat']['type'] == 'group' or update['message']['chat']['type'] == 'supergroup'):
            if update['message']['text'] == '/include@reactioner_bot':
                state = database_search({"id": update['message']['from']['id']}, 1)
                if state == None:
                    record = {
                        "id": update['message']['from']['id'],
                        "name": update['message']['from']['first_name'],
                        "username": update['message']['from'].get('username', 'None'),
                        "group": update['message']['chat']['id'],
                        "included": True,
                        "a": 0,
                        "b": 0,
                        "c": 0,
                        "d": 0,
                        "e": 0,
                        "f": 0
                    }
                    database_insert(record, 'users')
                    broadcast(update['message']['from']['id'], update['message']['from']['first_name'],update['message']['chat']['id'], '<em>You enrolled successfully.</em>')
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteMessage?chat_id={update['message']['chat']['id']}&message_id={update['message']['message_id']}")
                elif state["included"]:
                    broadcast(update['message']['from']['id'], update['message']['from']['first_name'],update['message']['chat']['id'], '<em>You have already enrolled.</em>')
                else: # If user is already in the database but not included (when user quited before and wants to join again)
                    filter = {"id": update['message']['from']['id']}
                    updated_record = {"$set": {"included": True, "group": update['message']['chat']['id']}}
                    database_update(filter, updated_record)
                    broadcast(update['message']['from']['id'], update['message']['from']['first_name'],update['message']['chat']['id'], '<em>Welcome back. You enrolled successfully.</em>')
            elif update['message']['text'] == '/exclude@reactioner_bot':
                state = database_search({"id": update['message']['from']['id']}, 1)
                if state == None:
                    broadcast(update['message']['from']['id'], update['message']['from']['first_name'],update['message']['chat']['id'], '<em>You have not started enrolling at all.</em>')
                elif state["included"] == True:
                    filter = {"id": update['message']['from']['id']}
                    updated_record = {"$set": {"included": False}}
                    database_update(filter, updated_record)
                    broadcast(update['message']['from']['id'], update['message']['from']['first_name'],update['message']['chat']['id'], '<em>Bye you stopped enrolling.</em>')
                else:
                    broadcast(update['message']['from']['id'], update['message']['from']['first_name'],update['message']['chat']['id'], '<em>You have already stopped enrolling.</em>')
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteMessage?chat_id={update['message']['chat']['id']}&message_id={update['message']['message_id']}")
            elif update['message']['text'] == '/stats@reactioner_bot':
                state = database_search({"id": update['message']['from']['id']}, 1)
                if state.get("included", False) == True:
                    broadcast(update['message']['from']['id'], update['message']['from']['first_name'],update['message']['chat']['id'],f"<strong>Your statistics:</strong>\n\n<em>Positive reactions:</em> {state['a']}\n<em>Negative reactions:</em> {state['b']}\n<em>Neutral reactions:</em> {state['d']}\n<em>Self reactions:</em> {state['e']}\n\n<strong>Total reactions you got:</strong> {state['a'] + state['b'] + state['d'] + state['e']}\n<strong>Total reactions you put:</strong> {state['c']}")
                else:
                    broadcast(update['message']['from']['id'], update['message']['from']['first_name'],update['message']['chat']['id'],f"<strong>You have not included.</strong>\n<em>Please /include@reactioner_bot</em>")
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteMessage?chat_id={update['message']['chat']['id']}&message_id={update['message']['message_id']}")
            elif update['message']['text'] == '/results@reactioner_bot':
                if is_admin(update['message']['chat']['id'], update['message']['from']['id']):
                    set1 = {}
                    set2 = {}
                    set3 = {}
                    set4 = {}
                    set5 = {}
                    set6 = {}
                    users = database_search({"group": update['message']['chat']['id']}, 2)
                    for user in users:
                        if user.get("included"):
                            set3[user["name"] + " -> "] = user['c']
                            set1[user["name"] + " -> "] = user['a']
                            set2[user["name"] + " -> "] = user['b']
                            set4[user["name"] + " -> "] = user['d']
                            set5[user["name"] + " -> "] = user['e']
                            if user['c'] != 0 and user['f'] != 0:
                                set6[user["name"] + " -> "] = float(user['a'] - user['b']) / ((user['c']) * user['f'])
                        else:
                            continue
                    set1 = dict(sorted(set1.items(), key=lambda item: item[1], reverse=True))
                    set2 = dict(sorted(set2.items(), key=lambda item: item[1], reverse=True))
                    set3 = dict(sorted(set3.items(), key=lambda item: item[1], reverse=True))
                    set4 = dict(sorted(set4.items(), key=lambda item: item[1], reverse=True))
                    set5 = dict(sorted(set5.items(), key=lambda item: item[1], reverse=True))
                    set6 = dict(sorted(set6.items(), key=lambda item: item[1], reverse=True))
                    ret = '\n<strong>TOP admired users:</strong>'
                    for key, value in islice(set1.items(), 5):
                        ret += '\n<em>' + key + '</em>' + str(value)
                    ret += '\n\n<strong>TOP hated users:</strong>'
                    for key, value in islice(set2.items(), 5):
                        ret += '\n<em>' + key + '</em>' + str(value)
                    ret += '\n\n<strong>TOP neutrally reacted users:</strong>'
                    for key, value in islice(set4.items(), 5):
                        ret += '\n<em>' + key + '</em>' + str(value)
                    ret += '\n\n<strong>TOP reaction makers:</strong>'
                    for key, value in islice(set3.items(), 5):
                        ret += '\n<em>' + key + '</em>' + str(value)
                    ret += '\n\n<strong>TOP self reacted users:</strong>'
                    for key, value in islice(set5.items(), 5):
                        ret += '\n<em>' + key + '</em>' + str(value)
                    ret += '\n\n<strong>Value coefficient:</strong>'
                    for key, value in islice(set6.items(), 5):
                        ret += '\n<em>' + key + '</em>' + str(value)
                    broadcast(update['message']['from']['id'], update['message']['from']['first_name'],update['message']['chat']['id'], ret)
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteMessage?chat_id={update['message']['chat']['id']}&message_id={update['message']['message_id']}")
        append(update['message']['message_id'], update['message']['from']['id'])
    elif 'message_reaction' in update:
        if 'chat' in update['message_reaction'] and (update['message_reaction']['chat']['type'] == 'group' or update['message_reaction']['chat']['type'] == 'supergroup') and database_search({"id": update['message_reaction']['user']['id']}, 1) != None:
            case = int(fetch(update['message_reaction']['message_id']))
            for reaction in update['message_reaction']['new_reaction']:
                if reaction.get('type') != 'emoji':
                    print(update['message_reaction']['new_reaction'])
                    return
                    #broadcast(update['message_reaction']['user']['id'],update['message_reaction']['user']['first_name'],update['message_reaction']['chat']['id'],'<strong>I will count it as a neutral reaction!</strong>')
                type = is_good(reaction.get('emoji', 'UNKNOWN'))
                try:
                    if case != update['message_reaction']['user']['id']:
                        filter = {"id": update['message_reaction']['user']['id']}
                        updated_record = {'$inc': {'c': 1}}
                        database_update(filter, updated_record)
                    else:
                        filter = {"id": update['message_reaction']['user']['id']}
                        updated_record = {'$inc': {'f': 1}}
                        database_update(filter, updated_record)
                    if case != -1:
                        if type == -1:
                            updated_record = {'$inc': {'b': 1}}
                        elif type == 1:
                            updated_record = {'$inc': {'a': 1}}
                        else:
                            updated_record = {'$inc': {'d': 1}}
                        filter = {"id": case}
                        database_update(filter, updated_record)
                except:
                    print('error 12')
            for reaction in update['message_reaction']['old_reaction']:
                if reaction.get('type') != 'emoji':
                    print(update['message_reaction']['old_reaction'])
                    return
                    #broadcast(update['message_reaction']['from']['id'],update['message_reaction']['from']['first_name'],update['message_reaction']['chat']['id'],'<strong>I will count it as a neutral reaction!</strong>')
                type = is_good(reaction.get('emoji', 'UNKNOWN'))
                try:
                    if case != update['message_reaction']['user']['id']:
                        filter = {"id": update['message_reaction']['user']['id']}
                        updated_record = {'$inc': {'c': -1}}
                        database_update(filter, updated_record)
                    else:
                        filter = {"id": update['message_reaction']['user']['id']}
                        updated_record = {'$inc': {'f': -1}}
                        database_update(filter, updated_record)
                    if case != -1:
                        if type == -1:
                            updupdated_recordate = {'$inc': {'b': -1}}
                        elif type == 1:
                            updated_record = {'$inc': {'a': -1}}
                        else:
                            updated_record = {'$inc': {'d': -1}}
                        filter = {"id": case}
                        database_update(filter, updated_record)
                except:
                    print('error 192')

def append(message_id, user_id):
    with open('messages.txt', 'r') as file:
        lines = file.readlines()
    if len(lines) >= 1000:
        lines.pop(0)
    with open('messages.txt', 'a') as file:
        file.write(f"{message_id} {user_id}" + '\n')
    filter = {"id": user_id}
    updated_record = {"$inc": {'f': 1}}
    database_update(filter, updated_record)


def fetch(message_id):
    with open('messages.txt', 'r') as file:
        for line in file.readlines():
            if str(line.split()[0]) == str(message_id):
                return line.split()[1]
    return -1


def is_good(emoji):
    for sample in GOOD:
        if emoji == sample:
            return 1
    for sample in BAD:
        if emoji == sample:
            return -1
    return 0


def broadcast(user_id, name, group, message):
    m = f"<a href='tg://user?id={user_id}'>{name}</a> ! "
    params = {
        'chat_id': group,
        'text': m + message,
        'parse_mode': 'HTML',
    }
    id_to_react = requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage', params=params).json().get(
        'result').get('message_id')
    params = {
        'chat_id': group,
        'message_id': id_to_react,
        'is_big': True,
        'reaction': json.dumps([{'type': 'emoji', 'emoji': '🔥'}])
    }
    print(requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/setMessageReaction', params=params).json())
    return

def private(chat_id):
    params = {"chat_id": chat_id,"text": "ℹ️ In order to use me, you need to add me to your group. Press the button below and select your group.\nℹ️ Чтобы использовать меня, вам нужно добавить меня в свою группу. Нажмите кнопку ниже и выберите свою группу.\nℹ️ Mendan foydalanish uchun siz meni guruhingizga qo'shishingiz kerak. Quyidagi tugmani bosing va guruhingizni tanlang.","reply_markup": json.dumps({"keyboard": [[{"text": "Add | Добавлять | Qo'shish","request_chat": {"request_id": 1, "chat_is_channel": False,"user_administrator_rights": {"can_manage_chat": True,"can_invite_users": True,"can_delete_messages": True,"can_promote_members": True,"can_restrict_members": True,"can_pin_messages": True,"can_manage_topics": True},"bot_administrator_rights": {"can_manage_chat": True,"can_invite_users": True,"can_delete_messages": True,"can_promote_members": True,"can_restrict_members": True,"can_pin_messages": True,"can_manage_topics": True}}}]],"resize_keyboard": True})}
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json=params).json()
    return

def is_admin(chat_id, user_id):
    if user_id == ADMIN or requests.get(f'https://api.telegram.org/bot{BOT_TOKEN}/getChatMember?chat_id={chat_id}&user_id={user_id}').json()['result']['status'] in ['administrator', 'creator']:
        return True
    else:
        return False

def database_search(query, option):
    connection_string = f"mongodb+srv://{USERNAME}:" + PASSWORD + "@cluster0.a0mvghx.mongodb.net/?retryWrites=true&w=majority"
    client = MongoClient(connection_string)
    db = client['reactioneer']
    collection = db['users']
    if option == 1:
        return collection.find_one(query)
    else:
        return collection.find(query)

def database_insert(record, collection_name):
    connection_string = f"mongodb+srv://{USERNAME}:" + PASSWORD + "@cluster0.a0mvghx.mongodb.net/?retryWrites=true&w=majority"
    client = MongoClient(connection_string)
    db = client['reactioneer']
    collection = db[collection_name]
    collection.insert_one(record)

def database_update(filter, update):
    connection_string = f"mongodb+srv://{USERNAME}:" + PASSWORD + "@cluster0.a0mvghx.mongodb.net/?retryWrites=true&w=majority"
    client = MongoClient(connection_string)
    db = client['reactioneer']
    collection = db['users']
    return collection.update_one(filter, update)


if __name__ == '__main__':
    app.run(debug=False)
    #testing()
