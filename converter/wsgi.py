#!/usr/local/bin/python3
#
# wsgi.py
# AmazonConverter
#
# Created by Eyal Shukrun on 02/03/20.
# Copyright 2020. Eyal Shukrun. All rights reserved.

import flask
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

@app.route('/bad-categories')
def fix_bad_categories():
    cats = bad_cat.BadCategoryHandler.unresolved_categories()

    return flask.render_template('bad_categories.jin', cats=cats)

if __name__ == "__main__":
    app.run(port=5000)


