# -*- coding:utf-8 -*- 
# author = 'denishuang'
from __future__ import unicode_literals

from six import text_type
from xyz_util.crawlutils import extract_between, retry
from time import sleep
from django.conf import settings
from datetime import datetime, timedelta
import logging, json

log = logging.getLogger('django')

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


def sync_transaction(d):
    from .models import Transaction, Wallet, Contract
    hash = d['hash']
    t = Transaction.objects.filter(hash=hash).first()
    if t:
        return
    w3 = Web3Api()
    r = w3.get_transaction(hash)
    d['from_addr'], created = Wallet.objects.get_or_create(address=r['from'])
    d['contract'], created = Contract.objects.get_or_create(address=r['to'])
    eapi = EtherScanApi()
    ers = eapi.call(action='tokennfttx', module='account', address=r['from'], startblock=r['blockNumber'],
                    endblock=r['blockNumber'])
    for a in ers['result']:
        # print(a['hash'], hash)
        if a['hash'] == hash:
            d['contract_nft'], created = Contract.objects.get_or_create(
                address=a['contractAddress'],
                defaults=dict(
                    name=a['tokenName']
                ))
            d['to_addr'], created = Wallet.objects.get_or_create(address=a['from'])
    t = Transaction(**d)
    t.save()
    return t


def get_recent_active_wallets(recent_days=1):
    from .models import Wallet
    return Wallet.objects.filter(
        transactions_sent__create_time__gt=datetime.now() + timedelta(days=-recent_days)
    ).distinct()


def sync_wallet_nfts(wallet):
    api = AlchemyApi()
    for nft in api.get_wallet_nfts(wallet.address):
        d = api.extract_nft(nft)
        if d:
            try:
                save_wallet_nft(wallet, d)
            except:
                import traceback
                log.error('save_wallet_nft error: %s %s', d, traceback.format_exc())


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


class EtherScanApi():
    def __init__(self, api_key=CONF.get('ETHERSCAN')):
        self.api_key = api_key

    def call(self, **kwargs):
        import requests
        from xyz_util.datautils import dict2str
        d = dict(
            module='account',
            action='balance',
            tag='latest',
            apikey=self.api_key
        )
        d.update(kwargs)
        url = "https://api.etherscan.io/api?%s" % dict2str(d, line_spliter='&', key_spliter='=')
        r = requests.get(url)
        if r.status_code != 200:
            raise Exception('http error: %s', r.text)
        return r.json()


class AlchemyApi():

    def extract_nft(self, d):
        meta = d['metadata']
        if 'external_url' not in meta:
            return None
        if isinstance(meta, text_type):
            meta = json.loads(meta.replace('\n', ''))
        print(meta['external_url'])
        attributes = meta.get('attributes', [])
        try:
            if isinstance(attributes, list):
                attributes = '\n'.join(
                    ['%s:%s' % (a['trait_type'], a['value']) for a in attributes if 'trait_type' in a])
            elif isinstance(attributes, dict):
                from xyz_util.datautils import dict2str
                attributes = dict2str(attributes)
        except:
            import traceback
            log.error("extract_nft error: %s\n%s", attributes, traceback.format_exc())
        return dict(
            contract=d['contract']['address'],
            preview_url=d['media'][0]['gateway'],
            attributes=attributes,
            name=d['title'],
            description=d.get('description', ''),
            url=meta['external_url'],
            token_id=eval(d['id']['tokenId'])
        )

    def get_wallet_nfts(self, wallet):
        import requests
        r = requests.get(
            'https://eth-mainnet.alchemyapi.io/v2/bUBHjykrEz_Qd5HUetHi8rvNW8Ik57Kc/getNFTs/?owner=%s' % wallet)
        return r.json()['ownedNfts']
