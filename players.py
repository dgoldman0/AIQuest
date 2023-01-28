from generation import generate_prompt
from generation import call_openai
from generation import generate_image
import maps

# Thinking of options to expand to multiple players. I would expand "Player's Character" to list of player characters, and the message of the player. Additionally, I could have a collector prompt system that collects the conversation and then sends the full results to the story stepping system. Basically, it would be a coordination phase. I would need a logic prompt to determine whether to finalize the sequence of events or keep listening for more user input.

users = []
discussion = ""

data = None
websockets = {}
user_states = {}

def inject_data(_data):
    global data
    data = _data

def set_websocket(user_id, websocket):
    global websockets
    websockets[user_id] = websocket

def img_realm(description, history):
    # Generate image of realm
    while image_prompt is None:
        prompt = generate_prompt("interactions/images/realm", (description, history))
        summary = call_openai(prompt, 245)
        if len(summary) < 1000:
            image_prompt = summary
    image_url = generate_image(image_prompt)


# Welcome new player.
async def welcome(user_id, character_id, clan_id, realm_id, x, y):
    # Currently uses global which is bad because it's not unique for each user.
    global websockets, user_states, scenario
    state = {}
    user_states[user_id] = state

    websocket = websockets[user_id]
    prompt = generate_prompt("interactions/introduce_realm", (realm[0], realm[1], realm[2], ))
    introduction = call_openai(prompt, 512)
    await websocket.send("NARRATION:" + introduction.replace('\n', '\n\n'))
#    image_url = img_realm()
#    await websocket.send("NARRATION:![Current](" + image_url + ")" + introduction.replace('\n', '\n\n'))
    character = data.get_character(character_id, True)
    realm = data.get_realm(character[5])
    clan = data.get_clan(clan_id, True)
    prompt = generate_prompt("interactions/introduce_player_character", (character[0], character[2], clan[0], clan[2], ))
    introduction = call_openai(prompt, 512)
    await websocket.send("NARRATION:" + introduction.replace('\n', '\n\n'))
#    await websocket.send("NARRATION:![Current](" + image_url + ")" + introduction.replace('\n', '\n\n'))
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
    state['realm_id'] = realm_id
    state['x'] = x
    state['y'] = y
    # Check if scenario already exists. If not, create one.
    await handle_interactions(user_id)


