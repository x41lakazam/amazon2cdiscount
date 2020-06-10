import setup
import datetime
import requests
from logging_manager import LoggingManager

requests_logging = LoggingManager(to_file="logs/requests.log")

def textify_response(resp, info_line=""):
    return """
<-<
{}
{}

Headers:
{}
>->

<-<
{}
>->
-=-=-=-=
""".format(
                    info_line,
                    resp.status_code,
                    '\n'.join(['{}:{}'.format(h,v) for h,v in resp.headers.items()]),
                    resp.text
                )

def textify_request(req, info_line=""):
    return """
<-<
{}
{} {}

Headers:
{}

>->
<-<
{}
>->
-=-=-=-=
""".format(
                    info_line,
                    req.method,
                    req.url,
                    '\n'.join(['{}:{}'.format(h,v) for h,v in req.headers.items()]),
                    req.data
                )

def POST(endpoint, data, headers, save_to=None):
    req = requests.Request('POST', endpoint, data=data, headers=headers)
    txt_request = textify_request(req)
    requests_logging.log_msg("REQUEST TO {}".format(endpoint), txt_request)

    r = requests.post(endpoint, data=data, headers=headers)
    txt_response = textify_response(r)
    requests_logging.log_msg("RESPONSE FROM {}".format(endpoint), txt_response)

    if save_to:
        open(save_to, 'w', encoding='utf-8').write(r.text)
    return r

