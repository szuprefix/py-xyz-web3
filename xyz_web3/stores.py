# -*- coding:utf-8 -*- 
# author = 'denishuang'
from __future__ import unicode_literals
from xyz_util.mongoutils import Store


class WalletStore(Store):
    name = 'web3_wallet'


class TransactionStore(Store):
    name = 'web3_transaction'


