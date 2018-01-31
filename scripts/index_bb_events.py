

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import requests
import time
from dateutil.parser import parse
import math
import datetime


import re
import nltk
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer


dataset_path = '/Users/evanpease/Development/viroonga/search/dataset/train.csv'
solr_url = 'http://localhost:8983/solr/bb_clicks/update'
commit_url = 'http://localhost:8983/solr/bb_clicks/update?commit=true'
delete_url = 'http://localhost:8983/solr/bb_clicks/update?stream.body=<delete><query>*:*</query></delete>'

chunksize = 10000
batch_count = 0

nltk.download('stopwords')
ps = PorterStemmer()
def clean_query(query):

    query = re.sub('[^a-zA-Z]', ' ', query)
    query = query.lower()
    query = query.split()

    # stem and remove stop words
    query = [word for word in query if not word in set(stopwords.words('english'))]

    #sort the array alphabetically
    #query = sorted(query)

    query = ' '.join(query)

    return query

def convert_date(dt):
    # convert to epoch seconds
    ndt = parse(dt)
    return math.ceil(ndt.timestamp())




# clear index
r = requests.get(delete_url)
r = requests.get(commit_url)

for dataset in pd.read_csv(dataset_path, chunksize=chunksize, iterator=True, skiprows=[0],
                           names=['user', 'sku', 'category', 'query', 'click_time', 'query_time']):

    batch_count = batch_count + 1
    docs = []
    for i, row in dataset.iterrows():
        doc = {}
        doc['type_s'] = 'click'
        doc['user_s'] = row['user']
        doc['sku_s'] = row['sku']
        doc['category_s'] = row['category']
        doc['query_s'] = row['query']
        doc['cleaned_query_s'] = clean_query(row['query'])
        doc['click_time_i'] = convert_date(row['click_time'])
        doc['query_time_dt'] = row['query_time']
        docs.append(doc)

    r = requests.post(solr_url, json=docs)
    print(r.content)

    #commit
    r = requests.get(commit_url)
    print(r.content)
    print("committed batch %d" % (batch_count))

    time.sleep(0.01)