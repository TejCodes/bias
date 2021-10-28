#!/bin/bash
set -x
source /opt/anaconda/etc/profile.d/conda.sh

# index data from ROAG
conda activate /home/akrause/.conda/envs/oppmatch_model
cd /root/document-embeddings/production/
python index_roag.py

# extract profiles and index in Elasticsearch
conda activate /usr/local/venvs/oppmatch_django
cd /var/www/opportunity_match/web-interface/opportunity_match_site/
python manage.py extract_profiles --elasticsearch --output /root/document-embeddings/production/profiles.json
conda activate /home/akrause/.conda/envs/oppmatch_model
cd /root/document-embeddings/production/
python index_profiles.py
