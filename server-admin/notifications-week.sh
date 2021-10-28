#!/bin/bash
cd /var/www/opportunity_match/web-interface/opportunity_match_site/
conda activate /usr/local/venvs/oppmatch_django
python manage.py notifications week >> /var/www/opportunity_match/scripts/logs/notifications.log 2>&1
