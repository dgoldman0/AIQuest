import openai
import io

users = []

data = None
websockets = {}

def inject_data(_data):
    global data
    data = _data

def set_websocket(user_id, websocket):
    websockets[user_id] = websocket

def welcome(user_id):
    pass
