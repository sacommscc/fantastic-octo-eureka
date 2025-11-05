"""Admin for membership models."""

from __future__ import annotations

from django.contrib import admin

from .models import AccessArea, MembershipGroup, MembershipInvoice, MembershipPlan, MembershipUpgradeRule, UserMembership


class AccessAreaInline(admin.TabularInline):
    model = AccessArea
    extra = 1


class PlanInline(admin.TabularInline):
    model = MembershipPlan
    extra = 1


@admin.register(MembershipGroup)
class MembershipGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "level", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    inlines = [AccessAreaInline, PlanInline]


@admin.register(MembershipPlan)
class MembershipPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "group", "amount", "currency", "interval", "is_active")
    list_filter = ("currency", "interval", "is_active")
    search_fields = ("name", "group__name")
    filter_horizontal = ("allow_upgrade_to",)


@admin.register(MembershipUpgradeRule)
class MembershipUpgradeRuleAdmin(admin.ModelAdmin):
    list_display = ("from_plan", "to_plan", "additional_cost", "prorate_remaining", "is_active")
    list_filter = ("is_active",)
    search_fields = ("from_plan__name", "to_plan__name")


@admin.register(UserMembership)
class UserMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "status", "started_at", "expires_at")
    list_filter = ("status", "plan__group")
    search_fields = ("user__username",)


@admin.register(MembershipInvoice)
class MembershipInvoiceAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "amount", "status", "created_at")
    list_filter = ("status", "currency")
    search_fields = ("user__username", "plan__name")

