from generation import generate_prompt
from generation import call_openai
from generation import generate_image
import maps
from random import randint

# Note: Probably should be grabbing character by id only. Getting character id from name will be a problem if two people have the same name. But I guess I can just force unique names.

# Will be based on party level at some point.
skill = "novice"
# Difficulty will be set by the players in the future, and will range between novice, casual, standard, advanced, hardcore.
difficulty = "advanced"
players = {}
discussion = ""

data = None
websockets = {}
user_states = {}
processing = False

def inject_data(_data):
    global data
    data = _data

def set_websocket(user_id, websocket):
    global websockets
    websockets[user_id] = websocket

def img_realm(description, history):
    # Generate image of realm
    image_prompt = None
    while image_prompt is None:
        prompt = generate_prompt("interactions/images/realm", (description, history))
        summary = call_openai(prompt, 245)
        if len(summary) < 1000:
            image_prompt = summary
    image_url = generate_image(image_prompt)

# Welcome new player.
async def welcome(user_id, character_id, clan_id, realm_id, x, y):
    # Currently uses global which is bad because it's not unique for each user.
    global websockets, user_states, scenario, players
    state = {}
    user_states[user_id] = state

    websocket = websockets[user_id]
    character = data.get_character(character_id, True)
    realm = data.get_realm(character[5])
    prompt = generate_prompt("interactions/introduce_realm", (realm[0], realm[1], realm[2], ))
    introduction = call_openai(prompt, 512)
    await websocket.send("NARRATION:" + introduction.replace('\n', '\n\n'))
    clan = data.get_clan(clan_id, True)
    prompt = generate_prompt("interactions/introduce_player_character", (character[0], character[2], clan[0], clan[2], ))
    introduction = call_openai(prompt, 512)
    await websocket.send("NARRATION:" + introduction.replace('\n', '\n\n'))
#    await websocket.send("NARRATION:![Current](" + image_url + ")" + introduction.replace('\n', '\n\n'))
    location = data.get_map(realm_id, x, y)
    if location is None:
        # Generate new location.
        maps.create_location(realm_id, x, y)
    data.set_character_location(character_id, realm_id, x, y)
    await load(user_id)

async def load(user_id):
    global websockets, user_states, players
    state = {}
    user_states[user_id] = state
    websocket = websockets[user_id]
    # Load settings from previous state.
    character = data.get_user_character(user_id, True)
    players[character[0]] = user_id
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
    for playersocket in websockets.values():
        if playersocket != websocket:
            websocket.send("SYSTEM:LOGIN!" + character[0])
    await handle_interactions(user_id)

