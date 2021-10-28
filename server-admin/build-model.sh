#!/bin/bash
set -x
source /opt/anaconda/etc/profile.d/conda.sh

# extract profiles as model input
conda activate /usr/local/venvs/oppmatch_django
cd /var/www/opportunity_match/web-interface/opportunity_match_site/
python manage.py extract_profiles --output /root/document-embeddings/production/profiles.json

# create the model
conda activate /home/akrause/.conda/envs/oppmatch_model
cd /root/document-embeddings/production/
python train_model.py
today=$(date +'%Y%m%d')
mkdir -p /var/www/opportunity_match/models/$today
mv doc2vec_roag.model* /var/www/opportunity_match/models/$today/
