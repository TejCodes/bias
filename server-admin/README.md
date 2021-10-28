# Update the models

Login to the server as root.

The web server and admin scripts are located in `/var/www/opportunity_match/`.

Scripts that train the document model, the search model and 
update the Elasticsearch index:

```
/var/www/opportunity_match/scripts/build-model.sh
/var/www/opportunity_match/scripts/search-model.sh
/var/www/opportunity_match/scripts/index_roag.sh
```

Copy the models from the output directory to the website:

```
cp /var/www/opportunity_match/models/$today/doc2vec_* /var/www/opportunity_match/web-interface/opportunity_match_site/models/
```

Then reload the Apache webserver to pick up the new models.
```
systemctl reload httpd.service
```

A cronjob runs `build-model.sh` every night.
The scripts `notifications-*.sh` generate the notification emails every
day, at the start of the week or the start of the month, depending on the
preferences of the user.

```
SHELL=/bin/bash
BASH_ENV=~/.bashrc

0 9 * * MON /var/www/opportunity_match/scripts/notifications-week.sh
0 9 1 * * /var/www/opportunity_match/scripts/notifications-month.sh
0 9 * * 1,2,3,4,5 /var/www/opportunity_match/scripts/notifications-day.sh
0 0 * * * /var/www/opportunity_match/scripts/build-model.sh > /var/www/opportunity_match/logs/model.log 2>&1
```