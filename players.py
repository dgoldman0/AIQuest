from generation import generate_prompt
from generation import call_openai
import maps

users = []

data = None
websockets = {}
user_states = {}

def inject_data(_data):
    global data
    data = _data

def set_websocket(user_id, websocket):
    global websockets
    websockets[user_id] = websocket

# Welcome new player.
async def welcome(user_id, character_id, clan_id, realm_id, x, y):
    # Currently uses global which is bad because it's not unique for each user.
    global websockets, user_states, scenario
    state = {}
    user_states[user_id] = state

    websocket = websockets[user_id]
    realm = data.get_realm(realm_id)
    prompt = generate_prompt("interactions/introduce_realm", (realm[0], realm[1], realm[2], ))
    introduction = call_openai(prompt, 512)
    await websocket.send("NARRATION:" + introduction)
    character = data.get_character(character_id, True)
    clan = data.get_clan(clan_id, True)
    prompt = generate_prompt("interactions/introduce_player_character", (character[0], character[2], clan[0], clan[2], ))
    introduction = call_openai(prompt, 512)
    await websocket.send("NARRATION:" + introduction)
    location = data.get_map(realm_id, x, y)
    if location is None:
        # Generate new location.
        maps.create_location(realm_id, x, y)
        location = data.get_map(realm_id, x, y)
    data.set_character_location(character_id, realm_id, x, y)
    state['character'] = character
    state['realm'] = realm
    state['clan'] = clan
    state['location'] = location
    # Check if scenario already exists. If not, create one.
    await handle_interactions(user_id)


async def load(user_id):
    global websockets, user_states
    character = data.get_character(character_id, True)
    # Load settings from previous state.
    await handle_interactions(user_id)

async def handle_interactions(user_id):
    global websockets, user_states, scenario
    state = user_states[user_id]
    websocket = websockets[user_id]
    # Handle user commands.
    first = True
    while True:
        character = state['character']
        realm = state['realm']
        clan = state['clan']
        location = state['location']
        scenario = data.get_scenario()
        if scenario is None:
            # setting, history, location details, location items, player's character name, player background, player clan, clan description
            prompt = generate_prompt("interactions/create_scenario", (realm[1], realm[2], location[1], location[2], character[0], character[2], clan[0], clan[2]))
            scenario = call_openai(prompt, 512)
            print("Scenario:" + scenario)
            data.add_scenario(scenario)
            prompt = generate_prompt("interactions/summarize_scenario", (scenario, ))
            summary = call_openai(prompt, 256)
            await websocket.send("NARRATION:" + summary)
        if first:
            first = False
            await websocket.send("WELCOME")
        message = await websocket.recv()
        # setting, location details, items, clan, request
        prompt = generate_prompt("interactions/process_request", (realm[1], location[1], location[2], clan[0], scenario, character[0], message, ))
        response = call_openai(prompt, 512)
        print("Response: " + response)
        await websocket.send("NARRATION:" + response)
        prompt = generate_prompt("interactions/check_updates", (realm[1], location[1], location[2], clan[0], scenario, character[0], message, response, ))
        response = call_openai(prompt, 64)
        row = [column.strip() for column in response.split('|')]
        print(response)
        if row[0].lowercase() == "true":
            prompt = generate_prompt("interactions/update_scenario", (realm[1], location[1], scenario, character[0], message, response, ))
            scenario = call_openai(prompt, 2048)
            print("Updated Scenario:" + scenario)
            data.update_scenario(scenario)
        if row[1].lowercase() == "true":
            # This will use the updated scenario as it was set already.
            prompt = generate_prompt("maps/update_location_details", (realm[1], location[1], scenario, character[0], message, response, ))
            location[1] = call_openai(prompt, 2048)
            print("Updated Details:" + location[1])
            data.update_scenario(scenario)
        if row[2].lowercase() == "true":
            # This will use the updated location details as it was set already.
            prompt = generate_prompt("maps/update_location_items", (realm[1], location[1], scenario, character[0], message, response, ))
            scenario = call_openai(prompt, 2048)
            data.update_scenario(scenario)
