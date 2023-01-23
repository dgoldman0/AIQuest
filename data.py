import bcrypt
import sqlite3
import magic
import realms

# Might be interesting to allow multiple worlds/realms at some point.

# Connect to local file database which will be used to store user information, etc. Maybe one day replace with full MySQL
print("Connecting to database.")

# Load database and check for previous system history. That way we don't have to go through the whole bootup process each time, and if the system goes out at one pont it can be rebooted where it was left off.
database = sqlite3.connect("aiquest.db")

def init():
    # Check if already initialized
    global database
    cur = database.cursor()
    try:
        res = cur.execute("SELECT TRUE FROM USERS WHERE rowid = 0")
    except Exception as err:
        print(err)
        if str(err) == "no such table: USERS":
            print("First initialization...")
            # Create user tables.
            cur.execute("CREATE TABLE USERS (username TEXT NOT NULL, passwd TEXT NOT NULL, salt TEXT NOT NULL, admin INT DEFAULT FALSE);")
#            username = input("Desired username: ")
#            password1 = ""
#            password2 = None
#            while password1 != password2:
#                password1 = input("Enter password: ")
#                password2 = input("Repeat password: ")
            username = "admin"
            password1 = "password"
            salt = bcrypt.gensalt()
            password = bcrypt.hashpw(password1.encode(), salt)
            cur.execute("INSERT INTO USERS (username, passwd, salt, admin) VALUES (?, ?, ?, ?);", (username, password, salt, True))
            cur.execute("CREATE TABLE CHARACTERS (user_id INT, current_realm INT NOT NULL, x_loc INT NOT NULL, y_loc INT NOT NULL, player INT NOT NULL DEFAULT FALSE);")
            cur.execute("CREATE TABLE CHARACTER_DETAILS (character_id INT NOT NULL, name TEXT NOT NULL, clan_id INT NOT NULL, background TEXT NOT NULL, affinities TEXT NOT NULL);")
            # Basic World Settings Table
            cur.execute("CREATE TABLE REALMS (name TEXT NOT NULL, setting TEXT NOT NULL);")
            # Clan List Table
            cur.execute("CREATE TABLE CLANS (realm_id INT NOT NULL, name TEXT NOT NULL, description TEXT NOT NULL, affinities TEXT NOT NULL);")
            # Create spell tables.
            cur.execute("CREATE TABLE SPELLS (name TEXT NOT NULL, elements TEXT NOT NULL, tier TEXT NOT NULL, cost INT NOT NULL, description TEXT NOT NULL, mishaps TEXT);")
            # Create map tables.
            cur.execute("CREATE TABLE MAPS (realm INT NOT NULL DEFAULT 0, x INT NOT NULL, y INT NOT NULL, last_explored INT NOT NULL DEFAULT -1, description TEXT NOT NULL, items TEXT);")
            database.commit()
            # Create initial realm.
            realms.create_realm()
            # Initialize novice spells.
            magic.initialize_spells()

# User Data
def get_user(username):
    return None

def add_user(username, password, salt):
    pass

# Realm Data

def add_realm(name, setting):
    global database
    cur = database.cursor()
    cur.execute("INSERT INTO REALMS (name, setting) VALUES (?, ?);", (name, setting, ))
    id = cur.lastrowid
    database.commit()
    return id

def get_setting(realm = 0):
    global database
    cur = database.cursor()
    res = cur.execute("SELECT name, setting FROM REALM WHERE rowid = ?;", (realm, ))
    return res.fetchone()

# Spell Data
def add_spell(spell):
    global database
    cur = database.cursor()

    lines = spell.split('\n\n')
    name = lines[0].split(':')[1].strip()
    elements = lines[1].split(':')[1].strip()
    tier = lines[2].split(':')[1].strip()
    cost = int(lines[3].split(':')[1].strip())
    description = lines[4].split(':')[1].strip()

    cur.execute("INSERT INTO SPELLS (name, elements, tier, cost, description) VALUES (?, ?, ?, ?, ?);", (name, elements, tier, cost, description, ))
    id = cur.lastrowid
    database.commit()
    return id

def set_mishaps(id, mishaps):
    global database
    cur = database.cursor()
    cur.execute("UPDATE SPELLS SET mishaps = ? WHERE rowid = ?", (mishaps, id, ))
    database.commit()

def get_spell(id):
    global database
    cur = database.cursor()
    res = cur.execute("SELECT name, elements, tier, cost, description FROM SPELLS WHERE rowid = ?", (id, ))
    return res.fetchone()

# Realm Data
def get_realmlist():
    global database
    cur = database.cursor()
    res = cur.execute("SELECT rowid, name, setting FROM REALMS;")
    return res.fetchall()

def get_realm(realm_id = 0):
    cur = database.cursor()
    res = cur.execute("SELECT name, description FROM REALMS WHERE rowid = ?;", (realm_id, ))
    return res.fetchone()

# Character Data
def get_clanlist(realm_id):
    global database
    cur = database.cursor()
    res = cur.execute("SELECT rowid, name, description, affinities FROM REALMS;")
    return res.fetchall()

def add_clans(realm_id, clans):
    global database
    cur = database.cursor()
    # It's okay to inject realm_id because it has to be an integer.
    realm_id = str(int(realm_id))
    cur.executemany("INSERT INTO CLANS (realm_id, name, description, affinities) VALUES (" + realm_id + ", ?, ?, ?);", clans)
    database.commit()

def get_clan(clan_id):
    global database
    cur = database.cursor()
    res = cur.execute("SELECT name, description, affinities FROM REALMS WHERE rowid = ?;", (clan_id))
    return res.fetchone()

def add_character(clan_id, name, background, affinities, current_realm, x, y, user_id, player):
    global database
    cur = database.cursor()
    cur.execute("INSERT INTO CHARACTERS (user_id, clan_id, name, background, affinities, player) VALUES (?, ?, ?, ?, ?, ?);", (user_id, clan_id, name, background, affinities, player))
    id = cur.lastrowid
    database.commit()
    return id

def update_character_location():
    global database
    cur = database.cursor()
    database.commit()

def update_character_background():
    global database
    cur = database.cursor()
    database.commit()

def get_character(character_id):
    global database
    cur = database.cursor()

# Map Data
def map_initialized(realm = 0):
    global database
    cur = database.cursor()
    res = cur.execute("SELECT COUNT(*) FROM MAPS WHERE realm = ?;", (realm, ))
    resp = res.fetchone()
    return resp > 0

def get_map(realm, x, y):
    global database
    cur = database.cursor()
    res = cur.execute("SELECT last_explored, description, items FROM MAPS WHERE realm = ? and x = ? and y = ?", (realm, x, y, ))
    resp = res.fetchone()
    return resp

def add_map(realm, x, y, details):
    global database
    cur = database.cursor()
    res = cur.execute("INSERT INTO MAPS (realm, x, y, details)", (realm, x, y, details, ))
    database.commit()

def update_map_details(realm, x, y, details):
    pass

def update_map_items(realm, x, y, items):
    pass
