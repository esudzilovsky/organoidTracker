# -*- coding: utf-8 -*-
"""
Created on Wed Oct 17 11:07:12 2018

@author: Ed
"""
from __future__ import print_function

import json
try:
    from bson import json_util
except Exception:
    import json_util

with open('E:/20180122_MIS_SOK/shapes[xy=122].json', 'r') as f:
    data = json.load(f, object_hook=json_util.object_hook)
    
print(data['saving date & time'])