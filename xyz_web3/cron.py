# -*- coding:utf-8 -*- 
# author = 'denishuang'
from __future__ import unicode_literals
from .helper import get_recent_active_wallets
import logging
log = logging.getLogger('django')
def sync_recent_active_wallets_data():
    for w in get_recent_active_wallets():
        print(w)
        try:
            w.sync_ens()
            w.sync_nfts()
        except:
            import traceback
            log.error('sync_recent_active_wallets_data %s error: %s', w, traceback.format_exc())