# -*- coding:utf-8 -*-
from __future__ import division

from xyz_restful.mixins import BatchActionMixin
from . import models, serializers
from rest_framework import viewsets
from xyz_restful.decorators import register

@register()
class UserViewSet(BatchActionMixin, viewsets.ModelViewSet):
    queryset = models.User.objects.all()
    serializer_class = serializers.UserSerializer
    search_fields = ('screen_name', 'name')
    filter_fields = {
        'id': ['in', 'exact'],
        'create_time': ['range']
    }
    ordering_fields = ('is_active', 'title', 'create_time', 'created_at')

@register()
class TweetViewSet(BatchActionMixin, viewsets.ModelViewSet):
    queryset = models.Tweet.objects.all()
    serializer_class = serializers.TweetSerializer
    filter_fields = {
        'id': ['in', 'exact'],
        'user': ['in', 'exact'],
        'create_time': ['range']
    }
    ordering_fields = ('create_time', 'created_at')