async def handle_interactions(user_id):
    global websockets, user_states, scenario, discussion, processing
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
        current_issue = state.get('current_issue')
        scenario = data.get_scenario()
        setting = data.get_current_setting(user_id)
        story = data.get_story(user_id)
        player_list = ""
        for player in players.keys():
            player_list += player + '\n'
        player_list = player_list.strip()

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
            prompt = generate_prompt("storyline/create_issue", (realm[1], realm[2], location[1], location[2], scenario, setting, ))
            current_issue = call_openai(prompt, 80)
            state['current_issue'] = current_issue
        if first:
            first = False
            # Change to a summary that includes scenario, location, setting, etc.
            prompt = generate_prompt("interactions/summarize_current", (scenario, location[1], setting, state['current_issue']))
            current = call_openai(prompt, 900)
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
        if not processing and message.startswith("MSG:"):
            message = message[4:]
            # Check if the message appears malicious.
            prompt = generate_prompt("logic/check_malicious", (message, ))
            malicious = call_openai(prompt, 32)
            if malicious.lower().startswith("yes"):
                await websocket.send("SYSTEM:MALICIOUS")
            else:
                # Send message to all clients. This message also indicates that the system is going to be processing this message and therefore all clients should wait for "SYSTEM:FINISHED"
                changed = False
                processing = True
                for playersocket in websockets.values():
                    if playersocket != websocket:
                        await playersocket.send("PLAYER:" + character[0] + "!" + message)
                decided = ""
                question = None
                while question is None:
                    prompt = generate_prompt("logic/check_question", (message, ))
                    question = call_openai(prompt, 32).lower()
                    if (not question.startswith("yes")) and (not question.startswith("no")):
                        question = None
                if question.startswith("no"):
                    prompt = generate_prompt("logic/check_players_decided", (current_issue, player_list, discussion, ))
                    decided = call_openai(prompt, 32)

                if decided.lower().startswith("yes"):
                    discussion += character[0] + ": " + message + '\n'

                    # Evaluate the amount of planning and based on the skill level determine whether something goes wrong and how badly.
                    prompt = generate_prompt("logic/evaluate_planning", (current_issue, player_list, discussion, ))
                    # The worse the planning, the more likely it is that something will go wrong.
                    leeway = None
                    # After deciding whether a failure occurs, the combination of bonuses and penalties will determine how badly it goes wrong.
                    bonuses = {'novice': 0, 'initiate': 1, 'adept': 2, 'expert': 3, 'master': 4, 'legendary': 5}
                    difficulty_cost = {'novice': 0, 'casual': 1, 'standard': 2, 'advanced': 4, 'hardcore': 8}
                    bonus = bonuses[skill]
                    penalty = 0
                    while leeway is None:
                        planning = call_openai(prompt, 32).lower()
                        if planning.startswith("poor"):
                            leeway = 2
                            penalty = 5
                        elif planning.startswith("below average"):
                            leeway = 4
                            penalty = 4
                        elif planning.startswith("adequate"):
                            leeway = 8
                            penalty = 3
                        elif planning.startswith("good"):
                            leeway = 16
                            penalty = 2
                        elif planning.startswith("excellent"):
                            leeway = 32
                            penalty = 1
                        elif planning.startswith("extraordinary"):
                            leeway = 64
                            penalty = 0

                    # Increase the chance of something going wrong based on difficulty.
                    # On hardcore, anything less than good will result in instant problem.
                    # On advanced, anything less than adequate will result in an instant problem.
                    leeway = max(1, leeway - difficulty_cost[difficulty])
                    # Roll dice and fail if they roll a 1.
                    roll = randint(1, leeway)
                    failure = (roll == 1)
                    if not failure:
                        prompt = generate_prompt("storyline/progress_successful_round", (realm[1], location[1], location[2], scenario, setting, player_list, current_issue, discussion, ))
                        gm_response = call_openai(prompt, 512)
                    else:
                        failure_levels = ['minor mishap', 'setback', 'failure', 'disaster', 'catastrophe']
                        cap = min(max(0, 4 - bonus + penalty), 4)
                        print("Cap: " + str(cap))
                        failure_level = failure_levels[randint(0, cap)]
                        prompt = generate_prompt("storyline/progress_failed_round", (realm[1], location[1], location[2], scenario, setting, player_list, current_issue, failure_level, discussion, ))
                        gm_response = call_openai(prompt, 512)
                    setting_progression = None
                    items_progression = None
                    location_progression = None
                    scenario_progression = None

                    # Maybe combine setting revision and changes in one chunk so it can be coordinated in correct order
                    old_setting = setting
                    prompt = generate_prompt("logic/check_update_setting", (realm[1], location[1], location[2], scenario, setting, player_list, character[0], message, discussion, ))
                    response = call_openai(prompt, 32)
                    if response.lower().startswith("yes"):
                        changed = True
                        prompt = generate_prompt("storyline/update_setting", (realm[1], setting, location[1], location[2], scenario, player_list, discussion, ))
                        response = None
                        while response is None:
                            response = call_openai(prompt, 1024)
                            if response.find("List of Changes:") != -1:
                                response = response.split("List of Changes:")
                            elif response.find("Changes:") != -1:
                                response = response.split("Changes:")
                            else:
                                response = None
                        setting = response[0].strip()
                        setting_progression = response[1].strip()
                        data.update_current_setting(user_id, setting)
                    else:
                        setting_progression = "None"

                    old_items = location[2]
                    # Should start wrapping these in methods and putting them into their correct files. For instance, maps.check_update_features()
                    prompt = generate_prompt("logic/check_update_location_features", (realm[1], setting, location[1], location[2], scenario, player_list, discussion, ))
                    response = call_openai(prompt, 32)
                    if response.lower().startswith("yes"):
                        changed = True
                        # Should do a sanity check on items to make sure the dimensions make sense.
                        prompt = generate_prompt("maps/update_location_features", (realm[1], setting, location[1], location[2], scenario, player_list, discussion, ))
                        response = None
                        while response is None:
                            response = call_openai(prompt, 1024)
                            if response.find("List of Changes:") != -1:
                                response = response.split("List of Changes:")
                            elif response.find("Changes:") != -1:
                                response = response.split("Changes:")
                            else:
                                response = None
                        items = response[0].strip()
                        response_progression = response[1].strip()
                        data.update_map_items(realm_id, x, y, items)
                        data.update_current_setting(user_id, setting)
                    else:
                        items_progression = "None"

                    old_details = location[1]
                    prompt = generate_prompt("logic/check_update_details", (realm[1], setting, location[1], location[2], scenario, player_list, discussion, ))
                    response = call_openai(prompt, 32)
                    if response.lower().startswith("yes"):
                        changed = True
                        prompt = generate_prompt("maps/update_location_details", (realm[1], setting, location[1], location[2], scenario, player_list, discussion, ))
                        response = None
                        while response is None:
                            response = call_openai(prompt, 1024)
                            if response.find("List of Changes:") != -1:
                                response = response.split("List of Changes:")
                            elif response.find("Changes:") != -1:
                                response = response.split("Changes:")
                            else:
                                response = None
                        location[1] = response[0].strip()
                        location_progression = response[1].strip()
                        data.update_map_description(realm_id, x, y, location[1])
                    else:
                        details_progression = "None"

                    old_scenario = scenario
                    prompt = generate_prompt("logic/check_update_scenario", (realm[1], setting, location[1], location[2], scenario, player_list, discussion, ))
                    response = call_openai(prompt, 32)
                    if response.lower().startswith("yes"):
                        changed = True
                        prompt = generate_prompt("storyline/update_scenario", (realm[1], setting, location[1], location[2], scenario, player_list, discussion, ))
                        response = None
                        while response is None:
                            response = call_openai(prompt, 1024)
                            if response.find("List of Changes:") != -1:
                                response = response.split("List of Changes:")
                            elif response.find("Changes:") != -1:
                                response = response.split("Changes:")
                            else:
                                response = None
                        scenario = response[0].strip()
                        scenario_progression = response[1].strip()
                        data.update_scenario(scenario)
                    else:
                        scenario_progression = "None"

                    if changed:
                        old_story = story
                        prompt = generate_prompt("storyline/progress_story", (story, scenario_progression, details_progression, items_progression, setting_progression, ))
                        response = call_openai(prompt, 1024)
                        data.update_story(user_id, response)

                        # Maybe the new issue shouldn't be updated here, or maybe the new issue should be focused on the aftemath.
                        old_issue = current_issue
                        prompt = generate_prompt("storyline/create_issue", (realm[1], realm[2], location[1], location[2], scenario, setting, ))
                        current_issue = call_openai(prompt, 80)
                        state['current_issue'] = current_issue

                        prompt = generate_prompt("interactions/narrate_developments", (story, scenario_progression, details_progression, items_progression, setting_progression, old_issue, current_issue, ))
                        developments = call_openai(prompt, 800)
                        prompt = generate_prompt("interactions/images/summary", (setting, location[1], location[2]))
                        image_prompt = None
                        while image_prompt is None:
                            summary = call_openai(prompt, 245)
                            if len(summary) < 1000:
                                image_prompt = summary
                        image_url = generate_image(image_prompt)
                        await websocket.send("NARRATION:![Developments](" + image_url + ")" + developments.replace('\n', '\n\n'))
                        # Determine player advancement.
                        prompt = generate_prompt("logic/check_advancement", (story, scenario_progression, details_progression, items_progression, setting_progression, old_issue, current_issue, ))
                        advance = call_openai(prompt, 32)
                        if (advance.lower().startswith("yes")):
                            for player_id in players.values():
                                pass
                    else:
                        prompt = generate_prompt("interactions/images/summary", (setting, location[1], location[2]))
                        image_prompt = None
                        while image_prompt is None:
                            summary = call_openai(prompt, 245)
                            if len(summary) < 1000:
                                image_prompt = summary
                        image_url = generate_image(image_prompt)
                        await websocket.send("NARRATION:![GM Response](" + image_url + ")" + gm_response.replace('\n', '\n\n'))
                    discussion = ""
                elif decided.lower().startswith("unsure"):
                    discussion += character[0] + ": " + message + '\n'
                    prompt = generate_prompt("interactions/request_clarification", (discussion, player_list, ))
                    gm_response = call_openai(prompt, 256)
                else:
                    # Not sure if embeddings would be a better approach here.
                    cnt = 0
                    parameters = None
                    while cnt != 3:
                        prompt = generate_prompt("logic/items/check_items", (character[0], message, ))
                        list = call_openai(prompt, 32)
                        parameters = [parameter.strip() for parameter in list.split('|')]
                        cnt = len(parameters)
                        if cnt != 3:
                            print("Incorrect arg count. Trying again...")
                    if parameters[0].lower() == "yes":
                        character_id = data.get_character_id(parameters[1])
                        character_items = ""
                        if character_id is not None:
                            character_items = data.get_character_items(character_id)
