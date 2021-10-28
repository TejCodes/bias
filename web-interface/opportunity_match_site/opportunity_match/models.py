from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from datetime import datetime
import json

class Settings(models.Model):

    class NotificationPeriod(models.IntegerChoices):
        NEVER = 0, _('Never')
        DAY = 1, _('Once a day')
        WEEK = 2, _('Once a week')
        MONTH = 3, _('Once a month')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,)
    url = models.TextField()
    uuid = models.CharField(max_length=128)
    notifications = models.IntegerField(
        choices = NotificationPeriod.choices,
        default = NotificationPeriod.NEVER
    )
    keyword_weight = models.FloatField(default=0.2)

    def __str__(self):
        return f'Settings: {self.user.username}'

class UserProfile(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,)
    name = models.CharField(max_length=64)
    text = models.TextField()
    # comma-separated list of keywords
    keywords = models.TextField(blank=True, default='')
    created = models.DateTimeField(default=datetime.utcnow)

class Search(models.Model):
    name = models.CharField(max_length=200, blank=True, default='', help_text='Your search name. This is optional and is not used in the search.')
    text = models.TextField(blank=True, default='', help_text='Add longer texts here that you would like to match to documents.')
    keywords = models.CharField(max_length=500, blank=True, default='')
    timestamp = models.DateTimeField(default=datetime.utcnow)
    shared = models.BooleanField(default=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,)

    def __str__(self):
        return f'Search(id={self.id}, "{self.name}")'

class SearchResult(models.Model):
    search = models.ForeignKey(Search, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=datetime.utcnow)
    results = models.TextField(blank=True, default='')

    @property
    def results_as_dict(self):
        if self.results:
            try:
                return json.loads(self.results)
            except:
                pass
        return None
