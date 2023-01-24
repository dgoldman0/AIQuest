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
    state['character'] = list(character)
    state['realm'] = list(realm)
    state['clan'] = list(clan)
    state['location'] = list(location)
    # Check if scenario already exists. If not, create one.
    await handle_interactions(user_id)


async def load(user_id):
    global websockets, user_states
    state = {}
    user_states[user_id] = state
    websocket = websockets[user_id]
    # Load settings from previous state.
    character = data.get_user_character(user_id, True)
    print(character)
    realm_id = character[4]
    clan_id = character[1]
    x = character[5]
    y = character[6]
    location = data.get_map(realm_id, x, y)

    realm = data.get_realm(realm_id)
    clan = data.get_clan(clan_id, True)
    state['character'] = list(character)
    state['realm'] = list(realm)
    state['clan'] = list(clan)
    state['location'] = list(location)
    state['realm_id'] = realm_id
    state['x'] = x
    state['y'] = y
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
        realm_id = state['realm_id']
        x = state['x']
        y = state['y']
        scenario = data.get_scenario()
        setting = data.get_current_setting(user_id)
        story = data.get_story(user_id)
        if scenario is None:
            # setting, history, location details, location items, player's character name, player background, player clan, clan description
            prompt = generate_prompt("storyline/create_scenario", (realm[1], realm[2], location[1], location[2], character[0], character[2], clan[0], clan[2]))
            scenario = call_openai(prompt, 256)
            print("Scenario:" + scenario)
            data.add_scenario(scenario)
        if setting is None:
            prompt = generate_prompt("storyline/create_setting", (realm[1], realm[2], location[1], location[2], scenario, ))
            setting = call_openai(prompt, 400)
            print("Setting:" + setting)
            data.update_current_setting(user_id, setting)
        if story is None:
            story = scenario
            data.update_story(user_id, story)
        if first:
            first = False
            # Change to a summary that includes scenario, location, setting, etc.
            prompt = generate_prompt("interactions/summarize_current", (setting, location[1], setting))
            summary = call_openai(prompt, 128)
            await websocket.send("NARRATION:" + summary)
            await websocket.send("WELCOME")
        message = await websocket.recv()
        # Eventually change process_request so that it's a decider that will select between different message processors depending on the message details.
        # setting, location details, items, clan, request
        prompt = generate_prompt("interactions/process_request", (realm[1], location[1], location[2], clan[0], scenario, setting, character[0], message, ))
        response = call_openai(prompt, 256)
        print("Response: " + response)
        # Check update for setting, location items, location details, and
        # Check update might work well in Curie in which case I could save a few cents.
        setting_progression = None
        items_progression = None
        location_progression = None
        scenario_progression = None

        old_setting = setting
        prompt = generate_prompt("logic/check_update_setting", (realm[1], setting, location[1], location[2], clan[0], scenario, character[0], message, response, ))
        response = call_openai(prompt, 32)
        print("Update Setting: " + response)
        if response.lower().startswith("yes"):
            prompt = generate_prompt("characters/update_setting", (realm[1], location[1], location[2], scenario, setting, character[0], message, response, ))
            setting = call_openai(prompt, 512)
            data.update_current_setting(user_id, setting)
            prompt = generate_prompt("storyline/comparisons/setting", (old_setting, setting, ))
            setting_progression = call_openai(prompt, 512)
            await websocket.send("NARRATION:" + setting_progression)
        else:
            setting_progression = "None"

        old_items = location[2]
        prompt = generate_prompt("logic/check_update_items", (realm[1], setting, location[1], location[2], clan[0], scenario, character[0], message, response, ))
        response = call_openai(prompt, 32)
        print("Update Items: " + response)
        if response.lower().startswith("yes"):
            # Should do a sanity check on items to make sure the dimensions make sense.
            prompt = generate_prompt("maps/update_location_items", (realm[1], location[1], location[2], scenario, setting, character[0], message, response, ))
            items = call_openai(prompt, 1024)
            data.update_map_items(realm_id, x, y, items)
            data.update_current_setting(user_id, setting)
            prompt = generate_prompt("storyline/comparisons/items", (old_items, items, ))
            items_progression = call_openai(prompt, 1024)
            await websocket.send("NARRATION:" + items_progression)
        else:
            items_progression = "None"

        old_details = location[1]
        prompt = generate_prompt("logic/check_update_details", (realm[1], setting, location[1], location[2], clan[0], scenario, character[0], message, response, ))
        response = call_openai(prompt, 32)
        print("Update Details: " + response)
        if response.lower().startswith("yes"):
            prompt = generate_prompt("maps/update_location_details", (realm[1], location[1], location[2], scenario, setting, character[0], message, response, ))
            details = call_openai(prompt, 256)
            location[1] = details
            print("\nUpdated Details:" + details)
            data.update_map_description(realm_id, x, y, details)
            prompt = generate_prompt("storyline/comparisons/details", (old_details, details, ))
            details_progression = call_openai(prompt, 256)
            await websocket.send("NARRATION:" + details_progression)
        else:
            details_progression = "None"

        old_scenario = scenario
        prompt = generate_prompt("logic/check_update_scenario", (realm[1], setting, location[1], location[2], clan[0], scenario, character[0], message, response, ))
        response = call_openai(prompt, 32)
        print("Update Scenario: " + response)
        if response.lower().startswith("yes"):
            prompt = generate_prompt("storyline/update_scenario", (realm[1], location[1], location[2], scenario, setting, character[0], message, response, ))
            scenario = call_openai(prompt, 256)
            print("\nUpdated Scenario:" + scenario)
            data.update_scenario(scenario)
            prompt = generate_prompt("storyline/comparisons/items", (old_scenario, scenario, ))
            scenario_progression = call_openai(prompt, 256)
            await websocket.send("NARRATION:" + scenario_progression)
        else:
            scenario_progression = "None"

        old_story = story
        prompt = generate_prompt("storyline/progress_story", (story, scenario_progression, details_progression, items_progression, setting_progression, ))
        print("\n\nPrompt:" + prompt)
        response = call_openai(prompt, 1024)
        data.update_story(user_id, response)
        await websocket.send("FINISHED") # Indicates finished with current narration.
