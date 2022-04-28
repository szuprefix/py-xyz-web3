# -*- coding:utf-8 -*- 
# author = 'denishuang'
from __future__ import unicode_literals
from xyz_util.crawlutils import extract_between
from time import sleep


def retry(func, times=3, interval=10):
    try:
        return func()
    except:
        if times > 1:
            sleep(interval)
            print('retrying...')
            return retry(func, times - 1, interval*2)
        import traceback
        traceback.print_exc()
        raise Exception('重试失败')


class BaseEtherScan(object):

    def __init__(self, address, direction='next', callback=print):
        from xyz_util.crawlutils import Browser
        self.address = address
        self.brower = Browser()
        self.direction = direction
        self.callback=callback
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
            return no<count
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
            return no<count
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

# def get_nft_trades(address):
#     from xyz_util.crawlutils import Browser
#     b = Browser()
#     b.get("https://etherscan.io/nfttracker?contractAddress=%s#trade" % address)
#     b.element('#mytable_last .page-link').click()
#     sleep(2)
#
#     def has_more(html):
#         t = html.select('#mytable_wrapper .pagination span.page-link')[0].text
#         print(t)
#         no = int(extract_between(t, 'Page ', ' of'))
#         if no > 1:
#             b.element('#mytable_previous .page-link').click()
#             sleep(2)
#             return True
#
#     while True:
#         html = b.get_bs_root()
#         for r in html.select('#mytable tbody tr'):
#             d = {}
#             tds = r.select('td')
#             d['hash'] = tds[1].text
#             d['trans_time'] = tds[2].select('span')[0].text
#             d['action'] = tds[3].text
#             d['buyer'] = tds[4].text
#             d['token_id'] = tds[6].text
#             d['type'] = tds[7].text
#             d['quantity'] = tds[8].text
#             d['price'] = tds[9].text
#             d['price_in_dolar'] = float(extract_between(d['price'], '$', ')').replace(',', ''))
#             d['nft'] = address
#             yield d
#         if not has_more(html):
#             return

#
# def get_nft_mint(address):
#     from xyz_util.crawlutils import Browser
#     b = Browser()
#     b.get("https://etherscan.io/nfttracker?contractAddress=%s#trade" % address)
#     b.element('#mytable_last .page-link').click()
#     sleep(2)
#
#     def has_more(html):
#         t = html.select('#mytable_mint_wrapper .pagination span.page-link')[0].text
#         print(t)
#         no = int(extract_between(t, 'Page ', ' of'))
#         if no > 1:
#             b.element('#mytable_mint_previous .page-link').click()
#             sleep(2)
#             return True
#
#     while True:
#         html = b.get_bs_root()
#         for r in html.select('#mytable_mint tbody tr'):
#             d = {}
#             tds = r.select('td')
#             d['hash'] = tds[1].text
#             d['trans_time'] = tds[2].select('span')[0].text
#             d['action'] = tds[3].text
#             d['maker'] = tds[4].text
#             d['token_id'] = tds[6].text
#             d['type'] = tds[7].text
#             d['quantity'] = tds[8].text
#             d['price'] = tds[9].text
#             d['price_in_dolar'] = float(extract_between(d['price'], '$', ')').replace(',', ''))
#             d['nft'] = address
#             yield d
#         if not has_more(html):
#             return
#
#
# def get_nft_transaction(address):
#     from xyz_util.crawlutils import Browser
#     b = Browser()
#     b.get("https://etherscan.io/token/%s" % address)
#     b.swith_iframe('tokentxnsiframe')
#     def has_more():
#         t = html.select('.page-item span.page-link.text-nowrap')[0].text
#         print(t)
#         no = int(extract_between(t, 'Page ', ' of'))
#         count = int(extract_between(t,' of ', ' '))
#         if no < count:
#             b.element('.page-item .page-link[aria-label="Next"]').click()
#             sleep(2)
#             return True
#
#     while True:
#         html = b.get_bs_root()
#         for r in html.select('table tbody tr'):
#             d = {}
#             tds = r.select('td')
#             d['hash'] = tds[1].text
#             d['method'] = tds[2].text
#             d['trans_time'] = tds[3].select('span')[0].text
#             d['from'] = tds[5].text
#             d['to'] = tds[7].text
#             d['token_id'] = tds[8].text
#             d['nft'] = address
#             yield d
#         if not has_more():
#             return


def crawl_nft_transaction(scanner):
    from .stores import TransactionStore
    ts = TransactionStore()
    scanner.callback = lambda r: ts.upsert({'hash': r['hash']}, r)
    scanner.crawl()