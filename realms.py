import openai
import io
import characters

data = None

def inject_data(_data):
    global data
    data = _data

def wrapper(func, args):
    return func(*args)

def generate_prompt(job, parameters = None):
    file = open("prompts/" + job + ".txt",mode='r')
    template = file.read()
    file.close()
    if parameters is None:
        return template
    else:
        return wrapper(template.format, parameters)

# So far all calls to openai should work with the same parameters so why repeat code?
def call_openai(prompt):
    openai_response = openai.Completion.create(
        model="text-davinci-003",
        temperature=0.7,
        max_tokens=512,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        prompt=prompt)
    completion = openai_response["choices"][0]["text"].strip()
    return completion

# Create a new realm.
def create_realm():
    print("Creating Realm")
    prompt = generate_prompt("realms/create_realm")
    setting = call_openai(prompt)
    prompt = generate_prompt("realms/name_realm", (setting, ))
    name = call_openai(prompt)
    print("Realm name: " + name)
    print("Realm Setting:\n" + setting)
    realm_id = data.add_realm(name, setting)
    characters.generate_clans(realm_id, setting)
