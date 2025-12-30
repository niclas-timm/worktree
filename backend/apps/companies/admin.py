from django.contrib import admin

from .models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "admin", "created_at")
    search_fields = ("name", "admin__email", "admin__name")
    filter_horizontal = ("members",)
    readonly_fields = ("created_at", "updated_at")
