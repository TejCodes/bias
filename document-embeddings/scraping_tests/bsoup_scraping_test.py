import requests
from bs4 import BeautifulSoup

''' Method for extracting the text of an URL
using BeautifulSoup (using URL from a funding call)'''


def extract_text_from_url(url_input):

    r = requests.get(url_input)
    
    soup = BeautifulSoup(r.text, features="lxml")

    # kill all script and style elements
    for script in soup(["script", "style"]):
        script.extract()    # rip it out

    # get text
    text = soup.get_text()

    # break into lines and remove leading and trailing space on each
    lines = (line.strip() for line in text.splitlines())
    
    # break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    
    # drop blank lines
    text = '\n'.join(chunk for chunk in chunks if chunk)
    return text


text=extract_text_from_url("https://www.ukri.org/news/decarbonising-heating-and-cooling-for-net-zero-survey-of-needs/")
print(text)
