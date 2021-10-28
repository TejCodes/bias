import requests
from textpipe import doc, pipeline

''' Requirements:
   pip install spacy
   python -m spacy download en_core_web_sm
   pip install pip install textpipe 

In this version we are going to use textpipe instead of bsoup.

textpipe is a Python package for converting raw text in to clean, 
readable text and extracting metadata from that text. 

Important: Gensim models + TextPipe: https://github.com/textpipe/textpipe 

Its functionalities include transforming raw text into readable text 
by removing HTML tags and extracting metadata such as the number 
of words and named entities from the text '''


def extract_text_from_url(url_input):

    r = requests.get(url_input)
    document = doc.Doc(r.text)

    #print(document.clean)
    #print(document.language)
    #print(document.nwords)

    pipe = pipeline.Pipeline(['CleanText', 'NWords'])
    return pipe(r.text)

if __name__ == "__main__":

   list_urls=[]
   list_urls.append("https://www.ukri.org/news/decarbonising-heating-and-cooling-for-net-zero-survey-of-needs/")
   list_urls.append("https://www.events.ed.ac.uk/index.cfm?event=showEventDetails&scheduleId=37896&start=&eventStart=0&eventProviderId=21")
   list_urls.append("https://efi.ed.ac.uk/research-awards-2/")
   list_urls.append("https://bbsrc.ukri.org/funding/filter/2019-bacterial-plant-diseases-coordination-team/")
   list_urls.append("https://www.airguide.soton.ac.uk/news/6594")
   list_urls.append("https://www.hfsp.org/funding/hfsp-funding/research-grants")
   list_urls.append("https://mrc.ukri.org/funding/browse/nrpnutrition/uk-nutrition-research-partnership-uk-nrp-travelling-skills-awards-for-nutrition-related-research/")
   list_urls.append("https://nerc.ukri.org/funding/application/currentopportunities/announcement-of-opportunity-enabling-research-in-smart-sustainable-plastic-packaging/")
   list_urls.append("https://www.ukri.org/funding/funding-opportunities/healthy-ageing-catalyst-awards-2020/")
   list_urls.append("https://wellcome.ac.uk/grant-funding/schemes/sir-henry-dale-fellowships")

   id=0
   for url in list_urls:
      text=extract_text_from_url(url)
      print("Document ID {} - CleanText {} - NumWords {} \n".format(id, text["CleanText"], text["NWords"]))
      print("------------------------------\n")
      id += 1
