import asyncio
import websockets
import players
import ssl
import pathlib
import bcrypt
import characters
from random import randint
import json

data = None

def inject_data(_data):
    global data
    data = _data

async def handle_player(websocket, path = None):
    print("Connected")
    global user_connections, data
    user = None

    # Check to see if Authenticate user.
    await websocket.send("AIQuest")
    response = await websocket.recv()
    if response is not None:
        if response.startswith("AUTH:"):
            username = response[5:]
            # rowid, username, passwd, salt
            user = data.get_user_by_username(username)
            if user is None:
                print("Unidentified user: " + username)
                await websocket.send("UNKNOWN")
                return
            else:
                await websocket.send("CHALLENGE:" + str(user[3]))
                response = await websocket.recv()
                if response is not None:
                    if response == user[2]:
                        players.set_websocket(user[0], websocket)
                        await player.load(user[0])

        elif response.startswith("REGISTER:"):
            username = response[9:]
            user = data.get_user(username)
            if user is None:
                salt = bcrypt.gensalt().decode()
                await websocket.send("CHALLENGE:" + salt)
                password = await websocket.recv()
                # Have user select realm.
                realmlist = data.get_realmlist()
                print(realmlist)
                await websocket.send("REALMS:" + json.dumps(realmlist))
                realm_id = None
                while realm_id is None:
                    selection = await websocket.recv()
                    try:
                        realm = int(selection)
                        if realm > 0 and realm <= len(realmlist):
                            realm_id = realm
                        else:
                            await websocket.send("INVALIDREALM")
                    except:
                        await websocket.send("INVALIDREALM")

                clanlist = data.get_clanlist(realm_id)
                await websocket.send("CLANS:" + json.dumps(clanlist))
                clan_id = None
                while clan_id is None:
                    selection = await websocket.recv()
                    try:
                        clan = int(selection)
                        if clan > 0 and clan <= len(clanlist):
                            clan_id = clan
                        else:
                            await websocket.send("INVALIDCLAN")
                    except:
                        await websocket.send("INVALIDCLAN")

                print("Adding User")
                user_id = data.add_user(username, password, salt)

                # Place user randomly into the realm.
                x = randint(0, 20000000)
                y = randint(0, 20000000)
                character_id = characters.generate_character('novice', clan_id, realm_id, x, y, user_id)
                players.set_websocket(user_id, websocket)
                await websocket.send("SUCCESS")
                await players.welcome(user_id, character_id, clan_id, realm_id, x, y)
            else:
                await websocket.send("EXISTINGUSER")

async def listen(url = "localhost", port = 9289, secure = False):
    start_server = None
    if secure:
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(
            pathlib.Path(__file__).with_name('localhost.pem'))
        print("Listening for chat incoming connections (secure).")
        async with websockets.serve(handle_player, url, port, ssl = ssl_context):
            await asyncio.Future()  # run forever
    else:
        print("Listening for chat incoming connections (unsecure).")
        async with websockets.serve(handle_player, url, port):
            await asyncio.Future()  # run forever
