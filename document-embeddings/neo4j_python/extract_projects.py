import argparse
import json
import configparser
import os

from neo4j import GraphDatabase


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--organisation', help='Organisational unit', nargs='+')
    parser.add_argument('-f', '--output-file', help='Research output file', required=True)
    # parser.add_argument('-a', '--authors-file', help='Authors file', required=True)
    args = parser.parse_args()

    config = configparser.ConfigParser()
    configfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    config.read(configfile)

    uri = "bolt://roag.is.ed.ac.uk:7687"
    driver = GraphDatabase.driver(uri, auth=(config['auth']['USERNAME'], config['auth']['PASSWORD']))
    
    where_clause = ' OR '.join([f"o.name_value = '{org}'" for org in args.organisation])
    query = f'''
            MATCH (o:PURE:OrganisationalUnit)
            --(person:PURE:Person)
            --(project:PURE:Project) 
            WHERE {where_clause}
            RETURN project, person
        '''
    print(query)

    projects = {}
    with driver.session() as session:
        result = session.run(query)
        for r in result:
            pers_node = r['person']
            person = {
                'uuid': pers_node['uuid'],
                'url': pers_node['info_portalUrl'],
                'name': f"{pers_node['name_firstName']} {pers_node['name_lastName']}",
            }
            proj = r['project']
            if proj['uuid'] in projects:
                if person not in projects[proj['uuid']]['people']:
                    projects[proj['uuid']]['people'].append(person)
            else:
                projects[proj['uuid']] = {
                    'title': proj['title'],
                    'description': proj['description'],
                    'keywords': proj['keywords'],
                    'startDate': proj['period_startDate'],
                    'endDate': proj['period_endDate'],
                    'people': [person],
                }
    with open(os.path.join(os.path.dirname(__file__), args.output_file), 'w') as f:
        json.dump(projects, f, indent=4)
    print(f'Found {len(projects)} projects')
        