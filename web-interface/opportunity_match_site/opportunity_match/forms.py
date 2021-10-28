from django.contrib.auth.models import User
from django.forms import ModelForm, Form, Textarea, TextInput, ChoiceField
from django.utils import timezone

from .models import UserProfile, Search, Settings

class UserProfileForm(ModelForm):
    class Meta:
        model = UserProfile
        fields = ['name', 'text', 'keywords']
        widgets = {
            "name": TextInput(attrs={'style':"width:100%"}),
            'text': Textarea(attrs={'rows':10, 'style':"width:100%"}),
            'keywords': Textarea(attrs={'rows':2, 'style':"width:100%"}),
        }
    
    def save(self):
        self.instance.created = timezone.now()
        super(UserProfileForm, self).save()

class SearchForm(ModelForm):
    class Meta:
        model = Search
        fields = ['name', 'text', 'keywords', 'shared',]
        labels = {
            "name": "Name your search (optional)",
            "text": "Enter your search as free text",
            "keywords": "Enter keywords for this search",
            "shared": "Share this search",
        }
        widgets = {
            "text": Textarea(attrs={
                'rows':10,
                'style':"width:100%",
            })
        }

class SettingsForm(ModelForm):

    class Meta:
        model = Settings
        fields = ['notifications', ]
        # widgets = {
        #     'keyword_weight': TextInput(
        #         attrs={"class": "slider",
        #             "type": "range",
        #             "min": "0",
        #             "max": "1",
        #             "step": "0.1"})
        # }

class UserForm(ModelForm):
    class Meta:
        model = User
        fields = ['email']