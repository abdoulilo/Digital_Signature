from django.contrib import admin
from .models import DigitalDocument


@admin.register(DigitalDocument)
class DigitalDocumentAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'title',
        'status',
        'uploaded_by',
        'created_at',
        'updated_at',
    ]

    search_fields = [
    'title',
    'file_hash',
]

    list_filter = [
        'status',
        'created_at',
    ]

    readonly_fields = [
    'file_hash',
    'signature',
    'public_key',
    'created_at',
    'updated_at',
]