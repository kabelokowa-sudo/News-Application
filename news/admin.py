from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, Publisher, Article, Newsletter


class CustomUserAdmin(UserAdmin):
    """
    Extends Django's built-in UserAdmin so the 'role' field and
    subscription fields are visible and editable from the admin site.
    """
    fieldsets = UserAdmin.fieldsets + (
        ('Role & subscriptions', {
            'fields': ('role', 'subscriptions_to_publishers', 'subscriptions_to_journalists'),
        }),
    )
    list_display = ('username', 'email', 'role', 'is_staff')


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Publisher)
admin.site.register(Article)
admin.site.register(Newsletter)