import requests

from bs4 import BeautifulSoup

urls = [
    'https://www.ukri.org/news/decarbonising-heating-and-cooling-for-net-zero-survey-of-needs/'
    'https://efi.ed.ac.uk/research-awards-2/',
    'https://bbsrc.ukri.org/funding/filter/2019-bacterial-plant-diseases-coordination-team/',
    'https://www.airguide.soton.ac.uk/news/6594',
    'https://www.hfsp.org/funding/hfsp-funding/research-grants',
    'https://mrc.ukri.org/funding/browse/nrpnutrition/uk-nutrition-research-partnership-uk-nrp-travelling-skills-awards-for-nutrition-related-research/',
    'https://nerc.ukri.org/funding/application/currentopportunities/announcement-of-opportunity-enabling-research-in-smart-sustainable-plastic-packaging/',
    'https://www.ukri.org/funding/funding-opportunities/healthy-ageing-catalyst-awards-2020/',
    'https://wellcome.ac.uk/grant-funding/schemes/sir-henry-dale-fellowships'
]

closed = 'https://epsrc.ukri.org/funding/calls/newapproachestodatascience/',

def get_text_from_url(url):
    response = requests.get(url)
    contents = BeautifulSoup(response.text, 'html.parser').get_text()
    return contents