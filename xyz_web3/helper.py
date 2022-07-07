# -*- coding:utf-8 -*- 
# author = 'denishuang'
from __future__ import unicode_literals

from six import text_type
from xyz_util.crawlutils import extract_between, retry
from xyz_util.datautils import access
from time import sleep
from django.conf import settings
from datetime import datetime, timedelta
import logging, json
import requests

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


def format_token_id(token_id):
    d = token_id
    if isinstance(token_id, text_type):
        if token_id.startswith('0x'):
            d = int(d, 16)
        else:
            d = int(d)
    if d > 1000000000:
        return hex(d)
    return d


def sync_transaction(d):
    from .models import Transaction, Wallet, Contract, Event, NFT
    hash = d['hash']
    t = Transaction.objects.filter(hash=hash).first()
    if t:
        return
    w3 = Web3Api()
    wt = w3.get_transaction(hash)
    d['from_addr'], created = Wallet.objects.get_or_create(address=wt['from'])
    d['contract'], created = Contract.objects.get_or_create(address=wt['to'])
    wallet = d['from_addr']
    eapi = EtherScanApi()
    ers = eapi.get_nft_trans(address=wt['from'], startblock=wt['blockNumber'],
                             endblock=wt['blockNumber'])
    tm = {}
    for i, a in enumerate(ers['result']):
        # print(a['hash'], a['timeStamp'])
        event_time = datetime.fromtimestamp(int(a['timeStamp']))
        ca = a['contractAddress']
        d['contract_nft'], created = Contract.objects.get_or_create(
            address=ca,
            defaults=dict(
                name=a['tokenName']
            ))
        d['to_addr'], created = Wallet.objects.get_or_create(address=a['from'])
        if i == 0:
            trans_time = datetime.fromtimestamp(int(a["timeStamp"]))
            t = Transaction(trans_time=trans_time, **d)
            t.save()
        tm.setdefault(ca, {})[format_token_id(a['tokenID'])] = 1
    alchemy = AlchemyApi()
    rs = alchemy.get_nfts(owner=wt['from'], contractAddresses=','.join(tm.keys()))
    print(tm)
    for r in rs:
        ca = access(r, 'contract.address')
        tid = format_token_id(access(r, 'id.tokenId'))
        if ca not in tm or tid not in tm[ca]:
            continue
        print(r)
        nd = alchemy.extract_nft(r)
        nft = save_wallet_nft(wallet, nd) if nd else None
        event, created = Event.objects.get_or_create(
            transaction=t,
            contract=d['contract_nft'],
            token_id=nft.token_id,
            defaults=dict(
                event_time=event_time,
                nft=nft
            )
        )
    return t


def get_recent_active_wallets(recent_days=1):
    from .models import Wallet
    return Wallet.objects.filter(
        transactions_sent__create_time__gt=datetime.now() + timedelta(days=-recent_days)
    ).distinct()


def sync_wallet_nfts(wallet, **kwargs):
    api = AlchemyApi()
    for nft in api.get_nfts(owner=wallet.address, **kwargs):
        d = api.extract_nft(nft)
        if d:
            try:
                save_wallet_nft(wallet, d)
            except:
                import traceback
                log.error('save_wallet_nft error: %s %s', d, traceback.format_exc())


def save_wallet_nft(wallet, d):
    from .models import Collection, Contract, NFT
    print(d)
    contract, created = Contract.objects.get_or_create(address=d['contract'])
    token_id = format_token_id(d['token_id'])
    collection, created = Collection.objects.get_or_create(
        contract=contract,
        defaults=dict(
            name=d['name'].split(' #')[0],
            preview_url=d['preview_url'],
            description=d['description'][:256],
            url=d['url']
        )
    )
    nft, created = NFT.objects.get_or_create(
        token_id=token_id,
        contract = contract,
        defaults=dict(
            collection=collection,
            preview_url=d['preview_url'],
            name=d['name'],
            attributes=d['attributes'][:256],
            wallet=wallet
        )
    )
    return nft


class EtherScanApi():
    def __init__(self, api_key=CONF.get('ETHERSCAN')):
        self.api_key = api_key

    def call(self, **kwargs):
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

    def get_nft_trans(self, **kwargs):
        return self.call(action='tokennfttx', module='account', **kwargs)

    def get_balance(self, **kwargs):
        return self.call(action='balance', module='account', **kwargs)

    def get_trans(self, **kwargs):
        return self.call(action='txlist', module='account', **kwargs)


class AlchemyApi():

    def __init__(self, api_key=CONF.get('ALCHEMYAPI')):
        self.api_key = api_key
        self.endpoint = 'https://eth-mainnet.alchemyapi.io/v2/%s' % api_key

    def extract_nft(self, d):
        meta = d['metadata']
        # if 'external_url' not in meta:
        #     return None
        if isinstance(meta, text_type):
            meta = json.loads(meta.replace('\n', ''))
        url = meta.get('external_url','')
        print(url)
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
            url=url,
            token_id=format_token_id(d['id']['tokenId'])
        )

    def get(self, url, **kwargs):
        from xyz_util.datautils import dict2str
        ps = dict2str(kwargs, line_spliter='&', key_spliter='=')
        r = requests.get('%s%s?%s' % (self.endpoint, url, ps))
        return r.json()

    def json_rpc(self, method, params):
        if isinstance(params, dict):
            params = [params]
        pd = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "alchemy_%s" % method,
            "params": params
        }
        return requests.post(self.endpoint, json.dumps(pd)).json()

    def get_nfts(self, **kwargs):
        d = kwargs
        while True:
            rs = self.get('/getNFTs/', **d)
            nfts = rs['ownedNfts']
            for nft in nfts:
                yield nft
            pk = rs.get('pageKey')
            if not pk:
                break
            d['pageKey'] = pk

    def get_wallet_nfts(self, wallet):
        return self.get('/getNFTs/?owner=%s' % wallet)['ownedNfts']

    def get_contract_nfts(self, contract):
        return self.get('/getNFTs/?')

    def get_contract_metadata(self, contract):
        return self.get('/getContractMetadata/?contractAddress=%s' % contract)['contractMetadata']

    def get_asset_transfers(self, from_addr, **kwargs):
        pd = {
            "fromAddress": from_addr,
            "fromBlock": '0x0',
            "excludeZeroValue": True
        }
        pd.update(kwargs)
        return self.json_rpc('getAssetTransfers', pd)


class OpenSea(object):

    def __init__(self):
        self.project = self.create_browser_project()

    def create_browser_project(self):
        from xyz_browser.signals import to_create_project
        from .models import Wallet
        return to_create_project.send_robust(
            sender=Wallet,
            name='OpenSea钱包信息',
            script="""
        extract('avatar','[display="inline-flex"] img','src')
        extract('name','div[data-testid="phoenix-header"]')
            """,
        )[0][1]

    def create_browser_task(self, address):
        from xyz_browser.signals import to_create_task
        url = 'https://opensea.io/%s' % address
        to_create_task.send_robust(self, project=self.project, url=url)


def create_opensea_linktree(task):
    from xyz_linktree.signals import to_save_linktree
    addr = task.url.split('/')[-1]
    from .models import Wallet
    w = Wallet.objects.get(address=addr)
    to_save_linktree.send_robust(
        sender=None,
        user=w.user,
        platform='OpenSea',
        url=task.url,
        name=task.data['name'],
        avatar=task.data.get('avatar')
    )
