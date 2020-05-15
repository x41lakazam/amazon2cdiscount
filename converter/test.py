import api_models
from main import debugme, get_product_category, check_file, generate_categories_list
import os
import json 
import time
import re
import datetime
import xmltodict

import api_handler as api
import api_models as models
import csv_extracter
import setup
from IPython import embed
import credentials

# utils

def get_tests_product(n=1):
    csv_file = '../sample_data/detail_fr.csv'
    csv = csv_extracter.AmazonCSV(csv_file)

    # Update categories names in cache
    if not check_file(setup.cache_categories_list):
        print('[*] Categories cache not found or expired, generating a new one.')
        generate_categories_list()

    content = json.load(open(setup.cache_categories_list, 'r'))
    [models.Category.from_dict(d) for d in content['data']]

    return csv.products[:n]

def test_product_package():

    # Get product
    product = get_tests_product()[0]

    # Get category 
    category_name = get_product_category(product)
    category = models.Category.by_name(category_name)
    if not category:
        logging_mgr.warning_msg('Category {} is invalid'.format(category_name))
        return 1

    # Test function
    pkg = api_models.ProductXML(product, category)
    xml = pkg.render()

    print(xml)
    debugme("test_product_package END", **locals())
    return 0

def test_products_package():
    products_and_categories = []

    # Get products
    products = get_tests_product(10)

    for product in products:
        # Get categories
        category_name = get_product_category(product)
        category = models.Category.by_name(category_name)
        if not category:
            logging_mgr.warning_msg('Category {} is invalid'.format(category_name))
        else:
            products_and_categories.append((product, category))

    # Test function
    pkg = api_models.ProductsXML(products_and_categories)
    xml = pkg.render()

    print(xml)
    debugme("test_product_package END", **locals())

    return 0

def test_build_zip_package():
    products_and_categories = []

    # Get products
    products = get_tests_product(10)

    for product in products:
        # Get categories
        category_name = get_product_category(product)
        category = models.Category.by_name(category_name)
        if not category:
            print('[!] Category {} is invalid'.format(category_name))
        else:
            products_and_categories.append((product, category))

    pkg = api_models.ProductPackage(products_and_categories)
    pkg.create()

def send_test_pkg():
    submit_pkg_action = api.SoapAction.actions['SubmitProductPackage']
    zipfile_url = setup.testpublic_folder_uri
    body = f"""
            <productPackageRequest xmlns:i="http://www.w3.org/2001/XMLSchema-instance">
                <ZipFileFullPath>{zipfile_url}</ZipFileFullPath>
            </productPackageRequest>
    """.strip()
    r = submit_pkg_action(credentials.token, body=body)
    print(r)
    return r

def convert_to_csv():

    products_and_categories = []

    # Get products
    products = get_tests_product(10)

    for product in products:
        # Get categories
        category_name = get_product_category(product)
        category = models.Category.by_name(category_name)
        if not category:
            print('[!] Category {} is invalid'.format(category_name))
        else:
            products_and_categories.append((product, category))

    print(products_and_categories)
    pkg = api_models.ProductPackage(products_and_categories)
    pkg.to_csv()


if __name__ == "__main__":
    #init
    #
    send_test_pkg()






