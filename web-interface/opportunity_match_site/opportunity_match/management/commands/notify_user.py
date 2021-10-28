import json

from django.core.management.base import BaseCommand, CommandError
from django.utils import dateparse, timezone
from django.urls import reverse

from opportunity_match.elastic_search import get_document
from opportunity_match.notifications import get_mentions, get_document_matches
from opportunity_match.models import Settings

class Command(BaseCommand):
    help = 'Collects the number of times experts appeared in searches'

    def add_arguments(self, parser):
        parser.add_argument('expert')
        parser.add_argument('-s', '--start', type=dateparse.parse_datetime)
        parser.add_argument('-e', '--end', type=dateparse.parse_datetime, required=False, default=timezone.now())

    def handle(self, *args, **options):
        start_date = options['start']
        end_date = options['end']
        expert = options['expert']
        settings = Settings.objects.filter(uuid=expert).first()
        if settings:
            to_address = settings.user.email
        else:
            self.stdout.write('No email address.')
            return

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
        text = (
            'Here are your updates from Opportunity Match\n\n'
            f'You appeared in {total_mentions} search{plural} this week.\n\n')
        if mentions:
            text += 'These publications and projects were found in searches:\n'
            for m in mentions:
                text += f" - {m['document']['title']}\n"

        text += f'\nView the search{plural} you appeared in at\nhttps://opportunitymatch.epcc.ed.ac.uk{reverse("opportunities")}.'
        self.stdout.write(text)

        import smtplib
        from email.message import EmailMessage

        msg = EmailMessage()
        msg.set_content(text)

        msg['Subject'] = f'You appeared in {total_mentions} search{plural} this week'
        msg['From'] = 'a.krause@epcc.ed.ac.uk'
        msg['To'] = to_address

        s = smtplib.SMTP('smtp.staffmail.ed.ac.uk')
        s.set_debuglevel(2)
        s.send_message(msg)
        s.quit()

        self.stdout.write(f'Sent email to {to_address}')