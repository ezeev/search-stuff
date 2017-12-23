'''
# Get the max timestamp
SELECT MAX(click_time_i) as max_ts FROM acme_events
'''


'''
ITEM:
SELECT cleaned_query_s, sku_s, type_s, count(*) as event_count, avg(click_time_i) as avg_ts FROM bb_clicks GROUP BY cleaned_query_s, sku_s, type_s HAVING count(*) > 10 ORDER BY count(*) DESC
'''


import requests
import json

max_click_time = 1320083031
min_click_time = 1313056852
seconds_in_day = 604800

dest_url = 'http://localhost:8983/solr/bb_clicks_aggr/update'
delete_url = 'http://localhost:8983/solr/bb_clicks_aggr/update?stream.body=<delete><query>aggr_type_s:item</query></delete>'
commit_url = 'http://localhost:8983/solr/bb_clicks_aggr/update?commit=true'

# clear first
r = requests.get(delete_url)
r = requests.get(commit_url)

cur_click_time = min_click_time #start at min

while cur_click_time <= max_click_time + seconds_in_day:
    #aggr_sql = 'SELECT query_s, sku_s, type_s, count(*) as event_count, avg(CAST( click_time_i AS double )) as avg_ts FROM bb_clicks GROUP BY query_s, sku_s, type_s HAVING count(*) > 10 ORDER BY count(*) DESC LIMIT 1000000'

    upper_click_time = cur_click_time + seconds_in_day
    aggr_sql = 'SELECT query_s, sku_s, type_s, count(*) as event_count, avg(CAST( click_time_i AS double )) as avg_ts FROM bb_clicks WHERE click_time_i BETWEEN %d AND %d GROUP BY query_s, sku_s, type_s HAVING count(*) > 2 ORDER BY count(*) DESC LIMIT 1000000' % (cur_click_time, upper_click_time)

    source_url = 'http://localhost:8983/solr/bb_clicks/sql?stmt=' + aggr_sql



    # streaming request
    print("Executing sql: %s " %(aggr_sql))
    r = requests.get(source_url, stream=True)



    #for line in r.iter_lines():
    #    if line:
    #        decoded_line = line.decode('utf-8')
    data = r.json()

    batch_size = 1000
    doc_count = 0
    new_docs = []
    total_count = 0
    num_results = len(data['result-set']['docs'])
    print("there are %d results" % (num_results))

    for doc in data['result-set']['docs']:
        if 'query_s' in doc:
            new_doc = {}
            new_doc['query_txt_en'] = doc['query_s'].lower()
            new_doc['query_s'] = doc['query_s'].lower()
            new_doc['type_s'] = doc['type_s']
            new_doc['sku_s'] = doc['sku_s']
            new_doc['aggr_type_s'] = "item"
            new_doc['event_count_i'] = doc['event_count']
            new_doc['avg_ts_i'] = doc['avg_ts']
            new_docs.append(new_doc)
            doc_count = doc_count + 1
        if doc_count == batch_size or doc is data['result-set']['docs'][-1]:
            print("batch number ")
            r = requests.post(dest_url, json=new_docs)
            doc_count = 0
            new_docs = []
            print(r.content)
            r = requests.get(commit_url)

    cur_click_time = upper_click_time


# now you can get recommendations!
# SELECT query_txt_en, sku_s, type_s, sum(event_count_i) as event_sum, avg(avg_ts_i) as avg_ts FROM acme_event_aggregations WHERE query_txt_en = 'ipad' GROUP BY query_txt_en, type_s, sku_s ORDER BY event_sum DESC LIMIT 100

# now you can execute queries like this to get boosts:
# http://localhost:8983/solr/acme_event_aggregations/select?defType=edismax&q=lcd%20tv&pf=query_txt_en&qf=query_txt_en&fl=score,*,countBoost:product(0.01,log(event_count_i)),recencyBoost:product(0.01,sqrt(log(avg_ts_i)))&debug=true&rows=100&boost=product(0.01,log(event_count_i))&boost=product(0.01,sqrt(log(avg_ts_i)))

