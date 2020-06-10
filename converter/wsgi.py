#!/usr/local/bin/python3
#
# wsgi.py
# AmazonConverter
#
# Created by Eyal Shukrun on 02/03/20.
# Copyright 2020. Eyal Shukrun. All rights reserved.

import flask
import xml.dom.minidom
import flask_wtf as wtf
import wtforms
from werkzeug import secure_filename
import os

import setup
import main
import bad_category_handler as bad_cat

app = flask.Flask("AmazonConverter")

app.config['SECRET_KEY'] = 'qweurhqiwuehrfqiwjdbnascjdhbcvj3u4y59182734nb128c7x3yz481273'

def valid_fn(filename):
    if not os.path.splitext(filename)[1] == '.csv':
        return False
    return True

@app.route("/")
def index():
    return flask.render_template("index.jin")

@app.route("/upload-csv", methods=("GET", "POST"))
def upload_csv():
    if flask.request.method == 'POST':
        f = flask.request.files['csv-file']
        if not valid_fn(f.filename):
            flask.flash("Bad file input")
        else:
            f.save(secure_filename(setup.tmp_upload_csv))
            main.api_upload(setup.tmp_upload_csv)
            os.remove(setup.tmp_upload_csv)
            flask.flash("File uploaded successfully")


    return flask.redirect(flask.url_for('index'))

@app.route('/requests-log')
def requests_log():
    logs_fn = "logs/requests.log"

    file_content = open(logs_fn, 'r').readlines()

    requests = []

    open_flag = 0
    head = body = ""
    for line in file_content:


        if line.startswith('<-<'):
            open_flag += 1
        elif line.startswith('>->'):
            open_flag += 1
        else:

            if open_flag == 1:
                head += line
            elif open_flag == 3:
                body += line[:1000] + "\n"


        if line.strip() == '-=-=-=-=':
            # Prettify body

            requests.append({'head':head, 'body':body})
            open_flag = 0
            head = body = ""


    return flask.render_template("request_log.jin", requests=requests)


@app.route('/bad-categories')
def fix_bad_categories():
    cats = bad_cat.BadCategoryHandler.unresolved_categories()

    return flask.render_template('bad_categories.jin', cats=cats)

if __name__ == "__main__":
    app.run(port=5000)

