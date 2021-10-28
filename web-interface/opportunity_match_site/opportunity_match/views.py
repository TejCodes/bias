from collections import defaultdict
from datetime import datetime, timedelta

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.detail import DetailView

from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from django.views import generic
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.utils import timezone

from .models import Search, SearchResult, Settings
from .notifications import get_document_matches
from .forms import UserProfileForm, SearchForm, UserProfile, SettingsForm, UserForm
from .elastic_search import generate_publications, get_document, get_person
from .search import SEARCHES, create_results, render_results, normalise_and_sort
from .visualisations import plot_profile_wordcloud, create_profile_graph


def about(request):
    return render(request, 'opportunity_match/about.html')

@login_required
def profile(request):
    try:
        settings = Settings.objects.get(user=request.user)
        publications = generate_publications(settings.uuid)
        wordcloud = plot_profile_wordcloud(settings.uuid)
        graph = create_profile_graph(settings.uuid)
    except Settings.DoesNotExist:
        publications = []
        wordcloud = None
        graph = None

    profiles = UserProfile.objects.filter(user=request.user).order_by('-created')
    return render(
        request, 
        'opportunity_match/profile.html', 
        {
            'profiles': profiles,
            'publications': publications,
            'image_base64': wordcloud,
            'graph': graph,
        }
    )

@login_required
def person(request, person_id):
    person = get_person(person_id)
    if person is None:
        return HttpResponseNotFound('Not found.')
    profiles = UserProfile.objects.filter(user__settings__uuid=person_id).order_by('-created').all()
    return render(
        request, 
        'opportunity_match/profile.html',
        {
            'person': person,
            'profiles': profiles,
            'publications': generate_publications(person_id),
            'image_base64': plot_profile_wordcloud(person_id),
            'graph': create_profile_graph(person_id),
        }
    )

