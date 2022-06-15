# -*- coding:utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class Wallet(models.Model):
    class Meta:
        verbose_name_plural = verbose_name = "钱包"
        ordering = ('-create_time',)

    address = models.CharField('地址', max_length=64, unique=True)
    name = models.CharField("名称", max_length=64, blank=True, default='')
    create_time = models.DateTimeField("创建时间", auto_now_add=True)
    is_active = models.BooleanField("有效", blank=False, default=True)

    def __str__(self):
        return self.name or self.address


class Contract(models.Model):
    class Meta:
        verbose_name_plural = verbose_name = "合约"
        ordering = ('-create_time',)

    address = models.CharField('地址', max_length=64, unique=True)
    is_active = models.BooleanField("有效", blank=False, default=True)
    create_time = models.DateTimeField("创建时间", auto_now_add=True)

    def __str__(self):
        return self.name


class Collection(models.Model):
    class Meta:
        verbose_name_plural = verbose_name = "数字藏品集"
        ordering = ('-create_time',)

    url = models.CharField('地址', max_length=128, unique=True)
    name = models.CharField("名称", max_length=64)
    contract = models.ForeignKey(Contract, verbose_name=Contract._meta.verbose_name, null=True, blank=True,
                                 on_delete=models.PROTECT)
    description = models.CharField("描述", max_length=256, blank=True, default='')
    create_time = models.DateTimeField("创建时间", auto_now_add=True)
    is_active = models.BooleanField("有效", blank=False, default=True)

    def __str__(self):
        return self.name or self.url


class NFT(models.Model):
    class Meta:
        verbose_name_plural = verbose_name = "数字藏品"
        ordering = ('-create_time',)
        unique_together = ('collection', 'token_id')

    collection = models.ForeignKey(Collection, verbose_name=Collection._meta.verbose_name, null=True, blank=True,
                                   on_delete=models.PROTECT)
    token_id = models.PositiveIntegerField('编号', default=0)
    name = models.CharField("名称", max_length=64, blank=True, default='')
    attributes = models.CharField('参数', max_length=256, blank=True, default='')
    preview_url = models.URLField('预览地址', max_length=256, blank=True, default='')
    wallet = models.ForeignKey(Wallet, verbose_name=Wallet._meta.verbose_name, null=True, blank=True,
                               on_delete=models.PROTECT)
    create_time = models.DateTimeField("创建时间", auto_now_add=True)
    is_active = models.BooleanField("有效", blank=False, default=True)

    def __str__(self):
        return self.name


class Transaction(models.Model):
    class Meta:
        verbose_name_plural = verbose_name = "事务"
        ordering = ('-create_time',)

    hash = models.CharField('编号', max_length=66, blank=True, unique=True)
    method = models.TextField("方法", max_length=64, blank=False, db_index=True)
    from_addr = models.ForeignKey(Wallet, verbose_name=Wallet._meta.verbose_name, null=True, blank=True,
                            related_name='transactions_started', on_delete=models.PROTECT)
    to_addr = models.ForeignKey(Wallet, verbose_name=Wallet._meta.verbose_name, null=True, blank=True,
                            related_name='transactions_received', on_delete=models.PROTECT)
    value = models.DecimalField("价值", blank=True, default=0, max_digits=20, decimal_places=6)
    value_in_dolar = models.DecimalField("价值(美元)", blank=True, default=0, max_digits=20, decimal_places=2)
    create_time = models.DateTimeField("创建时间", auto_now_add=True)

    def __str__(self):
        return self.hash