#                        else:
                            # If N/A assume it's about the currnet player.
#                            character_items = data.get_character_items(get_character_id(character[0]))

                        # Can end up making up additional items based on what the player requests might be available.
                        prompt = generate_prompt("logic/items/inject_item_info", (character[0], message, parameters[2], character_items))
                        injection = call_openai(prompt, 64)
                        discussion += "GM Note: " + injection + '\n'

                    # Do I check both items and skills independently?
                    cnt = 0
                    parameters = None
                    while cnt != 3:
                        prompt = generate_prompt("logic/skills/check_skills", (character[0], message, ))
                        list = call_openai(prompt, 32)
                        parameters = [parameter.strip() for parameter in list.split('|')]
                        cnt = len(parameters)
                        if cnt != 3:
                            print("Incorrect arg count. Trying again...")
                    if parameters[0].lower() == "yes":
                        character_id = data.get_character_id(parameters[1])
                        character_skills = ""
                        if character_id is not None:
                            character_skills = data.get_character_skills(character_id)

                        prompt = generate_prompt("logic/skills/inject_skill_info", (character[0], message, parameters[2], character_skills))
                        injection = call_openai(prompt, 64)
                        discussion += "GM Note: " + injection + '\n'
                    discussion += character[0] + ": " + message + '\n'
                    prompt = generate_prompt("interactions/discuss", (realm[1], location[1], location[2], scenario, setting, player_list, character[0], message, current_issue, discussion, ))
                    gm_response = call_openai(prompt, 256)

                if changed:
                    # Check if character items need updating.
                    pass
                processing = False
                for playersocket in websockets.values():
                    await playersocket.send("SYSTEM:FINISHED")

                # Check if discussion was cleared (in other words if the round has played out)
                if discussion != "":
                    discussion += "GM Response: " + gm_response + '\n'
                    await websocket.send("NARRATION:" + gm_response)
        else:
            if processing:
                await websocket.send("SYSTEM:PROCESSING")
