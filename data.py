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
            cur.execute("CREATE TABLE CHARACTERS (user_id INT, name TEXT NOT NULL);")
            cur.execute("CREATE TABLE CHARACTER_DETAILS (character_id INT NOT NULL, clan_id INT NOT NULL, background TEXT NOT NULL, affinities TEXT NOT NULL);")
            cur.execute("CREATE TABLE CHARACTER_LOCATION (character_id INT NOT NULL, realm_id INT NOT NULL, x INT NOT NULL, y INT NOT NULL);")
            # Basic World Settings Table
            cur.execute("CREATE TABLE REALMS (name TEXT NOT NULL, setting TEXT NOT NULL, history TEXT NOT NULL);")
            # Clan List Table
            cur.execute("CREATE TABLE CLANS (realm_id INT NOT NULL, name TEXT NOT NULL, short_description TEXT NOT NULL, long_description TEXT NOT NULL, affinities TEXT NOT NULL);")
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
def get_user(user_id):
    global database
    cur = database.cursor()
    res = cur.execute("SELECT username, passwd, salt FROM USERS WHERE rowid = ?;", (user_id, ))
    return res.fetchone()

def add_user(username, password, salt):
    global database
    cur = database.cursor()
    cur.execute("INSERT INTO USERS (username, passwd, salt, admin) VALUES (?, ?, ?, FALSE);", (username, password, salt))
    id = cur.lastrowid
    database.commit()
    return id

# Realm Data
def add_realm(name, setting, history):
    global database
    cur = database.cursor()
    cur.execute("INSERT INTO REALMS (name, setting, history) VALUES (?, ?, ?);", (name, setting, history, ))
    id = cur.lastrowid
    database.commit()
    return id

def get_setting(realm = 1):
    global database
    cur = database.cursor()
    res = cur.execute("SELECT setting FROM REALM WHERE rowid = ?;", (realm, ))
    return res.fetchone()

def get_history(realm = 1):
    global database
    cur = database.cursor()
    res = cur.execute("SELECT setting FROM REALM WHERE rowid = ?;", (realm, ))
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

def get_realm(realm_id = 1):
    cur = database.cursor()
    res = cur.execute("SELECT name, setting, history FROM REALMS WHERE rowid = ?;", (realm_id, ))
    return res.fetchone()

# Character Data
def get_clanlist(realm_id, full = False):
    global database
    cur = database.cursor()
    res = None
    if full:
        res = cur.execute("SELECT rowid, name, short_description, long_description, affinities FROM CLANS;")
    else:
        res = cur.execute("SELECT rowid, name, short_description, affinities FROM CLANS;")
    return res.fetchall()

def add_clans(realm_id, clans):
    global database
    cur = database.cursor()
    # It's okay to inject realm_id because it has to be an integer.
    realm_id = str(int(realm_id))
    cur.executemany("INSERT INTO CLANS (realm_id, name, short_description, long_description, affinities) VALUES (" + realm_id + ", ?, ?, ?, ?);", clans)
    database.commit()

def get_clan(clan_id, full = False):
    global database
    cur = database.cursor()
    print(clan_id)
    if full:
        res = cur.execute("SELECT name, short_description. long_description, affinities FROM CLANS WHERE rowid = ?;", (clan_id, ))
    else:
        res = cur.execute("SELECT name, long_description, affinities FROM CLANS WHERE rowid = ?;", (clan_id, ))
    return res.fetchone()

def get_user_character(user_id):
    global database
    cur = database.cursor()
    res = cur.execute("SELECT character_id, name FROM CHARACTERS WHERE user_id = ?;", (user_id, ))
    return res.fetchone()

def get_character(character_id, full = False):
    global database
    cur = database.cursor()
    if full:
        sql = """SELECT c.name, cd.clan_id, cd.background, cd.affinities, cl.realm_id, cl.x, cl.y
        FROM characters c
        JOIN character_details cd
        ON c.user_id = cd.character_id
        JOIN character_location cl
        ON cd.character_id = cl.character_id
        WHERE cd.character_id = ?"""

        cursor.execute(sql, (character_id,))
    else:
        res = cur.execute("SELECT user_id, name FROM CHARACTERS WHERE rowid = ?;", (character_id, ))
    return res.fetchone()


def add_character(clan_id, name, background, affinities, realm_id, x, y, user_id):
    global database
    cur = database.cursor()
    cur.execute("INSERT INTO CHARACTERS (user_id, name) VALUES (?, ?);", (user_id, name))
    character_id = cur.lastrowid
    cur.execute("INSERT INTO CHARACTER_DETAILS (character_id, clan_id, background, affinities) VALUES (?, ?, ?, ?)", (character_id, clan_id, background, affinities, ))
    cur.execute("INSERT INTO CHARACTER_LOCATION (character_id, realm_id, x, y) VALUES (?, ?, ?, ?)", (character_id, realm_id, x, y, ))
    database.commit()
    return character_id

def update_character_location(realm_id, x, y):
    global database
    cur = database.cursor()
    database.commit()

def update_character_background(character_id, background):
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
