# -*- coding:utf-8 -*- 
# author = 'denishuang'
from __future__ import unicode_literals
from .helper import get_recent_active_wallets
def sync_recent_active_wallets_data():
    for w in get_recent_active_wallets():
        print(w)
        w.sync_ens()
        w.sync_nfts()