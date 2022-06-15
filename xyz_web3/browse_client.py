# -*- coding:utf-8 -*- 
# author = 'denishuang'
from __future__ import print_function, unicode_literals
from time import sleep
from datetime import datetime
import requests, argparse


def get_args():
    parser = argparse.ArgumentParser(description="媒体浏览")
    parser.add_argument('-t', '--token', default='')
    parser.add_argument('-e', '--endpoint')
    return parser.parse_args()


class OpenseaScan(object):
    def __init__(self, callback):
        from xyz_util.crawlutils import Browser
        self.browser = Browser()
        self.callback = callback

    def getCurrentActivity(self):
        url = 'https://opensea.io/activity?search[chains][0]=ETHEREUM&search[eventTypes][0]=AUCTION_SUCCESSFUL'
        b = self.browser
        b.get(url)
        ll = []
        while True:
            tl = []
            for d in self.extractActivity():
                hash = d['hash']
                tl.append(hash)
                if hash not in ll:
                    self.callback(d)
                    print(d)
            ll = tl
            sleep(30)

    def extract_row_data(self, r):
        d = {}
        thref = r.select('.EventTimestamp--link')[0].attrs['href']
        d['hash'] = thref.split('/tx/')[1]
        d['contract'] = r.select('.AssetCell--link')[0].attrs['href'].split('/')[3]
        d['value_in_dolar'] = r.select('.Price--fiat-amount')[0].text.strip()
        d['value_in_dolar'] = float(d['value_in_dolar'].replace(' ', '').replace('$', '').replace(',', ''))
        d['value'] = float(r.select('.Price--amount')[0].text.strip())
        d['update_time'] = datetime.now().isoformat()
        return d

    def extractActivity(self):
        b = self.browser
        te = b.element('[data-testid="ActivityTable"] [role="list"]')
        es = []
        for e in te.find_elements_by_css_selector('[role="listitem"]'):
            try:
                es.append(self.extract_row_data(b.element_to_bs(e)))
            except:
                import traceback
                print('error', e)
                traceback.print_exc()
                sleep(1)
        for be in es:
            yield be


if __name__ == '__main__':
    args = get_args()
    headers = {'Authorization': 'Token %s' % args.token}
    endpoint = args.endpoint
    def callback(d):
        r =requests.post('%sreport/' % endpoint, d, headers=headers)
        print(r.status_code)
        print(r.json())
    sc = OpenseaScan(callback)
    while True:
        try:
            sc.getCurrentActivity()
        except:
            import traceback
            traceback.print_exc()
            sleep(10)
        sleep(1)
