#!/usr/local/bin/python3
#
# bad_category_handler.py
# AmazonConverter
#
# Created by Eyal Shukrun on 02/14/20.
# Copyright 2020. Eyal Shukrun. All rights reserved.

import setup
import json

BAD_CAT_FILE = setup.cache_bad_categories
MAP_FILE     = setup.categories_map

class BadCategoryHandler:

    def __init__(self, category_name):
        self.category_name = category_name.upper()

    def add_to_file(self):
        if self.category_name in open(BAD_CAT_FILE, 'r', encoding='utf-8').readlines():
            return False

        open(BAD_CAT_FILE, 'a', encoding='utf-8').write(self.category_name.upper()+"\n")

    def check_in_map(self):
        cat_map = json.load(open(MAP_FILE, 'r', encoding='utf-8'))
        if self.category_name in cat_map.keys():
            return cat_map[self.category_name]

        return None

    def run(self):
        mapped = self.check_in_map()
        if not mapped:
            self.add_to_file()
            return False

        return mapped

    @classmethod
    def clean_file(cls):
        cat_map = json.load(open(MAP_FILE, 'r', encoding='utf-8'))
        lines = open(BAD_CAT_FILE, 'r', encoding='utf-8').readlines()
        new   = []
        for name in lines:
            name = name.upper()
            if name in cat_map.keys():
                continue
            new.append(name)

        with open(BAD_CAT_FILE, 'w', encoding='utf-8') as f:
            for name in new:
                f.write(name+'\n')

        return len(lines) - len(new) # Number of cleaned lines

    @classmethod
    def unresolved_categories(cls):
        self.clean_file()
        return open(BAD_CAT_FILE, 'r', encoding='utf-8').readlines()


