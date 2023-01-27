from generation import generate_prompt
from generation import call_openai

data = None

def inject_data(_data):
    global data
    data = _data

def generate_clans(realm_id, name, setting, history):
    print("Generating Clans")
    # Going to need to create clan physical features for each. That's going to be hard, unless I can just add physical features into the base prompts. I probably can.
    # Separate each clan and clan info into tuples.
    clans = []
    valid_prompt = False
    while not valid_prompt:
        prompt = generate_prompt("clans/generate_clans", (setting, history, name, ))
        clanlist = call_openai(prompt, 1024).split('\n\n')
        # Verify that the format is correct.
        valid_prompt = True
        for clan in clanlist:
            if len(clan.split("|")) != 4:
                print("Incorrect arg count. Trying again...")
                valid_prompt = False
                break
    for clan in clanlist:
        columns = [column.strip() for column in clan[clan.index(".") + 1:].split("|")]
        prompt = generate_prompt("clans/generate_features", (columns[0], columns[2], ))
        features = call_openai(prompt, 1024)
        columns.insert(3, features)
        clans.append(columns)
    print("Clans: " + str(clans))
    data.add_clans(realm_id, clans)

def generate_character(level, clan_id, realm_id, x, y, user_id = None):
    print("Generating Character")
    realm = data.get_realm(realm_id)
    clan = data.get_clan(clan_id)
    cnt = 0
    while cnt != 4:
        prompt = generate_prompt("characters/generate_character", (realm[1], clan[0], clan[2], clan[3], level, ))
        list = call_openai(prompt, 1024)
        parameters = [parameter.strip() for parameter in list.split('|')]
        cnt = len(parameters)
        if cnt != 4:
            print("Incorrect arg count. Trying again...")
    print("Character: " + parameters)
    prompt = generate_prompt("characters/generate_features", (clan[0], clan[2], features, parameters[0], parameters[1], ))
    features = call_openai(prompt, 1024)
    print("Character Features: " + features)
    return data.add_character(clan_id, parameters[0], parameters[1], features, parameters[2], realm_id, x, y, user_id)
