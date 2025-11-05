"""Views for content management."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from .forms import NewsItemForm, NoticeForm
from .models import NewsItem, Notice


class NewsListView(LoginRequiredMixin, ListView):
    template_name = "content/news_list.html"
    model = NewsItem
    paginate_by = 10

    def get_queryset(self):  # type: ignore[override]
        qs = NewsItem.objects.filter(status__in=["published", "scheduled"]).order_by("-publish_at")
        now = timezone.now()
        qs = qs.filter(Q(publish_at__lte=now) | Q(publish_at__isnull=True))
        user_groups = self.request.user.memberships.filter(status="active").values_list("plan__group", flat=True)
        return qs.filter(Q(target_groups__isnull=True) | Q(target_groups__in=user_groups)).distinct()


class NewsDetailView(LoginRequiredMixin, DetailView):
    template_name = "content/news_detail.html"
    model = NewsItem
    context_object_name = "news_item"
    slug_field = "slug"
    slug_url_kwarg = "slug"


class NoticeListView(LoginRequiredMixin, ListView):
    template_name = "content/notice_list.html"
    model = Notice

    def get_queryset(self):  # type: ignore[override]
        now = timezone.now()
        qs = Notice.objects.filter(is_active=True)
        qs = qs.filter(start_at__lte=now)
        qs = qs.filter(Q(end_at__isnull=True) | Q(end_at__gte=now))
        user_groups = self.request.user.memberships.filter(status="active").values_list("plan__group", flat=True)
        return qs.filter(Q(target_groups__isnull=True) | Q(target_groups__in=user_groups)).distinct()


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):  # type: ignore[override]
        return self.request.user.is_staff

    def handle_no_permission(self):  # type: ignore[override]
        messages.error(self.request, "Administrator access required.")
        return super().handle_no_permission()


class NewsItemManageMixin(LoginRequiredMixin, StaffRequiredMixin):
    model = NewsItem
    form_class = NewsItemForm
    success_url = reverse_lazy("content:news_manage")

    def form_valid(self, form):  # type: ignore[override]
        form.instance.created_by = self.request.user
        messages.success(self.request, "News item saved.")
        return super().form_valid(form)


class NewsItemManageListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    template_name = "content/news_manage_list.html"
    model = NewsItem
    paginate_by = 20


class NewsItemCreateView(NewsItemManageMixin, CreateView):
    template_name = "content/news_form.html"


class NewsItemUpdateView(NewsItemManageMixin, UpdateView):
    template_name = "content/news_form.html"


class NoticeManageListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    template_name = "content/notice_manage_list.html"
    model = Notice
    paginate_by = 20


class NoticeManageMixin(LoginRequiredMixin, StaffRequiredMixin):
    model = Notice
    form_class = NoticeForm
    success_url = reverse_lazy("content:notice_manage")

    def form_valid(self, form):  # type: ignore[override]
        form.instance.created_by = self.request.user
        messages.success(self.request, "Notice saved.")
        return super().form_valid(form)


class NoticeCreateView(NoticeManageMixin, CreateView):
    template_name = "content/notice_form.html"


class NoticeUpdateView(NoticeManageMixin, UpdateView):
    template_name = "content/notice_form.html"

