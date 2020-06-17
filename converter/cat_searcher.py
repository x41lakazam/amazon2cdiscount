-*- coding:utf-8 -*-
#!/usr/local/bin/python3
#
# cat_searcher.py
# conversion_amazon_to_cdiscount
#
# Created by Eyal Shukrun on 02/14/20.
# Copyright 2020. Eyal Shukrun. All rights reserved.
#
import json
import csv_extracter

cat_file = "cache/categories.json"
csv_file      = "../sample_data/split-me.csv"

csv = csv_extracter.AmazonCSV(csv_file)
csv_cat = [p['productGroup'] for p in csv.products]

categories = [dic['Name'] for dic in json.load(open(cat_file, 'r'))['data']]
for cat in categories:
    if cat in csv_cat:
        print("Cat valid:",cat)

