from django.contrib import admin

from . import models


@admin.register(models.User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('name', 'screen_name', 'description', 'is_active', 'created_at', 'create_time')
    raw_id_fields = ('user',)
    search_fields = ("name", 'screen_name')
    date_hierarchy = 'create_time'

@admin.register(models.Tweet)
class UserAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_text', 'created_at', 'create_time')
    raw_id_fields = ('user',)
    search_fields = ("full_text", )
    date_hierarchy = 'create_time'
