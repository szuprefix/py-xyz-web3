# -*- coding:utf-8 -*- 
# author = 'denishuang'
from __future__ import unicode_literals
from .helper import get_recent_active_wallets, OpenSea
import logging
log = logging.getLogger('django')
def sync_recent_active_wallets_data(recent_days=1):
    qset = get_recent_active_wallets(recent_days=recent_days)
    osea = OpenSea()
    for w in qset:
        print(w)
        try:
            w.sync_ens()
            w.sync_nfts()
            osea.create_browser_task(w.address)
        except:
            import traceback
            log.error('sync_recent_active_wallets_data %s error: %s', w, traceback.format_exc())

def sync_active_wallets_data_per_10minutes():
    sync_recent_active_wallets_data(recent_days=0.007)