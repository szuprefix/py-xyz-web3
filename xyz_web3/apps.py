#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author:denishuang

from __future__ import unicode_literals

from django.apps import AppConfig


class Config(AppConfig):
    name = 'xyz_web3'
    label = 'web3'
    verbose_name = 'web3'

    def ready(self):
        super(Config, self).ready()
        # from . import receivers