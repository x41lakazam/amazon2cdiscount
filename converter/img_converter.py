#!/usr/local/bin/python3
#
# img_converter.py
# AmazonConverter
#
# Created by Eyal Shukrun on 01/30/20.
# Copyright 2020. Eyal Shukrun. All rights reserved.
#
import requests
import shutil
import os

def download_img(url, filepath):

    response = requests.get(url, stream=True)
    with open(filepath, 'wb') as out_file:
        shutil.copyfileobj(response.raw, out_file)
    del response

    return filepath


def jpg_to_jpeg(jpg_file):
    basename = os.path.splitext(jpg_file)[0]
    new = basename + '.jpeg'
    os.rename(jpg_file, new)
    return new




