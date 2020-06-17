#-*- coding:utf-8 -*-
import requests
from requests.auth import HTTPBasicAuth
import xmltodict
from logging_manager import logging_mgr


username="reuven-api"
password="reuven_2655"

def get_token(username, password):
    """
    Use basic auth to retrieve api token
    """
    logging_mgr.ok_msg("Retrieving token")

    auth = HTTPBasicAuth(username, password)
    url = "https://sts.cdiscount.com/users/httpIssue.svc/?realm=https://wsvc.cdiscount.com/MarketplaceAPIService.svc"
    response = requests.get(url, auth=auth)
    responsedict = xmltodict.parse(response.text)
    token = responsedict['string']['#text']

    logging_mgr.ok_msg("Got token:", token)
    return token

token = get_token(username, password)

filestack_api_key = "Amt2n2VehRWmnQDH3q0Blz"