@login_required
def edit_profile(request, profile_id=None):
    item = None
    if profile_id is not None:
        try:
            item = UserProfile.objects.filter(user=request.user).get(id=profile_id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound('Not found.')
    if request.method == 'GET':
        form = UserProfileForm(instance=item)
        return render(request, 
            'opportunity_match/edit_profile.html', 
            {'form': form, 'update': (item is not None)})
    else:
        if 'delete' in request.POST:
            item.delete()
        else:
            if not item:
                item = UserProfile(user=request.user)
            updated_profile = UserProfileForm(request.POST, instance=item)
            updated_profile.save()
        return redirect('profile')

@login_required
def delete_profile(request, profile_id):
    if request.method == 'POST':
        profile = UserProfile.objects.get(profile_id)
        if profile.user == request.user:
            profile.delete()
    return redirect('profile')        

@login_required
def opportunities(request):
    try:
        settings = Settings.objects.get(user=request.user)
    except Settings.DoesNotExist:
        return render(request,
            'opportunity_match/opportunities.html',
            {'matches': [], 'total_searches': 0, 'searches': {}}
        )

    end = timezone.now()
    start = end - timedelta(days=7)
    matches, matching_searches = get_document_matches(settings.uuid, start, end)
    mentions = []
    total_mentions = 0
    documents = {}
    for doc_id, num_mentions in matches.items():
        total_mentions += num_mentions
        documents[doc_id] = get_document(doc_id)
        mentions.append({'document': documents[doc_id], 'mentions': num_mentions})
    for m in matching_searches.values():
        m['documents'] = [documents[doc_id] for doc_id in m['documents']]
    # ms = get_matching_searches(settings.uuid, start, end)
    # matching_searches = defaultdict(lambda: {'documents': []})
    # for r in ms:
    #     matching_searches[r.search.id].update({
    #         'search': r.search,
    #         # 'similarity': r.similarity,
    #     })
    #     matching_searches[r.search.id]['documents'].append(get_document(r.document)),

    return render(request, 
        'opportunity_match/opportunities.html', 
        {'matches': mentions, 'total_searches': total_mentions, 'searches': matching_searches}
    )

@login_required
def search_visibility(request, search_id):
    if request.method == 'POST':
        vis = request.POST['shared']
        try:
            item = Search.objects.get(id=search_id)
            if item.user != request.user:
                item = None
        except ObjectDoesNotExist:
            item = None
        if item is None:
            return HttpResponseNotFound()
        item.shared = (vis == 'shared')
        item.save()
        return HttpResponse('OK')


@login_required
def search_detail(request, search_id=None):
    item = None
    if search_id:
        try:
            item = Search.objects.get(id=search_id)
            if item.user != request.user:
                item = None
        except ObjectDoesNotExist:
            item = None
    if request.method == 'GET':
        form = SearchForm(instance=item)
        return render(request, 'opportunity_match/search.html', {'form': form })
    else:
        timestamp = timezone.now()
        if item is None or (
                item.text != request.POST['text'] 
                or item.name != request.POST['name']
                or item.keywords != request.POST['keywords']):
            item = Search(user=request.user)
        item.timestamp = timestamp
        form = SearchForm(request.POST, instance=item)
        form.save()
        results = SEARCHES['v1'].render(form.instance)
        return redirect('search_result', search_id=item.id)

@login_required
def display_search(request, search_id):
    try:
        search = Search.objects.get(id=search_id)
    except ObjectDoesNotExist:
        return HttpResponseNotFound('Not found.')
    timestamp = request.GET.get('timestamp', search.timestamp)
    search_results = (
        SearchResult.objects
            .filter(search=search)
            .filter(timestamp=timestamp)
            .order_by('-timestamp')
        )
    if search.shared or search.user == request.user:
        all_results = []
        if search_results.first():
            result_docs = search_results.first().results_as_dict
            if result_docs:
                all_results = normalise_and_sort(result_docs.values())
        paginator = Paginator(all_results, 10)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        result_page = render_results(search, page_obj)
        expand_search = (request.GET.get('expand', 'false') == 'true')
        result_page[1]['expand_search'] = expand_search
        result_page[1]['page_obj'] = page_obj
        if page_number == 1:
            similar_searches = SEARCHES['search'].render(search)
            result_page[1]['similar_searches'] = similar_searches
        return render(request, *result_page)
    else:
        return HttpResponseNotFound('Not found.')

@login_required
def export_search_results(request, search_id):
    try:
        search = Search.objects.filter(user=request.user).get(id=search_id)
    except ObjectDoesNotExist:
        return HttpResponseNotFound('Not found.')
    search_results = (
        SearchResult.objects
            .filter(search=search)
            .filter(timestamp=search.timestamp)
            .order_by('-timestamp')
        )

    if 'text/csv' in request.META['HTTP_ACCEPT']:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="search-result.csv"'
        writer = csv.writer(response)
        writer.writerow(['document_id, similarity'])
        for simdoc in search_results:
            writer.writerow([sim.document, simdoc.similarity])
        return response

    similar_docs = [(simdoc.document, simdoc.similarity) for simdoc in search_results]
    result_documents = create_results(similar_docs, resolve_urls=False)

    export = []
    for doc in result_documents:
        export.append({
            'similarity': doc['similarity'],
            'document': {
                'uuid': doc['document']['document_id'],
                'title': doc['document']['title'],
                'experts': doc['document']['source']['names'],
            }
        })

    return JsonResponse({
        'search': search_id, 
        'timestamp': search.timestamp, 
        'results': export,
    })



class SearchView(LoginRequiredMixin, generic.ListView):
    context_object_name = 'searches'

    def get_queryset(self):
        return Search.objects.filter(user=self.request.user).order_by('-timestamp')

    def post(self, request, *args, **kwargs):
        todelete = [int(d) for d in request.POST.getlist('delete')]
        Search.objects.filter(user=request.user).filter(id__in=todelete).delete()
        return self.get(request, args, kwargs)

@login_required
def settings(request):
    if request.method == 'GET':
        try:
            settings = Settings.objects.get(user=request.user)
        except Settings.DoesNotExist:
            settings = Settings()
        return render(request, 
            'opportunity_match/settings.html',
            {'settings': settings}
        )

@login_required
def update_settings(request):
    try:
        settings = Settings.objects.get(user=request.user)
    except Settings.DoesNotExist:
        settings = Settings(user=request.user)
    user_form = UserForm(instance=request.user)
    settings_form = SettingsForm(instance=settings)
    if request.method == 'GET':
        return render(request, 
            'opportunity_match/update_settings.html',
            {'settings': settings_form, 'user': user_form}
        )
    else:
        settings.notifications = request.POST['notifications']
        settings.save()
        request.user.email = request.POST['email']
        request.user.save()
        return redirect('settings')
