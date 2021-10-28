# Preparing data

## Requirements

Prepare a virtual Python environment and install the required packages.
```
pip install -r requirements.txt
python -m spacy download en_core_web_lg
```

## Document embedding models

The document embeddings are trained with the Python package `gensim`.
The input data for training the model is extracted directly from ROAG.

For the connection to ROAG prepare the configuration file:
copy [env.template](production/env.template) to `.env` 
and fill in username and password for the connection to ROAG.

## Creating and Loading data into ES

We have the option to train our model using data stored ES instead of ROAG.

In order to store data in ES, we have an script that creates the 
necessary indices and loads the json data (expertise.json and experts.json files) into ES. 

More specifically, it creates two indices: `expertise` with the data from PURE research outputs and
GTR projects, and `experts` indexing UoE researchers from PURE.

```
python create_load_indexes.py 
Deleting-Creating-Loading Expertise to ES

RESPONSE: (161499, [])
Deleting-Creating-Loading Experts to ES

RESPONSE: (14430, [])

```
(Ignore the warning that you might get about _types. This scripts runs for a ~1min.)

To check if the data has been uploaded correctly, type:

```
 curl 'localhost:9200/_cat/indices?v'
```


## Train the model

Here we have two options available:

1) To train the model connecting with ROAG - using gensim run:
  ```
  python train_model.py
  ```

2) To train the model with the data previously loaded in ES - using gensim run:
  ```
  python train_model_es.py
  ```

This might take about 2 hours.
It will write the model to a set of files `doc2vec_roag.model*`.
Depending on the model size this might be one or more files, for example:
```
doc2vec_roag.model
doc2vec_roag.model.docvecs.vectors_docs.npy
doc2vec_roag.model.trainables.syn1neg.npy
doc2vec_roag.model.wv.vectors.npy
```

To use the new model in the website, copy these model files to
`web-interface/opportunity_match_site/models` and restart the web server.

To add profile data to the model, export profiles from the website database
(see below) and store them in a local file `profiles.json`. 
This file will be read when the model is built.

## Testing the models and ES

Once you have generated the doc2vec_roag.model using the "method 2" described in the
previous section (train_model_es.py), you can test it using the following command:

```
python test_load_search_model_es.py

```

This script loads the doc2vec_roag.model model, and uses it to search the 10 most
similar documents of a given text. For retrieving the details of those documents, we
use again ES. Furthermore, we also included a test for searching similar documents using
[elastic search more like this query](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-mlt-query.html) instead of the doc2vec gensim model generated before.

## ROAG data

**Ignore this secction if you do not have access to ROAG**

The website uses documents indexed and stored in Elasticsearch.
To index the ROAG data in Elasticsearch run the following:
```
python index_roag.py
```
This drops existing indices and extracts data from ROAG to index in Elasticsearch.
It creates two indices: `expertise` with the data from PURE research outputs and
GTR projects, and `experts` indexing UoE researchers from PURE.
This data is essential input for website and must be provided.

## User Profiles (Research Interests)

User profiles are stored in the django web-interface database. 
See below how to export this data to a JSON formatted file `profiles.json`.
The following command inserts the profiles from this input file into the 
Elasticsearch expertise index:
```
python index_profiles.py
```
This deletes all user profiles from the expertise index and inserts the all
profiles from the input file.

# Django data

All the following commands must be run from the django web-interface 
environment.

## Exporting user profiles

Extract user profiles from the django database and write them in JSON format 
to the file `profiles.json`:
```
python manage.py extract_profiles --output profiles.json
```
This file is used as input for training the model.

The profiles must also be inserted into the Elasticsearch database.
This requires a different output format:
```
python manage.py extract_profiles --output profiles.json --elasticsearch
```

## Searches and user profiles

The search model is trained on data extracted from the website database:
```
python manage.py build_search_model doc2vec_search.model
```
This trains the model on all **shared** (i.e. public) searches and writes
the resulting model to output file(s) named `doc2vec_search.model*`.
Private searches can be included by specifying the flag `--private`.

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
