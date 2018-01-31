
# Pre-requisites

- Python 3.x
- Flask (light-weight python web framework)
- Solr 7.x (I recommend completing the [solr quickstart](http://lucene.apache.org/solr/guide/7_2/solr-tutorial.html) tutorial first)

# Instructions

### 1.) Start Solr

The commands below will start a 2 node Solr cluster. This should look familiar if you completed the quickstart.

```
bin/solr start -c -p 8983 -s example/cloud/node1/solr
bin/solr start -c -p 7574 -s example/cloud/node2/solr -z localhost:9983
```

### 2.) Create Collections

This demo expects 3 collections:

- bb - where the best buy catalog will get indexed
- bb_clicks - where the best buy click event data will get indexed
- bb_clicks_aggr - where the click aggregations will get indexed

I did not script the collection creation step. You can create them manually from the Solr admin or use the Collections API from a script or a tool like Postman.


### 3.) Download the BestBuy Dataset

The best buy dataset is available for free on [Kaggle](https://www.kaggle.com/c/acm-sf-chapter-hackathon-big):

Download and extract all of the files to your machine and remember where they are saved. You will need the locations for the next step.


### 4.) Index the Data

In the scripts directory in this repo, there are 4 scripts to run. Run them in this order:

1. `python index_bb_catalog.py` - The location of the bestbuy catalog files is specified at the top of the file. Change this to the directory where the catalog XML files are located.
2. `python index_bb_events.py` - The location of the traning data (clicks) is specified in the top of the file. Change this to the path where train.csv is located.

### 5.) Run the Aggregations

1.) `python item_aggregations.py` - This will roll up the click counts on weekly windows using the query and product id as the tuple.
2.) `python category_aggregations.py` - Same as above except it uses the query and category ID as the tuple.

## 6.) Run the Demo App

From the root directory of this repo, run `python run.py`.
 
You should see the following output:
```
python run.py 
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: 338-113-189
```

Now you're ready to run some queries! 

- http://127.0.0.1:5000/?q=ipad
- http://127.0.0.1:5000/?q=ipad&add_params=bq=class_s:%22TABLET%22^0.7|fq=class_s:%22TABLET%22 (`&add_param` appends arbitrary parameters that get passed to Solr by the demo app. Use `|` as a separator)



### Stop Solr

The below command will stop any Solr nodes running on your machine.

```
bin/solr stop -all
```