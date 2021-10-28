from collections import defaultdict
import configparser
import json
import os

import MySQLdb

if __name__ == "__main__":
    config = configparser.ConfigParser()
    configfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    config.read(configfile)

    db = MySQLdb.connect(
            user=config['mysql']['USERNAME'], 
            passwd=config['mysql']['PASSWORD'],
            db=config['mysql']['DATABASE'])


    c = db.cursor()
    # modify this to retrieve only public searches, or include private
    shared_only = False # all searches for now
    c.execute('SELECT * FROM opportunity_match_search')
    row = c.fetchone()
    all_searches_by_user = defaultdict(list)
    while row is not None:
        s = {
            'id': row[0],
            'name': row[1],
            'text': row[2],
            'timestamp': row[3].isoformat(),
        }
        all_searches_by_user[row[4]].append(s)
        row = c.fetchone()
    
    all_searches = []
    for user_id, searches in all_searches_by_user.items():
        c.execute(f'''
        SELECT uuid, auth_user.id, first_name, last_name 
        FROM opportunity_match_settings 
        RIGHT OUTER JOIN auth_user 
        ON user_id=auth_user.id 
        WHERE auth_user.id={user_id}
        ''')
        settings = c.fetchone()
        for s in searches:
            s['person'] = {
                'id': settings[1],
                'name': f'{settings[2]} {settings[3]}',
            }
            if settings[0]:
                s['person']['uuid'] = settings[0]
            all_searches.append(s)
    
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'all_searches.json'), 'w') as f:
        json.dump(all_searches, f, indent=4)