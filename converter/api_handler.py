import requests
import credentials
import xml.etree.ElementTree as ET
import os
from requests_handler import POST
import re
import xmltodict

import api_models as models
from utils import debugme
from logging_manager import logging_mgr, LoggingManager

API_ENV = "wsvc.cdiscount.com"


class RequestTemplate:
    template ="""
        <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
            <s:Body>
                <{0} xmlns="http://www.cdiscount.com">
                    <headerMessage xmlns:a="http://schemas.datacontract.org/2004/07/Cdiscount.Framework.Core.Communication.Messages" xmlns:i="http://www.w3.org/2001/XMLSchema-instance">
                        <a:Context>
                            <a:CatalogID>1</a:CatalogID>
                            <a:CustomerPoolID>1</a:CustomerPoolID>
                            <a:SiteID>100</a:SiteID>
                        </a:Context>
                        <a:Localization>
                            <a:Country>Fr</a:Country>
                            <a:Currency>Eur</a:Currency>
                            <a:DecimalPosition>2</a:DecimalPosition>
                            <a:Language>Fr</a:Language>
                        </a:Localization>
                        <a:Security>
                            <a:DomainRightsList i:nil="true" />
                            <a:IssuerID i:nil="true" />
                            <a:SessionID i:nil="true" />
                            <a:SubjectLocality i:nil="true" />
                            <a:TokenId>{1}</a:TokenId>
                            <a:UserName i:nil="true" />
                        </a:Security>
                        <a:Version>1.0</a:Version>
                    </headerMessage>
                    {2}
                </{0}>
            </s:Body>
        </s:Envelope>
    """
    # 0 is soap action name
    # 1 is token
    # 2 is message body

    def __init__(self, soap):
        """
        soap is a SoapAction object
        """
        self.soap = soap

    def render(self, token, body=''):
        return RequestTemplate.template.format(self.soap.name, token, body)

class SoapAction:

    actions = {}

    def __init__(self, name, style, endpoint):
        self.name       = name
        self.style      = style
        self.endpoint   = endpoint

        self.template   = RequestTemplate(self)

        SoapAction.actions[name] = self

    def __repr__(self):
        return "<SoapAction {}>".format(self.name)

    def __call__(self, token, body='', save_to=None):
        """
            Call the endpoint and return the result
        """
        endpoint = f"https://{API_ENV}/MarketplaceAPIService.svc"
        headers = {
            'Accept-Encoding': 'gzip,deflate',
            'Content-Type': 'text/xml;charset=UTF-8',
            'SOAPAction': self.endpoint,
        }


        body = self.template.render(token, body)
        logging_mgr.process_msg("[>] Sent XML request {} to {}".format(self.name, endpoint),
                                nostarter=True)
        response = POST(endpoint, data=body, headers=headers, save_to=save_to)
        logging_mgr.process_msg("[<] Received XML response {} from {}".format(self.name, endpoint),
                               nostarter=True)

        return SoapResponse(response, save_to=self.name)

    @classmethod
    def from_xml_elem(cls, name, elem):
        return cls(name=name, style=elem.attrib['style'], endpoint=elem.attrib['soapAction'])

    @classmethod
    def download_from_wsdl(cls):
        wsdl_file = os.path.abspath('cache/wsdl.xml')
        nsmap = {
            'wsdl':'http://schemas.xmlsoap.org/wsdl/',
            'soap':'http://schemas.xmlsoap.org/wsdl/soap/',
        }

        if not os.path.exists(wsdl_file):
            wsdl = f"https://{API_ENV}/MarketplaceAPIService.svc?wsdl"
            r = requests.get(wsdl)
            open('cache/wsdl.xml', 'w', encoding='utf-8').write(r.text)

        tree = ET.parse(wsdl_file)
        root = tree.getroot()
        binding = root.find('wsdl:binding', namespaces=nsmap)

        for elem in binding.iterfind('wsdl:operation', namespaces=nsmap):
            name = elem.attrib['name']
            op = elem.find('soap:operation', namespaces=nsmap)
            sa = SoapAction.from_xml_elem(name, op)


        return cls.actions

