'''
Created on Mar 18, 2016

@author: nicolas
'''

import sys

IS_PYTHON3 = sys.version_info > (3,)

def humanize_duration(duration):
    ret = ""
    
    if duration / 3600 >= 1:
        ret += ("%02dh" if ret else "%dh") % (duration / 3600)
        duration %= 3600
    
    if duration / 60 >= 1:
        ret += ("%02dm" if ret else "%dm") % (duration / 60)
        duration %= 60
    
    if duration >= 1:
        ret += ("%02ds" if ret else "%ds") % duration
    
    if not ret:
        ret = "0s"
    
    return ret
