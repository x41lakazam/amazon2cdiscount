-*- coding:utf-8 -*-
import os
import json

# Resources
resources_dir = "resources/"
categories_map = os.path.join(resources_dir, "categories_map.json")

# Cache
cache_categories_list = "cache/categories.json"
cache_category_models = "cache/category_models/"
cache_bad_categories  = "cache/bad_categories"
cache_brands_list = "cache/brands.json"
cache_images_dir = "cache/imgs/"

# Temporary files
tmp_upload_dir = "tmp/uploads"
tmp_upload_csv = tmp_upload_dir+"/csv"

# Verbose of the logging manager
verbose_lvl        = 5

site_url           = "https://database.ubital.com"
basedir_url        = site_url + "/database2cdiscount/converter/"
results_path       = "results"
results_url        = basedir_url + results_path
cache_images_dir_url = basedir_url + cache_images_dir

public_folder_path = "/home/eyal/documents/work/freelance/conversion_amazon_to_cdiscount/AmazonConverter/results"
public_folder_uri  = ""

# DELETE below
testpublic_folder_uri  = results_url


requests_history_file = "cache/request.hist"

# init empty dirs
for directory in ('tmp', 'cache', results_path, cache_category_models, cache_images_dir, tmp_upload_dir,
                  resources_dir, ):
    if not os.path.exists(directory):
        os.mkdir(directory)

# init empty files
for filename in [requests_history_file,cache_bad_categories ]:
    if not os.path.exists(filename):
        open(filename, 'w', encoding='utf-8').close()

# init jsons
for jsonfile in [categories_map]:
    if not os.path.exists(jsonfile):
        open(jsonfile, 'w', encoding='utf-8').write("{}")

cache_model_list = lambda code: os.path.join(cache_category_models, str(code)+'.json')


