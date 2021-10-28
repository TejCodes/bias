import argparse
import json
import configparser
import os

from neo4j import GraphDatabase


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--organisation', help='Organisational unit', nargs='+')
    parser.add_argument('-f', '--output-file', help='Output file', required=True)
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
            WHERE {where_clause}
            RETURN person, o.name_value AS organisation
        '''
    print(query)

    staff = {}
    with driver.session() as session:
        result = session.run(query)
        for r in result:
            pers_node = r['person']
            pers_id = pers_node['uuid']
            org = r['organisation']
            if pers_id not in staff:
                staff[pers_id] = {
                    'uuid': pers_node['uuid'],
                    'url': pers_node['info_portalUrl'],
                    'name': f"{pers_node['name_firstName']} {pers_node['name_lastName']}",
                    'organisation': [org],
                }
            else:
                staff[pers_id]['organisation'].append(org)
    with open(os.path.join(os.path.dirname(__file__), args.output_file), 'w') as f:
        json.dump(staff, f, indent=4)
    print(f'Found {len(staff)} staff')
        