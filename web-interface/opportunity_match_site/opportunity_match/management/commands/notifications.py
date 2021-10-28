from datetime import timedelta
from dateutil.relativedelta import relativedelta
import json

import smtplib
from email.message import EmailMessage


from django.core.management.base import BaseCommand, CommandError
from django.utils import dateparse, timezone
from django.urls import reverse

from opportunity_match.elastic_search import get_document
from opportunity_match.notifications import get_mentions, get_document_matches
from opportunity_match.models import Settings

class Command(BaseCommand):
    help = 'Notifies users about searches they appeared in'

    def add_arguments(self, parser):
        parser.add_argument('window', choices=['day', 'week', 'month'])
        parser.add_argument('--test', default=False, action='store_true')
        parser.add_argument('--debug-level', default=0, type=int)
    
    def get_matches(self, expert, start_date, end_date, timewindow):
        matches, matching_searches = get_document_matches(expert, start_date, end_date)
        total_mentions = 0
        documents = {}
        mentions = []
        for doc_id, num_mentions in matches.items():
            total_mentions += num_mentions
            documents[doc_id] = get_document(doc_id)
            mentions.append({'document': documents[doc_id], 'mentions': num_mentions})
        
        if total_mentions == 1:
            plural = ''
        else:
            plural = 'es'
        subject = f'You appeared in {total_mentions} search{plural} in the last {timewindow}'
        text = (
            'Here are your updates from Opportunity Match\n\n'
            f'{subject}.\n\n')
        if mentions:
            text += 'These publications and projects were found in searches:\n'
            for m in mentions:
                text += f" - {m['document']['title']}\n"

        text += f'\nView the search{plural} you appeared in at\nhttps://opportunitymatch.epcc.ed.ac.uk{reverse("opportunities")}.'
        return subject, text
    
    def send_email(self, to_address, subject, text, debuglevel):
        msg = EmailMessage()
        msg.set_content(text)

        msg['Subject'] = subject
        msg['From'] = 'opportunity-match@ed.ac.uk'
        msg['To'] = to_address

        s = smtplib.SMTP('smtp.staffmail.ed.ac.uk')
        s.set_debuglevel(debuglevel)
        s.send_message(msg)
        s.quit()

        self.stdout.write(f'Sent email to {to_address}')


    def handle(self, *args, **options):
        timewindow = options['window']
        end_date = timezone.now()
        period = Settings.NotificationPeriod.NEVER
        if timewindow == 'day':
            start_date = end_date - timedelta(days=1)
            period = Settings.NotificationPeriod.DAY
        elif timewindow == 'week':
            start_date = end_date - timedelta(days=7)
            period = Settings.NotificationPeriod.WEEK
        elif timewindow == 'month':
            start_date = end_date + relativedelta(months=-1)
            period = Settings.NotificationPeriod.MONTH

        for settings in Settings.objects.filter(notifications=period).exclude(uuid__isnull=True).all():
            to_address = settings.user.email
            expert = settings.uuid
            if not to_address:
                continue
            
            subject, text = self.get_matches(expert, start_date, end_date, timewindow)
            self.stdout.write(f'================================================================')
            self.stdout.write(f'Time window: {start_date} to {end_date} ({timewindow})')
            self.stdout.write(f'Notifying user: {to_address}')

            if options['test']:
                self.stdout.write(f'Subject: {subject}')
                self.stdout.write(text)
            else:
                self.send_email(to_address, subject, text, options['debug_level'])