# Automatical run of actions retrieve
SoapAction.download_from_wsdl()

class SoapResponse:

    def __init__(self, response, save_to=None):
        self.xmls = response.text # xml as string
        if save_to:
            open(save_to, 'w', encoding='utf-8').write(self.xmls)
            logging_mgr.ok_msg("Saved xml response to", save_to)

        self.root = ET.fromstring(self.xmls)
        self.body = self.root[0]

        try:
            # Handle fault
            self.success   = self.body[0][0][1].text
            assert self.success == "true"
        except IndexError:
            logging_mgr.err_msg("Unexpected XML response:", self.body)
            raise IndexError
        except AssertionError:
            error_msg = self.body[0][0][0].text
            logging_mgr.err_msg("Error on SoapResponse: {}".format(error_msg))
            raise AssertionError

        self.xmldict = xmltodict.parse(self.xmls)
        self.enveloppe = self.xmldict['s:Envelope']
        self.body      = self.enveloppe['s:Body']
        self.sa_response = self.body[list(self.body.keys())[0]]
        self.sa_result = self.sa_response[list(self.sa_response.keys())[1]]

        # Parse soap action name
        prefix = list(self.sa_response.keys())[1]
        self.soapaction_name = prefix[:-6]

def get_categories():
    ### TEST PART ###
    ###
    get_allowed_category_tree = SoapAction.actions['GetAllowedCategoryTree']
    r = get_allowed_category_tree(credentials.token,
                                  save_to='../sample_data/cdiscount_outs/getallowedcategorytree_out.txt')
    ### DELETE BELOW
    #r  = SoapResponse(Fake('../sample_data/cdiscount_outs/getallowedcategorytree_out.txt'))
    ###

    if not r.success:
        return

    # Parse categories
    cat_tree = r.sa_result['CategoryTree']
    models.CategoryTree.parse_categories(cat_tree)
    models.Category.remove_duplicates()
    return [obj.to_json() for obj in models.Category.objects]

def model_by_category(cat_code):
    get_model_list = SoapAction.actions['GetModelList']

    body = """
    <modelFilter xmlns:i="http://www.w3.org/2001/XMLSchema-instance">
        <CategoryCodeList xmlns:a="http://schemas.microsoft.com/2003/10/Serialization/Arrays">
            <a:string>{}</a:string>
        </CategoryCodeList>
    </modelFilter>
    """.format(cat_code)

    # Body built from https://dev.cdiscount.com/marketplace/?page_id=230 example

    ### UNCOMMENT TEST
    r = get_model_list(credentials.token, body=body,
                 save_to="../sample_data/cdiscount_outs/getmodellist_out.txt")
    ### DELETE BELOW
    #r  = SoapResponse(Fake('../sample_data/cdiscount_outs/getmodellist_out.txt'))
    ###

    products = []

    # Get the response part
    model_list = r.sa_result.get('ModelList')

    # Check if it's empty
    if not model_list:
        logging_mgr.warning_msg('No models found for category code <{}>'.format(cat_code))
        return products

    # Retrieve the list of products
    product_models = model_list['ProductModel']

    if type(product_models) is not list:
        product_model = models.ProductModel.from_dict(product_models)
        products.append(product_model)
    else:
        for product_model in product_products:
            product_model = products.ProductModel.from_dict(product_model)
            products.append(product_model)

    if not r.success:
        return

    return products

# below is obsolete
def submit_product_package(product_pkg):
    """
        Use it to submit this package to cdiscount, using SubmitProductPackage
        :product_pkg: Object of type api_models.ProductPackage
    """
    submit_pkg_action = SoapAction.actions['SubmitProductPackage']
    r = submit_pkg_action(credentials.token, body=product_pkg.soap_request_body())

    return r

# DELETE ME
class Fake:
    def __init__(self, filename):
        self.text = open(filename, 'r', encoding='utf-8').read()
        self.success = True

if __name__ == "__main__":
    pass
