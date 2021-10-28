#!/bin/bash
set -x
source /opt/anaconda/etc/profile.d/conda.sh
today=$(date +'%Y%m%d')

mkdir -p /var/www/opportunity_match/models/$today
conda activate /usr/local/venvs/oppmatch_django
cd /var/www/opportunity_match/web-interface/opportunity_match_site/
python manage.py build_search_model /var/www/opportunity_match/models/$today/doc2vec_search.model
