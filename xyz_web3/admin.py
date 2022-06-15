from django.contrib import admin

from . import models

@admin.register(models.Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('address', 'name',  'is_active',  'create_time')
    search_fields = ("name", 'address')
    date_hierarchy = 'create_time'

@admin.register(models.Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('address', 'is_active', 'create_time')
    search_fields = ('address',)
    date_hierarchy = 'create_time'

@admin.register(models.Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ('url', 'name', 'contract', 'is_active', 'create_time')
    search_fields = ("name", "url")
    date_hierarchy = 'create_time'

@admin.register(models.NFT)
class NFTAdmin(admin.ModelAdmin):
    list_display = ('collection', 'token_id', 'wallet', 'is_active', 'create_time')
    date_hierarchy = 'create_time'
