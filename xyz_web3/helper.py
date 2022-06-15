# -*- coding:utf-8 -*- 
# author = 'denishuang'
from __future__ import unicode_literals
from xyz_util.crawlutils import extract_between, retry
from time import sleep
from django.conf import settings
from datetime import datetime

CONF = getattr(settings, 'WEB3', {})


class Web3Api(object):

    def __init__(self, api_key=CONF.get('API_KEY')):
        url = "https://mainnet.infura.io/v3/%s" % api_key
        from web3 import Web3
        from ens import ENS
        self.w3 = Web3(Web3.HTTPProvider(url))
        self.ens = ENS.fromWeb3(self.w3)
        for fn in ['get_transaction', 'get_balance']:
            f = getattr(self.w3.eth, fn)
            setattr(self, fn, f)


class BaseEtherScan(object):

    def __init__(self, address, direction='next', callback=print):
        from xyz_util.crawlutils import Browser
        self.address = address
        self.brower = Browser()
        self.direction = direction
        self.callback = callback
        self.row = None
        self.be_ready()

    def go_page(self, page):
        for a in self.html.select('.page-item a.page-link'):
            h = a.attrs['href']
            if h.startswith('javascript:'):
                s = extract_between(h, 'javascript:', '&p=')
                js = "%s&p=%s')" % (s, page)
                self.brower.driver.execute_script(js)
                return True

    def next_pages(self):
        raise NotImplementedError()

    def get_pages(self):
        raise NotImplementedError()

    def has_more(self):
        no, count = self.get_pages()
        if self.direction == 'next':
            return no < count
        if self.direction == 'previous':
            return no > 1
        return False

    def be_ready(self):
        raise NotImplementedError()

    def extract_row_data(self, r):
        raise NotImplementedError()

    def get_table_rows(self):
        return self.html.select('table tbody tr')

    def crawl(self):
        def one_round():
            self.html = self.brower.get_bs_root()
            for r in self.get_table_rows():
                self.row = r
                d = self.extract_row_data(r)
                self.callback(d)
            if self.has_more():
                self.next_page()
            else:
                return 0

        while True:
            r = retry(one_round)
            if r == 0:
                return


class NFTTradeScan(BaseEtherScan):
    table_id = 'mytable'

    def next_page(self):
        self.brower.element('#%s_%s .page-link' % (self.table_id, self.direction)).click()
        sleep(2)

    def get_pages(self):
        t = self.html.select('#%s_wrapper .pagination span.page-link' % self.table_id)[0].text
        no = int(extract_between(t, 'Page ', ' of'))
        count = int(extract_between(t, ' of ', ' '))
        return (no, count)

    def get_table_rows(self):
        return self.html.select('#%s tbody tr' % self.table_id)

    def has_more(self):
        no, count = self.get_pages()
        if self.direction == 'next':
            return no < count
        if self.direction == 'previous':
            return no > 1
        return False

    def be_ready(self):
        self.brower.get("https://etherscan.io/nfttracker?contractAddress=%s#trade" % self.address)
        self.html = self.brower.get_bs_root()
        if self.direction == 'previous':
            self.brower.element('#mytable_last .page-link').click()

    def extract_row_data(self, r):
        d = {}
        tds = r.select('td')
        # print(tds)
        d['hash'] = tds[1].text
        d['trans_time'] = tds[2].select('span')[0].text
        d['action'] = tds[3].text
        d['buyer'] = tds[4].text
        d['token_id'] = tds[6].text
        d['type'] = tds[7].text
        # d['quantity'] = tds[8].text
        d['price'] = tds[8].text
        d['price_in_dolar'] = float(extract_between(d['price'], '$', ')').replace(',', ''))
        d['nft'] = self.address
        return d


