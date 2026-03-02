import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UserProfile(TimeStampedModel):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        USER = "user", "User"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.USER)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"


class TemplateType(TimeStampedModel):
    class Code(models.TextChoices):
        ANALYTICAL = "analytical", "Analytical"
        STABILITY = "stability", "Stability"
        SPECIFICATION = "specification", "Specification"

    code = models.CharField(max_length=32, choices=Code.choices, unique=True)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class WordTemplate(TimeStampedModel):
    name = models.CharField(max_length=255)
    template_type = models.ForeignKey(TemplateType, on_delete=models.PROTECT, related_name="templates")
    file = models.FileField(upload_to="word_templates/")
    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="uploaded_templates")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["template_type", "version"], name="uniq_template_type_version"),
        ]

    def __str__(self):
        return f"{self.name} v{self.version}"


class ExtractionRule(TimeStampedModel):
    class RuleType(models.TextChoices):
        FIELD = "field", "Field"
        TABLE = "table", "Table"

    template_type = models.ForeignKey(TemplateType, on_delete=models.CASCADE, related_name="extraction_rules")
    rule_type = models.CharField(max_length=20, choices=RuleType.choices, default=RuleType.FIELD)
    source_key = models.CharField(max_length=255, help_text="Textract key/label to match")
    target_field = models.CharField(max_length=255, help_text="Placeholder name without angle brackets")
    regex_pattern = models.CharField(max_length=500, blank=True)
    table_index = models.PositiveIntegerField(null=True, blank=True)
    is_enabled = models.BooleanField(default=True)
    priority = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["priority", "id"]
        constraints = [
            models.UniqueConstraint(fields=["template_type", "source_key", "target_field"], name="uniq_rule_target_mapping"),
        ]

    def __str__(self):
        return f"{self.template_type} :: {self.target_field}"


class UploadedDocument(TimeStampedModel):
    class Status(models.TextChoices):
        UPLOADED = "uploaded", "Uploaded"
        PROCESSING = "processing", "Processing"
        EXTRACTED = "extracted", "Extracted"
        VERIFIED = "verified", "Verified"
        GENERATED = "generated", "Generated"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="uploaded_documents")
    template_type = models.ForeignKey(TemplateType, on_delete=models.PROTECT, related_name="uploaded_documents")
    file = models.FileField(upload_to="uploaded_pdfs/")
    original_filename = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UPLOADED)
    upload_time = models.DateTimeField(default=timezone.now)
    processed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.original_filename


class TextractResult(TimeStampedModel):
    document = models.OneToOneField(UploadedDocument, on_delete=models.CASCADE, related_name="textract_result")
    raw_response = models.JSONField()
    confidence_score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)


class ExtractedField(TimeStampedModel):
    document = models.ForeignKey(UploadedDocument, on_delete=models.CASCADE, related_name="extracted_fields")
    extraction_rule = models.ForeignKey(ExtractionRule, on_delete=models.SET_NULL, null=True, blank=True, related_name="extracted_fields")
    field_name = models.CharField(max_length=255)
    extracted_value = models.TextField(blank=True)
    confidence = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    is_table_value = models.BooleanField(default=False)

    class Meta:
        indexes = [models.Index(fields=["document", "field_name"])]


class UserFieldSelection(TimeStampedModel):
    document = models.ForeignKey(UploadedDocument, on_delete=models.CASCADE, related_name="field_selections")
    extracted_field = models.ForeignKey(ExtractedField, on_delete=models.CASCADE, related_name="user_selections")
    selected_value = models.TextField()
    edited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="field_edits")
    is_manual_override = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["document", "extracted_field", "edited_by"], name="uniq_user_selection_per_field"),
        ]


class GeneratedDocument(TimeStampedModel):
    document = models.ForeignKey(UploadedDocument, on_delete=models.CASCADE, related_name="generated_versions")
    template = models.ForeignKey(WordTemplate, on_delete=models.PROTECT, related_name="generated_documents")
    generated_file = models.FileField(upload_to="generated_docs/")
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="generated_documents")
    is_final = models.BooleanField(default=False)


class ProcessingLog(TimeStampedModel):
    document = models.ForeignKey(UploadedDocument, on_delete=models.CASCADE, related_name="processing_logs")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    status_from = models.CharField(max_length=20, blank=True)
    status_to = models.CharField(max_length=20)
    message = models.TextField(blank=True)


class AuditTrail(TimeStampedModel):
    class ActionType(models.TextChoices):
        CREATE = "create", "Create"
        UPDATE = "update", "Update"
        DELETE = "delete", "Delete"
        PROCESS = "process", "Process"
        DOWNLOAD = "download", "Download"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action_type = models.CharField(max_length=20, choices=ActionType.choices)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=64)
    changes = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
