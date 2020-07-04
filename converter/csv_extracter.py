#-*- coding:utf-8 -*-
import re
import csv

from logging_manager import logging_mgr

def check_line(keys, spline):
    max_in = max(len(keys), len(spline))
    for i in range(max_in):
        k = 'EMPTY'
        s = 'EMPTY'
        if i < len(keys):
            k = keys[i]
        if i < len(spline):
            s = spline[i]
            if s == '':
                s = 'null'

class AmazonProduct:

    attribs = [
        "ean",
        "asin",
        "binding",
        "height",
        "height_units",
        "width",
        "width_units",
        "weight",
        "weight_units",
        "length",
        "length_units",
        "packageQuantity",
        "partNumber",
        "productGroup",
        "publisher",
        "editorialReviews_content",
        "BrowseNodeName",
        "BrowseNodeId",
        "BrowseNodeNameA",
        "BrowseNodeIdA",
        "marque",
        "nom",
        "ref",
        "imagesCSV"
    ]

    cdiscount_attrs = {
        #Cdiscount:Amazoninput
        "Couleur principale": "color",
        "Genre":"genre",
    }

    def __init__(self,
                ean,
                asin,
                binding,
                height,
                height_units,
                width,
                width_units,
                weight,
                weight_units,
                length,
                length_units,
                packageQuantity,
                partNumber,
                productGroup,
                publisher,
                editorialReviews_content,
                BrowseNodeName,
                BrowseNodeId,
                BrowseNodeNameA,
                BrowseNodeIdA,
                marque,
                nom,
                ref,
                imagesCSV
                ):


                self.ean = ean
                self.asin = asin
                self.binding = binding
                self.height = height
                self.height_units = height_units
                self.width = width
                self.width_units = width_units
                self.weight = weight
                self.weight_units = weight_units
                self.length = length
                self.length_units = length_units
                self.packageQuantity = packageQuantity
                self.partNumber = partNumber
                self.productGroup = productGroup
                self.publisher = publisher
                self.editorialReviews_content = editorialReviews_content
                self.BrowseNodeName = BrowseNodeName
                self.BrowseNodeId = BrowseNodeId
                self.BrowseNodeNameA = BrowseNodeNameA
                self.BrowseNodeIdA = BrowseNodeIdA
                self.marque = marque
                self.nom = nom
                self.ref = ref
                self.imagesCSV = imagesCSV

    def convert_attributes(self, product_attributes):
        for attr in product_attributes:
            if attr not in type(self).cdiscount_attrs:
                continue
            cdiscount_attr = cdiscount_attrs[attr]

class AmazonProduct(dict):

    def validate(self):
        assert 'productGroup' in self.keys(), "This item got no product group"

    def convert_attributes(self, products_attrs):
        pass

class AmazonCSV:

    attribs = ["asin","ean","categories","imagesCSV","manufacturer","title","rootCategory","parentAsin","variationCSV","type","upc","mpn","brand","label","department","publisher","productGroup","partNumber","genre","model","color","size","edition","platform","format","packageHeight","packageLength","packageWidth","packageWeight","packageQuantity","isAdultProduct","binding","frequentlyBoughtTogether","features","description","hazardousMaterialType","categoryTreeId","categoryTreeName","datemaj"]

    def __init__(self, filename):

        self.products = []

        with open(filename, newline='', encoding='utf-8') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')

            # Extract information
            ok = problem = 0
            keys = next(spamreader)
            for line in spamreader:
                line = list(line)
                line_args = {att:elem for att, elem in zip(AmazonCSV.attribs, line)}
                try:
                    product = AmazonProduct(**line_args)
                    ok += 1
                    self.products.append(product)

                except Exception as e:
                    logging_mgr.err_msg("Error reading amazon csv: ", str(e))
                    problem += 1


if __name__ == "__main__":
    csv = AmazonCSV('../sample_data/')
