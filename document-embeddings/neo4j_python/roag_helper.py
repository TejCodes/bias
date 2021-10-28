def get_gtr_project(driver, project_id):
    query = f'''
        MATCH (proj:GTR:Project {{id: {project_id}}})
        -- (:GTR:Person)
        - [:ROAG_CANONICAL_ID_FOR]-()-[:ROAG_CANONICAL_ID_FOR] 
        - (p:PURE:Person)
        RETURN p, proj
    '''
    project = None
    with driver.session() as session:
        result = session.run(query)
        members = []
        member_ids = set()
        for r in result:
            if project is None:
                project = {
                    'id': r['proj']['id'],
                    'title': r['proj']['title'],
                    'abstract': r['proj']['abstractText'],
                }
            person_id = r['p']['uuid']
            person = {
                'name': f"{r['p']['name_firstName']} {r['p']['name_lastName']}",
                'url': r['p']['info_portalUrl'],
                'uuid': person_id,
            }
            if person_id not in member_ids:
                members.append(person)
                member_ids.add(person_id)
        if project:
            project['members'] = members
    return project

def get_research_output(driver, doc_id):
    document = None
    with driver.session() as session:        
        query = f"""
            MATCH (r:PURE:ResearchOutput) -- (p:PURE:Person)
            WHERE r.uuid = '{doc_id}' 
            RETURN r, p
        """
        result = session.run(query)
        author_ids = set()
        authors = []
        for r in result:
            if document is None:
                resout_node = r['r']
                document = {
                    'id': resout_node['uuid'],
                    'url': resout_node['info_portalUrl'],
                    'abstract' : resout_node['abstract_value'],
                    'title': resout_node['title'],
                    'keywords': resout_node['keywords'],
                }

            author_id = r['p']['uuid']
            author = {
                'name': f"{r['p']['name_firstName']} {r['p']['name_lastName']}",
                'url': r['p']['info_portalUrl'],
                'uuid': author_id,
            }
            if author_id not in author_ids:
                authors.append(author)
                author_ids.add(author_id)
    
        document['authors'] = authors

    return document