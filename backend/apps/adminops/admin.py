# adminops/admin.py
import csv

from django.contrib import admin
from django.http import HttpResponse

from apps.adminops.models import AdminAuditLog, DomainEventLog


@admin.register(DomainEventLog)
class DomainEventLogAdmin(admin.ModelAdmin):
    list_display = [
        "event_type",
        "room_id",
        "match_id",
        "participant_id",
        "occurred_at",
    ]
    list_filter = ["event_type"]
    search_fields = ["event_type", "room_id", "match_id", "participant_id"]
    ordering = ["-occurred_at"]
    readonly_fields = [f.name for f in DomainEventLog._meta.get_fields()]
    actions = ["export_to_csv"]

    @admin.action(description="Export selected events to CSV")
    def export_to_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="events.csv"'
        writer = csv.writer(response)
        writer.writerow(["event_type", "room_id", ...])  # Headers
        for obj in queryset:
            writer.writerow([obj.event_type, obj.room_id, ...])
        return response


@admin.register(AdminAuditLog)
class AdminAuditLogAdmin(admin.ModelAdmin):
    list_display = ["action_type", "target_type", "target_id", "occurred_at"]
    ordering = ["-occurred_at"]
    readonly_fields = [f.name for f in AdminAuditLog._meta.get_fields()]
