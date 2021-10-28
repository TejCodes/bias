from django.urls import path

from . import views

urlpatterns = [
    path('', views.search_detail, name='index'),
    # path('profile', views.profile, name='profile'),
    path('profile', views.profile, name='profile'),
    path('person/<person_id>', views.person, name='person'),
    path('userprofile/', views.edit_profile, name='edit_profile'),
    path('userprofile/<int:profile_id>', views.edit_profile, name='edit_profile_id'),
    path('userprofile/<int:profile_id>/delete', views.delete_profile, name='delete_profile'),
    path('opportunities', views.opportunities, name='opportunities'),
    path('settings', views.settings, name='settings'),
    path('settings/edit', views.update_settings, name='update_settings'),
    path('searches', views.SearchView.as_view(), name='searches'),
    path('searches/<int:search_id>', views.search_detail, name='search_detail'),
    path('searches/<int:search_id>/visibility', views.search_visibility, name='search_visibility'),
    path('result/export/<int:search_id>', views.export_search_results, name='export_result'),
    path('result/<int:search_id>', views.display_search, name='search_result'),
    path('about', views.about, name='about'),
]