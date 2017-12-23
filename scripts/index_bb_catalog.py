import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import requests
import time
from dateutil.parser import parse
import math
import datetime
import glob
import xml.etree.ElementTree

files_path = '/Users/evanpease/Development/viroonga/search/dataset/product_data/products/*.xml'
solr_url = 'http://localhost:8983/solr/bb/update'
commit_url = 'http://localhost:8983/solr/bb/update?commit=true'
delete_url = 'http://localhost:8983/solr/bb/update?stream.body=<delete><query>*:*</query></delete>'


def get_text(e_name, element):
    if element.find(e_name) != None:
        return element.find(e_name).text
    else:
        return ""


# clear first
r = requests.get(delete_url)
r = requests.get(commit_url)

files = glob.glob(files_path)           # create the list of file
for file_name in files:
    e = xml.etree.ElementTree.parse(file_name).getroot()
    docs = []
    for product in e:
        doc = {}
        doc['sku_s'] = get_text('sku', product)
        doc['type_s'] = product.find('type').text
        doc['name_s'] = product.find('name').text
        reg_price = float(product.find('regularPrice').text)
        sale_price = float(product.find('salePrice').text)
        try:
            discount = (reg_price - sale_price) / reg_price
        except:
            print("Unable to calculate discount")
        doc['reg_price_f'] = reg_price
        doc['sale_price_f'] = sale_price
        doc['discount_f'] = discount
        doc['on_sale_s'] = product.find('onSale').text
        doc['short_description_s'] = product.find('shortDescription').text
        doc['class_s'] = product.find('class').text
        doc['class_t'] = product.find('class').text
        doc['bb_item_id_s'] = product.find('bestBuyItemId').text
        doc['model_number_s'] = get_text('modelNumber', product)
        doc['manufacturer_s'] = get_text('manufacturer', product)
        doc['manufacturer_t'] = get_text('manufacturer', product)
        doc['image_s'] = product.find('image').text
        doc['med_image_s'] = product.find('mediumImage').text
        doc['thumb_image_s'] = product.find('thumbnailImage').text
        doc['large_image_s'] = product.find('largeImage').text
        doc['long_description_s'] = get_text('longDescription', product)

        # keywords
        kw = str(doc['manufacturer_s']) + ' ' + str(doc['name_s']) + ' ' + str(doc['model_number_s']) + ' ' +str(doc['short_description_s']) + ' ' + str(doc['class_s'])
        doc['keywords_txt_en'] = kw

        # traverse categories
        catPath = product.find('categoryPath')
        catIds = []
        catNames = []
        for cat in catPath:
            name = cat.find('name').text
            id = cat.find('id').text
            catNames.append(name)
            catIds.append(id)
        catPath = "/".join(catNames)
        doc['cat_path_tree'] = catPath
        doc['cat_id_ss'] = catIds
        docs.append(doc)

    #post the docs from this file
    r = requests.post(solr_url, json=docs)
    print(r.content)
    r = requests.get(commit_url)

