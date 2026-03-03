from django.contrib import admin

from .models import (
    AuditTrail,
    ExtractedField,
    ExtractionRule,
    GeneratedDocument,
    ProcessingLog,
    TemplateType,
    TextractResult,
    UploadedDocument,
    UserFieldSelection,
    UserProfile,
    WordTemplate,
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "created_at")
    search_fields = ("user__username", "user__email")


@admin.register(TemplateType)
class TemplateTypeAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active")


@admin.register(WordTemplate)
class WordTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "template_type", "version", "is_active", "uploaded_by")


@admin.register(ExtractionRule)
class ExtractionRuleAdmin(admin.ModelAdmin):
    list_display = ("template_type", "rule_type", "source_key", "target_field", "is_enabled", "priority")
    list_filter = ("template_type", "rule_type", "is_enabled")


admin.site.register(UploadedDocument)
admin.site.register(TextractResult)
admin.site.register(ExtractedField)
admin.site.register(UserFieldSelection)
admin.site.register(GeneratedDocument)
admin.site.register(ProcessingLog)
admin.site.register(AuditTrail)
