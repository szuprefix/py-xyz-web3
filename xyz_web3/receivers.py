# -*- coding:utf-8 -*- 
# author = 'denishuang'
from __future__ import unicode_literals

import logging
log = logging.getLogger('django')

def bind_browser_task_events():
    from xyz_browser.signals import task_done
    task_done.connect(to_create_opensea_linktree)

def to_create_opensea_linktree(sender, **kwargs):
    from .helper import create_opensea_linktree
    create_opensea_linktree(kwargs['task'])

try:
    bind_browser_task_events()
except:
    import traceback
    log.error('bind_browser_task_events error:%s', traceback.format_exc())