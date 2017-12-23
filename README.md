Starting and Stopping Solr:

bin/solr start -c -p 8983 -s example/cloud/node1/solr

bin/solr start -c -p 7574 -s example/cloud/node2/solr -z localhost:9983

bin/solr stop -all
