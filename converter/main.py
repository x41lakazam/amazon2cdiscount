# -*- coding: utf-8 -*-
import os
import json
import time
import re
import datetime
import xmltodict

from utils import debugme
import api_handler as api
import api_models as models
import csv_extracter
import setup
from logging_manager import logging_mgr
import bad_category_handler

# TODO Test unit:
# Cached files can be corrupted


def check_file(filename, ):
    """
        This is checking a cached file for his existence and expiration date
        The first line of the file needs to be in this format: "Expires:%%<epoch>%%"
    """
    # Check if file exist
    if not os.path.exists(filename):
        return False

    # Parse expiration date
    content = json.load(open(filename, 'r', encoding='utf-8' ))
    expires = content['expires']
    if time.time() > expires:
        return False
    return True

def generate_categories_list():
    categories = api.get_categories()
    n = len(categories)
    expires = (datetime.datetime.now()+datetime.timedelta(days=1)).timestamp()
    payload = {
        'expires': expires,
        'data':categories
    }
    json.dump(payload, open(setup.cache_categories_list, 'w', encoding='utf-8'))
    logging_mgr.ok_msg('Stored {} categories into {}'.format(n, setup.cache_categories_list))
    return True

def generate_models_list(category_code):
    """
        Generate the cached list of models
    """
    filename = setup.cache_model_list(category_code)
    models_dic = api.model_by_category(category_code)
    expires = (datetime.datetime.now()+datetime.timedelta(days=1)).timestamp()
    payload = {
        'expires': expires,
        'data': [model.to_json() for model in models_dic]
    }
    json.dump(payload, open(filename, 'w', encoding='utf-8'))
    logging_mgr.ok_msg('Stored {} models of category {} into {}'.format(len(models_dic), category_code, filename))

def get_product_category(product):
    category = product['productGroup']
    return category.upper()


def create_pkg(csv_file):
    # Extract csv
    csv = csv_extracter.AmazonCSV(csv_file)

    # Update categories names in cache
    if not check_file(setup.cache_categories_list):
        logging_mgr.process_msg('Categories cache not found or expired, generating a new one.')
        generate_categories_list()

    #Load categories
    content = json.load(open(setup.cache_categories_list, 'r', encoding='utf-8'))
    [models.Category.from_dict(d) for d in content['data']]

    products_and_categories = []
    for product in csv.products:
        # Get categories
        category_name = get_product_category(product)
        category = models.Category.by_name(category_name)
        if category is None:
            logging_mgr.err_msg("Category {} doesn't exist".format(category_name))
            return False
        product_attributes = api.get_model_attributes(category.code)
        product.convert_attributes(product_attributes)
        if not category:
            mapped = bad_category_handler.BadCategoryHandler(category_name)
            logging_mgr.warning_msg('Category {} is invalid'.format(category_name))
        else:
            products_and_categories.append((product, category))

    if not products_and_categories:
        logging_mgr.err_msg("Products and categories is empty.")
        return False

    pkg = models.ProductPackage(products_and_categories)
    pkg.create()

    return pkg

def api_upload(csv_file):

    pkg = create_pkg(csv_file)
    if not pkg:
        return False
    pkg_id = pkg.submit_package()
    status = pkg.get_submissions_result()

    return {'pkg_id': pkg_id, 'status': status}

def generate_example_csv(src_csv, dst_csv):
    import random
    lines = open(src_csv, 'r', encoding='utf-8' ).readlines()
    while True:
        random_line = random.choice(lines[1:])
        if 'Book' in random_line:
            break
    lines.remove(random_line)
    random_line = random_line.replace('Book', 'Autres Livres')

    open(src_csv, 'w', encoding='utf-8' ).write(''.join(lines))

    header = open(dst_csv, 'r', encoding='utf-8' ).readlines()[0]

    with open(dst_csv, 'w', encoding='utf-8' ) as f:
        f.write(header)
        f.write(random_line)


if __name__ == '__main__':
    csv_path = '../sample_data/example.csv'
    generate_example_csv('../sample_data/split-me.csv', csv_path)
    pkg_infos = api_upload(csv_path)
    if pkg_infos is False:
        print("Problem")
    import ipdb; ipdb.set_trace()
    print(pkg_infos)

    # Get brand list --> returns list of Brands
    # Submit product package --> Receive ProductPackageRequest, returns ProductIntegrationReportMessage
    # GetProductPackageSubmissionResult --> Receive package id , returns ProductIntegrationReportMessage



