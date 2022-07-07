# -*- coding:utf-8 -*-
from __future__ import unicode_literals
import json
from django.db import models
from xyz_util.modelutils import JSONField


class Wallet(models.Model):
    class Meta:
        verbose_name_plural = verbose_name = "钱包"
        ordering = ('-create_time',)

    address = models.CharField('地址', max_length=64, unique=True)
    user = models.OneToOneField('auth.user', verbose_name='网站用户', blank=True, null=True,
                                related_name='as_web3_wallet', on_delete=models.PROTECT)
    name = models.CharField("名称", max_length=64, blank=True, default='')
    # balance = models.DecimalField("余额", max_digits=20, decimal_places=6)
    create_time = models.DateTimeField("创建时间", auto_now_add=True)
    # update_time = models.DateTimeField("更新时间", auto_now=True)
    is_active = models.BooleanField("有效", blank=False, default=True)
    is_signed = models.BooleanField("已验", blank=False, default=False)

    def __str__(self):
        return self.name or self.address[:8]

    def sync_ens(self):
        from .helper import Web3Api
        api = Web3Api()
        n = api.ens.name(self.address)
        if n:
            self.name = n
            self.save()
            return n

    def sync_nfts(self):
        from .helper import sync_wallet_nfts
        sync_wallet_nfts(self)

    def save(self, **kwargs):
        if not self.user:
            un = '%s%s@eth' % (self.address[0:6], self.address[-6:])
            from django.contrib.auth.models import User
            self.user, created = User.objects.get_or_create(
                username=un,
                defaults=dict(
                    last_name=self.name
                )
            )
        super(Wallet, self).save(**kwargs)

    @property
    def linktree_links(self):
        from xyz_util.datautils import access
        return access(self, 'user.as_linktree_account.links') or []


class Contract(models.Model):
    class Meta:
        verbose_name_plural = verbose_name = "合约"
        ordering = ('-create_time',)

    address = models.CharField('地址', max_length=64, unique=True)
    name = models.CharField("名称", max_length=64, blank=True, default='')
    abi = JSONField('ABI', blank=True, default={})
    # standard = models.CharField('标准', max_length=16, blank=True, null=True,default='')
    is_active = models.BooleanField("有效", blank=False, default=True)
    create_time = models.DateTimeField("创建时间", auto_now_add=True)

    def __str__(self):
        return self.name or self.address[:8]

    def sync_abi(self):
        from .helper import EtherScanApi
        abi = EtherScanApi().call(address=self.address, action='getabi', module='contract')
        self.abi = json.loads(abi)
        self.save()


class Collection(models.Model):
    class Meta:
        verbose_name_plural = verbose_name = "数字藏品集"
        ordering = ('-create_time',)

    contract = models.OneToOneField(Contract, verbose_name=Contract._meta.verbose_name, null=True, blank=True,
                                 on_delete=models.PROTECT)
    url = models.URLField('地址', max_length=255)
    name = models.CharField("名称", max_length=64)
    preview_url = models.URLField('预览地址', max_length=256, blank=True, default='')
    description = models.CharField("描述", max_length=256, blank=True, default='')
    create_time = models.DateTimeField("创建时间", auto_now_add=True)
    is_active = models.BooleanField("有效", blank=False, default=True)

    def __str__(self):
        return self.name or self.url


class NFT(models.Model):
    class Meta:
        verbose_name_plural = verbose_name = "数字藏品"
        ordering = ('-create_time',)
        # unique_together = ('collection', 'token_id')

    collection = models.ForeignKey(Collection, verbose_name=Collection._meta.verbose_name, null=True, blank=True,
                                   related_name='nfts', on_delete=models.PROTECT)
    contract = models.ForeignKey(Contract, verbose_name=Contract._meta.verbose_name, null=True, blank=True,
                                 related_name='nfts', on_delete=models.PROTECT)
    token_id = models.CharField('编号', max_length=66, blank=True, default='')
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
    method = models.CharField("方法", max_length=64, blank=False, db_index=True)
    from_addr = models.ForeignKey(Wallet, verbose_name='从', null=True, blank=True,
                                  related_name='transactions_sent', on_delete=models.PROTECT)
    to_addr = models.ForeignKey(Wallet, verbose_name='到', null=True, blank=True,
                                related_name='transactions_received', on_delete=models.PROTECT)
    contract = models.ForeignKey(Contract, verbose_name=Contract._meta.verbose_name, null=True, blank=True,
                                 related_name='transactions', on_delete=models.PROTECT)
    contract_nft = models.ForeignKey(Contract, verbose_name='%s(NFT)' % Contract._meta.verbose_name, null=True,
                                     blank=True, related_name='nfttransactions', on_delete=models.PROTECT)
    collection = models.ForeignKey(Collection, verbose_name='NFT集', null=True,
                                     blank=True, related_name='transactions', on_delete=models.PROTECT)
    value = models.DecimalField("价值", blank=True, default=0, max_digits=20, decimal_places=6)
    value_in_dolar = models.DecimalField("价值(美元)", blank=True, default=0, max_digits=20, decimal_places=2)
    trans_time = models.DateTimeField('时间', blank=True, null=True, db_index=True)
    create_time = models.DateTimeField("创建时间", auto_now_add=True)

    def __str__(self):
        return self.hash[:12]


class Event(models.Model):
    class Meta:
        verbose_name_plural = verbose_name = "事件"
        ordering = ('-create_time',)
        unique_together = ('transaction', 'contract', 'token_id')

    transaction = models.ForeignKey(Transaction, verbose_name=Transaction._meta.verbose_name, null=True, blank=True,
                                    related_name='events', on_delete=models.PROTECT)
    contract = models.ForeignKey(Contract, verbose_name=Contract._meta.verbose_name, null=True, blank=True,
                                 related_name='events', on_delete=models.PROTECT)
    nft = models.ForeignKey(NFT, verbose_name=NFT._meta.verbose_name, null=True, blank=True,
                                 related_name='events', on_delete=models.PROTECT)
    token_id = models.CharField('编号', max_length=66, blank=True, default='')
    event_time = models.DateTimeField('时间', blank=True, null=True)
    create_time = models.DateTimeField("创建时间", auto_now_add=True)
