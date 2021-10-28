# Django web server

## Requirements

Install requirements:

```
conda create --name oppmatch_django python=3.8
conda activate oppmatch_django
pip install django
pip install django-crispy-forms
pip install django-bootstrap4
pip install elasticsearch
pip install elasticsearch-dsl
pip install gensim
pip install spacy
pip install wordcloud
pip install matplotlib
pip install pandas
```

For spaCy download pretrained statistical models for English:
```
python -m spacy download en_core_web_lg
```

Create the initial database and admin user:
```
cd opportunity_match_site/
python manage.py migrate
python manage.py createsuperuser
python manage.py makemigrations opportunity_match
python manage.py migrate
```

Start the server:
```
python manage.py runserver
```
## Models location

Create a directory `opportunity_match_site/models/` and 
copy the model files `doc2vec_roag.model*` and `doc2vec_search.model*`
into this directory.

## Static files with Apache

Configure Apache to serve static files from a local directory, and set STATIC_ROOT to the
same directory. Then collect all static files from the django apps into this directory:
```
python manage.py collectstatic
```

For ElasticSearch connections on CentOS 8 (Allow HTTPD scripts and modules to connect to the network.) execute the following:

```
setsebool httpd_can_network_connect on
```

# Management commands

## Create search model

Create the search model. This pulls the searches out of the Django database, 
creates the model and writes the model file to the specified output path.

```
python manage.py build_search_model /path/to/doc2vec_search.model
```

If `--private` is specified, the model also uses searches that are not shared (not recommended!).

```
python manage.py build_search_model /path/to/doc2vec_search.model --private
```

## Exporting user profiles

Extract user profiles from the django database and write them in JSON format 
to the file `profiles.json`:
```
python manage.py extract_profiles --output profiles.json
```
This file is used as input when training the document embeddings model.

The profiles must also be inserted into the Elasticsearch database.
This requires a different output format:
```
python manage.py extract_profiles --output profiles.json --elasticsearch
```

## Notifications

Users may subscribe to notifications about opportunities.
If a user appears in searches within the configured time period 
(e.g. 1 week or 1 month) they can be notified by email.
The django admin command `notifications` emails all users for a specific 
time period, one of `day`, `week` and `month`.

To check which users would be notified for a time period run notifications 
with the parameter `--test`, for example to see which users would be notified
about in the last week:

```
python manage.py notifications week --test
```

The following sends out emails with notifications from the last month:
```
python manage.py notifications month
```

Turn on the debug level (0, 1, 2) for the email client with the option
`--debug-level <level>` for example:
```
python manage.py notifications month --debug-level 2
```