class NFTTransferScan(BaseEtherScan):

    def be_ready(self):
        self.brower.get("https://etherscan.io/token/%s" % self.address)
        self.brower.swith_iframe('tokentxnsiframe')
        sleep(2)
        self.html = self.brower.get_bs_root()
        if self.direction == 'previous':
            self.brower.element('#mytable_last .page-link').click()

    def next_page(self):
        c = 'Previous' if self.direction == 'previous' else 'Next'
        self.brower.element('.page-item .page-link[aria-label="%s"]' % c).click()
        sleep(2)

    def get_pages(self):
        t = self.html.select('.page-item span.page-link.text-nowrap')[0].text
        print(t)
        no = int(extract_between(t, 'Page ', ' of'))
        count = int(extract_between(t, ' of ', ' '))
        return (no, count)

    def extract_row_data(self, r):
        d = {}
        tds = r.select('td')
        d['hash'] = tds[1].text
        d['method'] = tds[2].text
        d['trans_time'] = tds[3].select('span')[0].text
        d['from'] = tds[5].text
        d['to'] = tds[7].text
        d['token_id'] = tds[8].text
        d['nft'] = self.address
        return d


def crawl_nft_transaction(scanner):
    from .stores import TransactionStore
    ts = TransactionStore()
    scanner.callback = lambda r: ts.upsert({'hash': r['hash']}, r)
    scanner.crawl()


def crawl_wallets_twitter(address_list, interval=2):
    from xyz_twitter.helper import TwitterScan
    sc = TwitterScan()
    from .stores import WalletStore
    ws = WalletStore()
    for a in address_list:
        sn = sc.search_screen_name(a)
        if sn:
            ws.upsert({'ens': a}, {'twitter': {'screen_name': sn}})
        print(a, sn)
        sleep(interval)


def crawl_wallets_ens(wallets):
    api = Web3Api()
    for wallet in wallets:
        wa = wallet.address
        n = api.ens.name(wa)
        if n:
            wallet.name = n
            wallet.save()
            print(n, wa)

def sync_transaction(d):
    from .models import Transaction, Wallet
    hash = d['hash']
    t = Transaction.objects.filter(hash=hash).first()
    if t:
        return
    w3 = Web3Api()
    r = w3.get_transaction(hash)
    d['from_addr'], created = Wallet.objects.get_or_create(address=r['from'])
    d['to_addr'], created = Wallet.objects.get_or_create(address=r['to'])
    t = Transaction(**d)
    t.save()
    return t


def sync_wallet_nfts(wallet):
    api=AlchemyApi()
    for nft in api.get_wallet_nfts(wallet.address):
        d = api.extract_nft(nft)
        if d:
            save_wallet_nft(wallet, d)
            print(d)

def save_wallet_nft(wallet, d):
    from .models import Collection, Contract, NFT
    contract, created = Contract.objects.get_or_create(address=d['contract'])
    collection, created = Collection.objects.get_or_create(
        url=d['url'],
        defaults=dict(
            name=d['name'].split(' #')[0],
            description=d['description'][:256],
            contract=contract
        )
    )
    nft, created = NFT.objects.get_or_create(
        collection=collection,
        token_id=d['token_id'],
        defaults=dict(
            preview_url=d['preview_url'],
            name=d['name'],
            attributes=d['attributes'][:256],
            wallet=wallet
        )
    )


class AlchemyApi():

    def extract_nft(self, d):
        meta = d['metadata']
        if 'external_url' not in meta:
            return None
        print(meta['external_url'])
        attributes = '\n'.join(['%s:%s' % (a['trait_type'], a['value']) for a in meta.get('attributes',[])])
        return dict(
            contract=d['contract']['address'],
            preview_url=d['media'][0]['gateway'],
            attributes=attributes,
            name=d['title'],
            description=d['description'],
            url=meta['external_url'],
            token_id=eval(d['id']['tokenId'])
        )

    def get_wallet_nfts(self, wallet):
        import requests
        r = requests.get(
            'https://eth-mainnet.alchemyapi.io/v2/bUBHjykrEz_Qd5HUetHi8rvNW8Ik57Kc/getNFTs/?owner=%s' % wallet)
        return r.json()['ownedNfts']
