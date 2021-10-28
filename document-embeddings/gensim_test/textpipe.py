import requests
from textpipe import doc, pipeline 

import spacy
nlp = spacy.load('en')

''' Requirements:
   pip install spacy
   python -m spacy download en_core_web_sm
   pip install pip install textpipe 

   In this version, we are going to apply a pre-trained module (gensim_test_en.kv)
   to generate the embbedings. 

'''

def extract_text_apply_pipe(url_input):

    r = requests.get(url_input)
    #steps = [('Raw',), ('NWords',), ('Complexity',), ('CleanText',), ('Entities',)] 
    
    steps = [('NWords',), ('Complexity',), ('CleanText',)] 
    steps.append(('GensimDocumentEmbedding', {
        'model_mapping': {
            'en': 'gensim_test_en.kv'
        }
    }))
    pipe = pipeline.Pipeline(steps)
    pipe(r.text)
    return pipe(r.text), doc.Doc(r.text)


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


   docs=[]
   pipes=[]
   for url in list_urls:
      pipe_url, doc_url =extract_text_apply_pipe(url)
      print("----Pipe -------")
      print("{}\n".format(pipe_url))
      docs.append(doc_url)
      pipes.append(pipe_url)


   # Extract and rank key terms in the document by proxying to
   # `textacy.keyterms`. Returns a list of (term, score) tuples. Depending
   # on the ranking algorithm used, terms can consist of multiple words.

   #Available rankers are TextRank (textrank), SingleRank (singlerank) and
   # SGRank ('sgrank').
   
   print("KeyTerms:\n")      
   id=0
   for d in docs:
       print("-----------")
       print("Document{}, keyterms {} \n".format(id, d.extract_keyterms(ranker="textrank")))
       id += 1 

   print("##############") 
   print("Similarity:\n")      
   for d_i in range(len(docs)):
      for j in range (len(docs)):
           print("Similarity between {} and {} is: {}\n".format(d_i, j, docs[d_i].similarity(docs[j])))
   

