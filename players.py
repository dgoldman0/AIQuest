from generation import generate_prompt
from generation import call_openai

users = []

data = None
websockets = {}

def inject_data(_data):
    global data
    data = _data

def set_websocket(user_id, websocket):
    websockets[user_id] = websocket

# Welcome new player.
async def welcome(user_id, character_id, clan_id, realm_id, x, y):
    websocket = websockets[user_id]
    realm = data.get_realm(realm_id)
    prompt = generate_prompt("interactions/introduce_realm", (realm[0], realm[1], realm[2], ))
    introduction = call_openai(prompt, 512)
    await websocket.send("NARRATION:" + introduction)
    # name, clan_id, background, affinities, realm_id, x, y
    character = data.get_character(character_id, True)
    # name, short_description. long_description, affinities
    clan = data.get_clan(cland_id, True)
    prompt = generate_prompt("interactions/introduce_player_character", (character[0], character[2], clan[0], clan[2]))
    introduction = call_openai(prompt, 512)
    await websocket.send("NARRATION:" + introduction)
    return
