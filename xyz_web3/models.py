# -*- coding:utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from xyz_util import modelutils
from . import choices
#
#
# class Wallet(models.Model):
#     class Meta:
#         verbose_name_plural = verbose_name = "钱包"
#         ordering = ('-create_time',)
#
#     address = models.CharField('编号', max_length=64, unique=True)
#     name = models.CharField("名称", max_length=64, blank=True, default='')
#     create_time = models.DateTimeField("创建时间", auto_now_add=True)
#     is_active = models.BooleanField("有效", blank=False, default=True)
#
#     def __str__(self):
#         return self.name or self.address
#
# class NFT(models.Model):
#     class Meta:
#         verbose_name_plural = verbose_name = "钱包"
#         ordering = ('-create_time',)
#
#     address = models.CharField('编号', max_length=64, unique=True)
#     name = models.CharField("名称", max_length=64, blank=False)
#     create_time = models.DateTimeField("创建时间", auto_now_add=True)
#     is_active = models.BooleanField("有效", blank=False, default=True)
#
#     def __str__(self):
#         return self.name or self.address
#
#
# class Trasaction(models.Model):
#     class Meta:
#         verbose_name_plural = verbose_name = "事务"
#         ordering = ('-create_time',)
#
#     hash = models.CharField('编号', max_length=64, blank=True, unique=True)
#     method = models.TextField("文法", max_length=64, blank=False, db_index=True)
#     from_addr = models.DateTimeField("从", blank=True, null=True)
#     to_addr = models.DateTimeField("到", blank=True, null=True)
#     create_time = models.DateTimeField("创建时间", auto_now_add=True)
#
#     def __str__(self):
#         return self.full_text
