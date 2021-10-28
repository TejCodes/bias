#!/bin/bash

today=$(date +'%Y%m%d')
/var/www/opportunity_match/scripts/build-model.sh
/var/www/opportunity_match/scripts/search-model.sh
/var/www/opportunity_match/scripts/index_roag.sh
#/bin/cp /var/www/opportunity_match/models/$today/doc2vec_* /var/www/opportunity_match/web-interface/opportunity_match_site/models/
#systemctl reload httpd.service