async def load(user_id):
    global websockets, user_states
    state = {}
    user_states[user_id] = state
    websocket = websockets[user_id]
    # Load settings from previous state.
    character = data.get_user_character(user_id, True)
    realm_id = character[5]
    clan_id = character[1]
    x = character[6]
    y = character[7]
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
    global websockets, user_states, scenario, discussion
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
        current_issue = state['current_issue']
        scenario = data.get_scenario()
        setting = data.get_current_setting(user_id)
        story = data.get_story(user_id)
        if scenario is None:
            # setting, history, location details, location items, player's character name, player background, player clan, clan description
            prompt = generate_prompt("storyline/create_scenario", (realm[1], realm[2], location[1], location[2], character[0], character[2], clan[0], clan[2]))
            scenario = call_openai(prompt, 256)
            data.add_scenario(scenario)
        if setting is None:
            prompt = generate_prompt("storyline/create_setting", (realm[1], realm[2], location[1], location[2], scenario, ))
            setting = call_openai(prompt, 400)
            data.update_current_setting(user_id, setting)
        if story is None:
            story = scenario
            data.update_story(user_id, story)
        if current_issue is None:
            prompt = generate_prompt("storyline/create_issue", realm[1], realm[2], location[1], location[2], scenario, setting, )
            current_issue = call_openai(prompt, 64)
            state['current_issue'] = current_issue
        if first:
            first = False
            # Change to a summary that includes scenario, location, setting, etc.
            prompt = generate_prompt("interactions/summarize_current", (scenario, location[1], setting))
            current = call_openai(prompt, 512)
            image_prompt = None
            prompt = generate_prompt("interactions/images/summary", (setting, location[1], location[2]))
            while image_prompt is None:
                summary = call_openai(prompt, 245)
                if len(summary) < 1000:
                    image_prompt = summary
            image_url = generate_image(image_prompt)
            await websocket.send("NARRATION:![Current](" + image_url + ")" + current.replace('\n', '\n\n'))
            await websocket.send("WELCOME")
        message = await websocket.recv()
        # Replace round_duration with "current issue." Then ask something like "have the players addressed the current issue?"
        if message.startswith("MSG:"):
            message = message[4:]
            # For now it's just the one character, but that'll change over time.
            players = character[0]
            discussion += character[0] + ": " + message + '\n'
            prompt = generate_prompt("logic/check_players_decided", (setting, current_issue, discussion, players, ))
            decided = call_openai(prompt, 32)
            # Add the response so the GM response doesn't accidentally trigger a "yes" answer.
            if decided.lower().startswith("yes"):
                prompt = generate_prompt("storyline/progress_round", (realm[1], location[1], location[2], scenario, setting, players, character[0], message, current_issue, discussion, ))
                gm_response = call_openai(prompt, 256)
                # Check update for setting, location items, location details, and
                # Check update might work well in Curie in which case I could save a few cents.
                setting_progression = None
                items_progression = None
                location_progression = None
                scenario_progression = None
                changed = False

                # Maybe combine setting revision and changes in one chunk so it can be coordinated in correct order
                old_setting = setting
                prompt = generate_prompt("logic/check_update_setting", (realm[1], location[1], location[2], scenario, setting, players, character[0], message, discussion, ))
                response = call_openai(prompt, 32)
                if response.lower().startswith("yes"):
                    changed = True
                    prompt = generate_prompt("storyline/update_setting", (realm[1], setting, location[1], location[2], scenario, players, discussion, ))
                    response = None
                    while response is None:
                        response = call_openai(prompt, 1024)
                        if response.find("List of Changes:") != -1:
                            response = response.split("List of Changes:")
                        elif response.find("Changes:") != -1:
                            response = response.split("Changes:")
                    setting = response[0].strip()
                    setting_progression = response[1].strip()
                    data.update_current_setting(user_id, setting)
                else:
                    setting_progression = "None"

                old_items = location[2]
                # Should start wrapping these in methods and putting them into their correct files. For instance, maps.check_update_features()
                prompt = generate_prompt("logic/check_update_location_features", (realm[1], setting, location[1], location[2], scenario, players, discussion, ))
                response = call_openai(prompt, 32)
                if response.lower().startswith("yes"):
                    changed = True
                    # Should do a sanity check on items to make sure the dimensions make sense.
                    prompt = generate_prompt("maps/update_location_features", (realm[1], setting, location[1], location[2], scenario, players, discussion, ))
                    response = None
                    while response is None:
                        response = call_openai(prompt, 1024)
                        if response.find("List of Changes:") != -1:
                            response = response.split("List of Changes:")
                        elif response.find("Changes:") != -1:
                            response = response.split("Changes:")
                    items = response[0].strip()
                    response_progression = response[1].strip()
                    data.update_map_items(realm_id, x, y, items)
                    data.update_current_setting(user_id, setting)
                else:
                    items_progression = "None"

                old_details = location[1]
                prompt = generate_prompt("logic/check_update_details", (realm[1], setting, location[1], location[2], scenario, players, discussion, ))
                response = call_openai(prompt, 32)
                if response.lower().startswith("yes"):
                    changed = True
                    prompt = generate_prompt("maps/update_location_details", (realm[1], setting, location[1], location[2], scenario, players, discussion, ))
                    response = None
                    while response is None:
                        response = call_openai(prompt, 1024)
                        if response.find("List of Changes:") != -1:
                            response = response.split("List of Changes:")
                        elif response.find("Changes:") != -1:
                            response = response.split("Changes:")
                    location[1] = response[0].strip()
                    location_progression = response[1].strip()
                    data.update_map_description(realm_id, x, y, location[1])
                else:
                    details_progression = "None"

                old_scenario = scenario
                prompt = generate_prompt("logic/check_update_scenario", (realm[1], setting, location[1], location[2], scenario, players, discussion, ))
                response = call_openai(prompt, 32)
                if response.lower().startswith("yes"):
                    changed = True
                    prompt = generate_prompt("storyline/update_scenario", (realm[1], setting, location[1], location[2], scenario, players, discussion, ))
                    response = None
                    while response is None:
                        response = call_openai(prompt, 1024)
                        if response.find("List of Changes:") != -1:
                            response = response.split("List of Changes:")
                        elif response.find("Changes:") != -1:
                            response = response.split("Changes:")
                    scenario = response[0].strip()
                    scenario_progression = response[1].strip()
                    data.update_scenario(scenario)
                else:
                    scenario_progression = "None"

                if changed:
                    old_story = story
                    prompt = generate_prompt("storyline/progress_story", (story, scenario_progression, details_progression, items_progression, setting_progression, ))
                    response = call_openai(prompt, 1024)
                    discussion = ""
                    data.update_story(user_id, response)

                    prompt = generate_prompt("storyline/create_issue", realm[1], realm[2], location[1], location[2], scenario, setting, )
                    current_issue = call_openai(prompt, 64)
                    state['current_issue'] = current_issue

                    prompt = generate_prompt("interactions/narrate_developments", (story, scenario_progression, details_progression, items_progression, setting_progression, ))
                    developments = call_openai(prompt, 800)
                    prompt = generate_prompt("interactions/images/summary", (setting, location[1], location[2]))
                    image_prompt = call_openai(prompt, 245)
                    image_url = generate_image(image_prompt)
                    await websocket.send("NARRATION:![Developments](" + image_url + ")" + developments.replace('\n', '\n\n'))
                else:
                    prompt = generate_prompt("interactions/images/summary", (setting, location[1], location[2]))
                    image_prompt = None
                    while image_prompt is None:
                        summary = call_openai(prompt, 245)
                        if len(summary) < 1000:
                            image_prompt = summary
                    image_url = generate_image(image_prompt)
                    await websocket.send("NARRATION:![GM Response](" + image_url + ")" + gm_response.replace('\n', '\n\n'))
                    return
            elif decided.lower().startswith("unsure"):
                prompt = generate_prompt("interactions/request_clarification", (discussion, players, ))
                gm_response = call_openai(prompt, 256)
            else:
                prompt = generate_prompt("interactions/discuss", (realm[1], location[1], location[2], scenario, setting, players, character[0], message, current_issue, discussion, ))
                gm_response = call_openai(prompt, 256)

            discussion += "GM Response: " + gm_response + '\n'
            await websocket.send("NARRATION:" + gm_response)
        else:
            pass
        await websocket.send("FINISHED") # Indicates finished with current narration.
