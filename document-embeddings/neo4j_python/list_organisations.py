import json
import configparser
import os

from neo4j import GraphDatabase


if __name__ == "__main__":

    config = configparser.ConfigParser()
    configfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    config.read(configfile)

    uri = "bolt://roag.is.ed.ac.uk:7687"
    driver = GraphDatabase.driver(uri, auth=(config['auth']['USERNAME'], config['auth']['PASSWORD']))

    query = 'MATCH (o:PURE:OrganisationalUnit) return o.name_value'
    organisations = []
    with driver.session() as session:
        result = session.run(query)
        for r in result:
            organisations.append(r['o.name_value'])
    
    with open(os.path.join(os.path.dirname(__file__), 'uoe_organisations.json'), 'w') as f:
        json.dump(organisations, f, indent=4)