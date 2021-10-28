from collections import defaultdict
import json

from opportunity_match.models import UserProfile, Settings
from opportunity_match.elastic_search import generate_user_profiles

from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Extracts user profiles from database'

    def add_arguments(self, parser):
        parser.add_argument('--output')
        parser.add_argument('--elasticsearch', default=False, action='store_true')

    def handle(self, *args, **options):

        output_file = options['output']
        if output_file and options['elasticsearch']:
            result = list(generate_user_profiles('expertise'))
            with open(output_file, 'w') as f:
                json.dump(result, f)
        elif output_file:
            result = []
            for p in generate_user_profiles('expertise'):
                result.append({
                    'document_id': p['_source']['document_id'],
                    'text': p['_source']['abstract'],
                })
            with open(output_file, 'w') as f:
                json.dump(result, f)
            self.stdout.write(f'Wrote {len(result)} user profiles to {output_file}')
        else:
            self.stdout.write(json.dumps(list(generate_user_profiles('expertise')), indent=4))
