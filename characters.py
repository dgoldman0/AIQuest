import openai
import io

data = None

def inject_data(_data):
    global data
    data = _data

def wrapper(func, args):
    return func(*args)

def generate_prompt(job, parameters):
    file = open("prompts/" + job + ".txt",mode='r')
    template = file.read()
    file.close()
    return wrapper(template.format, parameters)

# So far all calls to openai should work with the same parameters so why repeat code?
def call_openai(prompt):
    openai_response = openai.Completion.create(
        model="text-davinci-003",
        temperature=0.7,
        max_tokens=1024,
        top_p=1,
        frequency_penalty=0.1,
        presence_penalty=0,
        prompt=prompt)
    completion = openai_response["choices"][0]["text"].strip()
    return completion

def generate_clans(realm_id, setting):
    print("Generating Clans")
    prompt = generate_prompt("characters/generate_clans", (setting, ))
    clanlist = call_openai(prompt)
    # Separate each clan and clan info into tuples.
    clans = [[element.strip() for element in clan.split("|")] for clan in clanlist.split('\n\n')]
    print("Clans: " + str(clans))
    data.add_clans(realm_id, clans)

def generate_character(clan_id, realm_id, x, y, user_id = None, player = None):
    realm = data.get_realm(realm_id)
    clan = data.get_clan(clan_id)
    prompt = generate_prompt("characters/generate_character", realm['setting'], clan['name'], clan['description'], clan['affinities'])
    list = call_openai(prompt)
    parameters = [parameter.strip() for parameter in list.split('|')]
    return data.add_character(clan_id, name, background, affinities, realm_id, x, y, user_id, player)
