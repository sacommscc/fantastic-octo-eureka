from __future__ import annotations

from django.urls import path

from . import views

app_name = "content"

urlpatterns = [
    path("news/", views.NewsListView.as_view(), name="news"),
    path("news/manage/", views.NewsItemManageListView.as_view(), name="news_manage"),
    path("news/create/", views.NewsItemCreateView.as_view(), name="news_create"),
    path("news/<slug:slug>/", views.NewsDetailView.as_view(), name="news_detail"),
    path("news/<int:pk>/edit/", views.NewsItemUpdateView.as_view(), name="news_edit"),
    path("notices/", views.NoticeListView.as_view(), name="notices"),
    path("notices/manage/", views.NoticeManageListView.as_view(), name="notice_manage"),
    path("notices/create/", views.NoticeCreateView.as_view(), name="notice_create"),
    path("notices/<int:pk>/edit/", views.NoticeUpdateView.as_view(), name="notice_edit"),
]
