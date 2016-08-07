 #!/usr/bin/python
 # -*- coding: utf-8 -*-

import urllib2
import json
import numpy as np
import time

class StrelkaUser(object):
    '''Object for keeping data about Strelka card user'''
    def __init__(self, user_id):
        self.user_id = user_id
        self.strelka_number = None
        self.strelka_last_balance = None
        self.strelka_last_checked = None
        
    @staticmethod
    def get_card_status(card_number, timeout = 10):
        '''Returns dict with info''' 
        url="https://strelkacard.ru/api/cards/status/?cardnum=%011d&cardtypeid=3ae427a1-0f17-4524-acb1-a3f50090a8f3" % card_number
        try:
            headers = { 'User-Agent' : 'Mozilla/5.0 (compatible; YandexBot/3.0; +http://yandex.com/bots)' }
            req = urllib2.Request(url, None, headers)
            q = urllib2.urlopen(req, timeout = timeout)
            data=json.load(q)
        except urllib2.HTTPError as e:
            error_message = e.read()
            print 'ERROR', error_message
        return data
    
    @staticmethod
    def is_valid_number(card_number):
        ''' Verifies if given integer is indeed valid Strelka card number using Luhn algorithm'''
        if type(card_number) not in [int, long]:
            return False
        #prefix: array of digits of card_number
        #checksum: last digit
        prefix = np.array([int(n) for n in str(card_number)[:-1]], dtype=int)
        checksum = int( str(card_number)[-1] )
        if len(prefix) != 9:
            return False
        coefs = np.array([2,1,2,1,2,1,2,1,2])
        dotprod = prefix * coefs
        dotprod[dotprod > 9] = dotprod[dotprod > 9] - 9
        dotprod_sum = sum(dotprod) % 10
        return checksum == (2 - dotprod_sum if 2 - dotprod_sum >= 0 else (12 - dotprod_sum) )
    
    @classmethod
    def get_card_balance(self, card_number):
        '''Return float of card balance'''
        return float(self.get_card_status(card_number)['balance'])/100
    
    def update_number(self, number):
        if self.is_valid_number(number):
            self.strelka_number = number
        else:
            raise ValueError, 'This Strelka card number is not valid. Please check your number'
    
    def has_strelka_number(self):
        return self.strelka_number is not None
    
    def update_balance(self, verbose = False):
        '''Update this card balance, and write it to self.strelka_last_balance. 
        self.strelka_last_checked would save time in the future'''
        self.strelka_last_balance = self.get_card_balance(self.strelka_number)
        self.strelka_last_checked = time.time()
        if verbose:
            print 'Card #%i balance is %.2f'%(self.strelka_number, self.strelka_last_balance)
        
    def get_updated_balance(self):
        assert self.strelka_number is not None 
        self.update_balance()
        return self.strelka_last_balance