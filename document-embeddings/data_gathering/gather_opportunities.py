import json
import os
import requests

from bs4 import BeautifulSoup
import dateparser

# AHRC, BBSRC, EPSRC, ESRC, MRC, NERC, STFC
urls = {
    'EPSRC': 'https://epsrc.ukri.org/funding/calls/?selectedCallsStatus=Open&pageNumber=1&resultsPerPage=100',
    'NERC': 'https://nerc.ukri.org/funding/application/currentopportunities/',
    'MRC': 'https://mrc.ukri.org/funding/browse/',
    'ESRC': 'https://esrc.ukri.org/funding/funding-opportunities/',
}

rss_feeds = {
    'bbsrc': 'http://feeds.feedburner.com/bbsrcfunding',
    'epsrc': 'https://epsrc.ukri.org/tasks/feed/?feedID=8C271FBA-01C3-4CC9-B908354CC9D8FFEB',
    'nerc': 'https://nerc.ukri.org/site/rss/funding/',
}

import feedparser

def get_rss_calls(name, tags=False):
    feed = feedparser.parse(rss_feeds[name])
    for entry in feed.entries:
        call = {
            'title': entry.title,
            'summary': entry.summary,
            'ref': entry.link,
            
        }
        if 'published_parsed' in entry:
            call['date'] = entry.published_parsed
        elif 'published' in entry:
            call['date'] = entry.published
        if tags and 'tags' in entry:
            call['keywords'] = [tag['term'] for tag in entry.tags]
        yield call

def get_epsrc_calls():
    calls = []
    rss_feed = get_rss_calls('epsrc', tags=True) # tags look like keywords here
    for rss_call in rss_feed:
        call = {}
        calls.append(call)
        call['title'] = rss_call['title']
        call['summary'] = rss_call['summary']
        response = requests.get(rss_call['ref'])
        soup = BeautifulSoup(response.text, 'html.parser')
        content = soup.find('section', {'id': 'itemcontent'})
        metadata = content.find('div', class_='metadata')
        td = metadata.find('td', class_='date issue')
        if td:
            call['issue_date'] = dateparser.parse(td.get_text().strip()).isoformat()
        td = metadata.find('td', class_='date openingdate')
        if td:
            call['opening_date'] = dateparser.parse(td.get_text().strip()).isoformat()
        td = metadata.find('td', class_='date closingdate')
        if td:
            call['closing_date'] = dateparser.parse(td.get_text().strip()).isoformat()
        td = metadata.find('td', class_='status')
        if td:
            call['status'] = td.get_text().strip()
        metadata.decompose()
        call['content'] = content.get_text()
    return calls

if __name__ == "__main__":    
    epsrc_calls = get_epsrc_calls()
    print(f'EPSRC: {len(epsrc_calls)} calls')
    with open(os.path.join(os.path.dirname(__file__), 'opportunities_epsrc.json'), 'w') as f:
        json.dump(epsrc_calls, f, indent=4)

    # nerc_calls = get_calls('nerc')
    # bbsrc_calls = get_calls('bbsrc')
