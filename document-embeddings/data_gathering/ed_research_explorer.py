from datetime import datetime
import json 
import os
import re
import requests

from bs4 import BeautifulSoup

people_url = 'https://www.research.ed.ac.uk/portal/en/organisations/edinburgh-parallel-computing-centre(4a95ea9f-8c95-4d45-aa10-485a08823d53)/persons.html?pageSize=1000&amp;page=0'
outputs_url = 'https://www.research.ed.ac.uk/portal/en/organisations/edinburgh-parallel-computing-centre(4a95ea9f-8c95-4d45-aa10-485a08823d53)/publications.html?pageSize=200&page={page}'

def retrieve_publications(page):
    response = requests.get(outputs_url.format(page=page))
    contents = BeautifulSoup(response.text, 'html.parser')
    items = contents.find_all('li', {'class': 'portal_list_item'})
    print(f'Page {page}: found {len(items)} publications.')
    epcc_publications = []
    for item in items:
        print('.', end='', flush=True)
        title = item.find('h2', {'class': 'title'}).span.get_text()
        publication = item.find('a', {'class': 'link'})
        pubtype = [t for t in publication['rel']]
        publink = publication['href']
        pub_id = publink.replace('https://www.research.ed.ac.uk/portal/en/publications/', '')
        pub_id = pub_id[pub_id.find('(')+1:]
        pub_id = pub_id[:pub_id.find(')')]

        pr = requests.get(publink)
        pub_contents = BeautifulSoup(pr.text, 'html.parser')
        regex = re.compile('relations persons.*')
        persons_list = pub_contents.find('ul', {'class': regex})
        all_persons = []
        uoe_persons = []
        if persons_list is not None:
            for li in persons_list.find_all('li'):
                if li.has_attr('class'):
                    # external author
                    all_persons.append({'name': li.get_text()})
                else:
                    a = li.find('a', {'rel': 'Person'})
                    if a is None:
                        # external person but not marked as external
                        all_persons.append({'name': li.get_text()})
                    else:
                        n = a.get_text()
                        uoe_persons.append(n)
                        all_persons.append({
                            'name': n,
                            'url': a['href']
                        })
        else:
            print(f'\n{publink}')
        abstract_header = pub_contents.find('h3', {'class': 'subheader'}, text='Abstract')
        abstract_text = None
        if abstract_header:
            abstract = abstract_header.find_next('div')
            if abstract:
                abstract_text = abstract.get_text()
        p = {
            'title': title,
            'type': pubtype,
            'authors': uoe_persons,
            'id': pub_id,
            'abstract': abstract_text,
        }
        meta = pub_contents.find('meta', {'name': 'citation_keywords'})
        if meta:
            p['keywords'] = meta['content']
        meta = pub_contents.find('meta', {'name': 'citation_publication_date'})
        if meta:
            p['date'] = meta['content'].replace('/', '-')
    
        p['citation'] = {
            'link': publink,
            'authors': all_persons,
        }
        meta = pub_contents.find('meta', {'name': 'citation_inbook_title'})
        if meta:
            p['citation']['inbook'] = meta['content']
        meta = pub_contents.find('meta', {'name': 'citation_journal_title'})
        if meta:
            p['citation']['journal'] = meta['content']
        meta = pub_contents.find('meta', {'name': 'citation_doi'})
        if meta:
            p['citation']['doi'] = meta['content']


        epcc_publications.append(p)
    print('')
    return epcc_publications

if __name__ == "__main__":
    # # retrieve a list of EPCC staff 
    # response = requests.get(people_url)
    # text = BeautifulSoup(response.text, 'html.parser')
    # people = text.find_all('a', {'rel': 'Person'})
    # epcc_staff = {}
    # print('EPCC staff')
    # for person in people:
    #     name = person.span.get_text()
    #     last_name, first_name = name.split(',')
    #     print(name)
    #     full_name = f'{first_name.strip()} {last_name.strip()}'
    #     epcc_staff[person['href']] = full_name

    page = 0
    epcc_publications = retrieve_publications(page)
    new_publications = epcc_publications
    with open(os.path.join(os.path.dirname(__file__), 'epcc_publications.json'), 'w') as f:
        json.dump(epcc_publications, f, indent=4)
    while new_publications:
        page += 1
        new_publications = retrieve_publications(page)
        epcc_publications += new_publications
        with open(os.path.join(os.path.dirname(__file__), 'epcc_publications.json'), 'w') as f:
            json.dump(epcc_publications, f, indent=4)
    print(f'Complete: Found {len(epcc_publications)} publications')