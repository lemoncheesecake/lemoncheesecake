'''
Created on Mar 18, 2016

@author: nicolas
'''

class LemonCheesecakeException(Exception):
    message_prefix = None
    
    def __str__(self):
        s = Exception.__str__(self)
        if self.message_prefix:
            s = "%s: %s" % (self.message_prefix, s)
        return s

class LemonCheesecakeInternalError(Exception):
    def __str__(self):
        return "Internal error: %s" % Exception.__str__(self)