
from flask import render_template, request
from app import app
import requests
import operator


def scale(max, min, value, scale_min=0.1, scale_max=1.0):
    # prevent divide by 0 error
    if max == min:
        return scale_max
    OldRange = (max - min)
    NewRange = (scale_max - scale_min)
    NewValue = (((value - min) * NewRange) / OldRange) + scale_min
    return round(NewValue,3)


def signals_to_dict(docs, group_by):
    bq = {}
    for doc in docs:
        if doc[group_by] in bq:
            # add
            bq[doc[group_by]] = bq[doc[group_by]] + doc['event_count_i']
        else:
            bq[doc[group_by]] = doc['event_count_i']
    sorted_x = sorted(bq.items(), key=operator.itemgetter(1), reverse=True)
    return sorted_x


def signals_dict_to_bq(signals, bq_field, lower_bound, upper_bound):
    bq = ""
    length = len(signals)
    max = signals[0][1]
    min = signals[length-1][1]
    for sig in signals:
        var = sig[1]
        bq += bq_field+":"+sig[0]+"^"+str(scale(max,min, sig[1], lower_bound, upper_bound)) + " "
    return bq


def bq_to_dict(bq_str):
    bq_dict = {}
    for bq in bq_str.split(" "):
        bq_parts = bq.split(":")
        bq_dict[bq_parts[1].split("^")[0]] = float(bq_parts[1].split("^")[1])
    return bq_dict


@app.route('/autocomplete')
def autocomplete():
    #TODO: implement: http://localhost:8983/solr/bb_clicks_aggr/select?q=*:*&defType=edismax&qf=query_txt_en&rows=0&facet=true&facet.field=query_s&facet.mincount=1&facet.limit=10&facet.prefix=apple%20iph
    return "TODO"

@app.route('/')
@app.route('/index')
def index():
    # step 1.
    params = request.args

    q = '*'

    if not request.args.get("q") is None:
        q = params['q']


    cat_aggr_q = 'http://localhost:8983/solr/bb_clicks_aggr/select?q=%s&defType=edismax&qf=query_txt_en&pf=query_txt_en^0.5&mm=67%%25&fq=aggr_type_s:category&rows=50' % (q)
    r = requests.get(cat_aggr_q)

    cat_aggr = r.json()
    cat_signals = signals_to_dict(cat_aggr['response']['docs'], 'category_s')

    cat_bq = signals_dict_to_bq(cat_signals, "cat_id_ss", 0.1, 0.6)

    # item stats query
    #item_aggr_q = 'http://localhost:8983/solr/bb_clicks_aggr/query?q=%s&defType=edismax&qf=query_txt_en&mm=100%%25&fq=aggr_type_s:item&rows=50&json.facet={ stats:{ type : terms, field : sku_s, limit : 50, sort : { x : desc}, facet: { x : "sum(event_count_i)" } }}' % (q)
    item_aggr_q = 'http://localhost:8983/solr/bb_clicks_aggr/select?q=%s&defType=edismax&qf=query_txt_en&pf=query_txt_en^0.5&mm=67%%25&fq=aggr_type_s:item&rows=50' % (q)

    r = requests.get(item_aggr_q)

    item_aggr = r.json()

    # signals to dict
    sku_signals = signals_to_dict(item_aggr['response']['docs'], 'sku_s')

    sku_bq = signals_dict_to_bq(sku_signals, "sku_s", 0.1, 0.5)

    # main solr query
    query = 'http://localhost:8983/solr/bb/select?q=%s&fl=*,score&rows=25&mm=67%%25&defType=edismax&qf=keywords_txt_en&bq=' % (q)

    woc_sku = False
    woc_cat = False

    # Apply wisdom of crowd?
    sku_bq_dict = {} # pass a dict of the boosts to the response for rendering
    cat_bq_dict = {}
    if params.get('woc_sku') == 'true':
        woc_sku = True
        query = query + sku_bq
        if len(sku_bq) > 0:
            sku_bq_dict = bq_to_dict(sku_bq.strip())
    if params.get('woc_cat') == 'true':
        woc_cat = True
        query = query + cat_bq
        if len(cat_bq) > 0:
            cat_bq_dict = bq_to_dict(cat_bq.strip())

    # Apply auto filtering?
    woc_cat_msg = ""
    if params.get('woc_cat') == 'true':
        woc_cat = True
        #d = stats_to_dict(cat_aggr)
        d = cat_signals
        if len(d) > 0:
            d_max = d[0][1]
            d_tot = 0.0
            for sig in d:
                d_tot = d_tot + sig[1]
            print(d_max)
            #d_max = max(d.values())
            #d_tot = sum(d.values())
            d_perc = d_max / d_tot
            if d_max > 100 and d_perc > 0.9:
                cat_id = next(iter(d[0]))
                cat_fq = "&fq=cat_id_ss:%s" % (cat_id)
                query = query + cat_fq
                woc_cat_msg = '%d%% of click-through for "%s" matches category %s ' % ((d_perc * 100), q, cat_id)
            else:
                woc_cat_msg = ""


    add_params = []
    if params.get('add_params'):
        # add to the query
        add_params = params.get('add_params').split("|")

        for p in add_params:
            print("WE ARE HERE and p=%s" % (p))
            query = query + "&" + p


    r = requests.get(query)
    results = r.json()

    # perform main request
    data = {'results': results,
            'q' : request.args.get("q"),
            'main_q' : query,
            'woc_sku': woc_sku,
            'woc_cat': woc_cat,
            'sku_bq_dict': sku_bq_dict,
            'cat_bq_dict': cat_bq_dict,
            'sku_signals': sku_signals,
            'cat_signals': cat_signals,
            'cat_aggr_q': cat_aggr_q,
            'item_aggr_q': item_aggr_q,
            'woc_cat_msg': woc_cat_msg,
            'add_params': add_params
            }
    return render_template('index.html',
                           title='Find 2.0',
                           data=data)

