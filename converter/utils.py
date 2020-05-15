#!/usr/local/bin/python3
#
# utils.py
# AmazonConverter
#
# Created by Eyal Shukrun on 01/15/20.
# Copyright 2020. Eyal Shukrun. All rights reserved.
#


#!/usr/local/bin/python3
#
# utils.py
# AmazonConverter
#
# Created by Eyal Shukrun on 01/15/20.
# Copyright 2020. Eyal Shukrun. All rights reserved.
#


from IPython import embed
import builtins

def debugme(message="", **additional_vars):
    print("Debugging -",message)
    locals().update(additional_vars)
    print("Debugging mode")
    embed(**locals())

def join_url(root, *subs):
    return root.rstrip('/') + '/' + '/'.join([sub.strip('/') for sub in subs if sub])




