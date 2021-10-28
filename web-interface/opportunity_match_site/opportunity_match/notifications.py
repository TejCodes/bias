from collections import defaultdict

from django.db.models import F, Count
from django.urls import reverse

from .models import SearchResult
from .search import create_results, normalise_and_sort
from .elastic_search import generate_publications, get_profile_document_ids, get_document
        
def get_mentions(start_date, end_date):
    search_results = (
        SearchResult.objects
            .filter(search__timestamp=F('timestamp'))
            .filter(timestamp__lte=end_date)
            .filter(timestamp__gte=start_date)   
    )
    mentions = defaultdict(int)
    for simdoc in search_results:
        results = create_results(
            [(simdoc.document, simdoc.similarity)],
            resolve_urls=False)
        for r in results:
            for uuid in r['document']['experts']:
                mentions[uuid] += 1
    return mentions

def get_document_matches(pure_id, start_date, end_date, topn=10):
    my_docs = set([d.document_id for d in get_profile_document_ids(pure_id)])
    mentions = defaultdict(int)
    matching_searches = {}
    search_results = (
        SearchResult.objects
            .filter(search__timestamp=F('timestamp'))
            .filter(timestamp__lte=end_date)
            .filter(timestamp__gte=start_date))
    for search_result in search_results:
        if search_result.results:
            documents = set()
            all_results = normalise_and_sort(search_result.results_as_dict.values())
            for doc_id, sim in all_results[:topn]:
                if doc_id in my_docs:
                    documents.add(doc_id)
                    mentions[doc_id] += 1
            if documents and search_result.search.shared:
                matching_searches[search_result.search.id] = {
                    'search': search_result.search,
                    'documents': documents,
                }

    return mentions, matching_searches

def get_notification_text(pure_id, start_date, end_date, topn=10):
    matches, matching_searches = get_document_matches(pure_id, start_date, end_date, topn)
    total_mentions = 0
    documents = {}
    mentions = []
    for doc_id, num_mentions in matches.items():
        total_mentions += num_mentions
        documents[doc_id] = get_document(doc_id)
        mentions.append({'document': documents[doc_id], 'mentions': num_mentions})
    
    text = (
        f'You appeared in {total_mentions} searches this week.\n\n'
        'These publications and projects were found in searches:\n')
    for m in mentions:
        text += f" - {m['document']['title']}\n"

    text += f'\nView the searches you appeared in at https://opportunitymatch.epcc.ed.ac.uk/opportunity_match{reverse("opportunities")}.'
    
    return text