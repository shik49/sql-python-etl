import requests
import json
import twitterAuth
import sqlite3

# spider of people I follow and the people I follow, follow.

conn = sqlite3.connect('friends.sqlite')
cur = conn.cursor()

cur.execute('''CREATE TABLE IF NOT EXISTS People
                (id INTEGER PRIMARY KEY, name TEXT UNIQUE, retrieved INTEGER)''')
cur.execute('''CREATE TABLE IF NOT EXISTS Follows
                (from_id INTEGER, to_id INTEGER, UNIQUE(from_id, to_id))''')

TWITTER_URL = 'https://api.twitter.com/1.1/friends/list.json'

while True:
    acct = input("Enter a twitter account, or quit: ")
    if (acct == 'quit'):
        break
    if len(acct) < 1:
        cur.execute('SELECT id, name FROM People WHERE retrieved = 0 LIMIT 1')
        try:
            (id, acct) = cur.fetchone()
        except:
            print('No unretrieved Twitter accounts found')
            continue
    else:
        cur.execute('SELECT id FROM People WHERE name = ?', (acct, ))
        try:
            id = cur.fetchone()[0]
        except:
            cur.execute('''INSERT OR IGNORE INTO People
                            (name, retrieved) VALUES (?, 0)''', (acct, ))
            conn.commit()
            if cur.rowcount != 1: # affected row count from above query
                print('Error inserting account:', acct)
                continue
            id = cur.lastrowid
    params = {'screen_name': acct, 'count': 100}
    try:
        data = requests.get(TWITTER_URL, auth=twitterAuth.oauth, params=params)
    except Exception as e:
        print(e)
        break

    headers = data.headers

    print(f"Remaining: {headers['x-rate-limit-remaining']}")

    try:
        json_data = json.loads(data.text)
    except:
        print('Unable to parse json')
        print(data)
        break

    if 'users' not in json_data:
        print('Incorrect JSON received')
        print(json.dumps(json_data, indent=4))
        continue

    cur.execute('UPDATE People SET retrieved=1 WHERE name = ?', (acct, ))

    countnew = 0
    countold = 0

    for u in json_data['users']:
        friend = u['screen_name']
        print(friend)
        cur.execute('SELECT id FROM People WHERE name = ? LIMIT 1', (friend, ))
        try:
            friend_id = cur.fetchone()[0]
            countold = countold + 1
        except:
            cur.execute('INSERT OR IGNORE INTO People (name, retrieved) VALUES (?, 0)', (friend, ))
            conn.commit()
            if cur.rowcount != 1:
                print('Error inserting account:', friend)
                continue
            friend_id = cur.lastrowid
            countnew = countnew + 1

        cur.execute('''INSERT OR IGNORE INTO Follows (from_id, to_id)
                        VALUES (?, ?)''', (id, friend_id))
    print('New accounts=', countnew, 'Revisited=', countold)
    conn.commit()
cur.close()
