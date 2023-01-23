from generation import generate_prompt
from generation import call_openai

data = None

def inject_data(_data):
    global data
    data = _data

def generate_clans(realm_id, name, setting, history):
    print("Generating Clans")
    prompt = generate_prompt("characters/generate_clans", (setting, history, name, ))
    clanlist = call_openai(prompt, 1024)
    # Separate each clan and clan info into tuples.
    clans = [[element.strip() for element in clan[clan.index(".") + 1:].split("|")] for clan in clanlist.split('\n\n')]
    print("Clans: " + str(clans))
    data.add_clans(realm_id, clans)

# Add a column for physical description. Probably in a second table, using more prompts.
def generate_character(level, clan_id, realm_id, x, y, user_id = None):
    print("Generating Character")
    realm = data.get_realm(realm_id)
    clan = data.get_clan(clan_id)
    cnt = 0
    while cnt != 3:
        prompt = generate_prompt("characters/generate_character", (realm[1], clan[0], clan[1], clan[2], level, ))
        list = call_openai(prompt, 1024)
        print(list)
        parameters = [parameter.strip() for parameter in list.split('|')]
        cnt = len(parameters)
        if cnt != 3:
            print("Incorrect arg count. Trying again...")
    return data.add_character(clan_id, parameters[0], parameters[1], parameters[2], realm_id, x, y, user_id)
