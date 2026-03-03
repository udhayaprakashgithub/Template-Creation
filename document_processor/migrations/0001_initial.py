# Generated manually for initial project bootstrap
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="TemplateType",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "code",
                    models.CharField(
                        choices=[
                            ("analytical", "Analytical"),
                            ("stability", "Stability"),
                            ("specification", "Specification"),
                        ],
                        max_length=32,
                        unique=True,
                    ),
                ),
                ("name", models.CharField(max_length=100, unique=True)),
                ("description", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="AuditTrail",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "action_type",
                    models.CharField(
                        choices=[
                            ("create", "Create"),
                            ("update", "Update"),
                            ("delete", "Delete"),
                            ("process", "Process"),
                            ("download", "Download"),
                        ],
                        max_length=20,
                    ),
                ),
                ("model_name", models.CharField(max_length=100)),
                ("object_id", models.CharField(max_length=64)),
                ("changes", models.JSONField(blank=True, default=dict)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                (
                    "user",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="UserProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("role", models.CharField(choices=[("admin", "Admin"), ("user", "User")], default="user", max_length=20)),
                (
                    "user",
                    models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="profile", to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="WordTemplate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=255)),
                ("file", models.FileField(upload_to="word_templates/")),
                ("version", models.PositiveIntegerField(default=1)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "template_type",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="templates", to="document_processor.templatetype"),
                ),
                (
                    "uploaded_by",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="uploaded_templates", to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="ExtractionRule",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("rule_type", models.CharField(choices=[("field", "Field"), ("table", "Table")], default="field", max_length=20)),
                ("source_key", models.CharField(help_text="Textract key/label to match", max_length=255)),
                (
                    "target_field",
                    models.CharField(help_text="Placeholder name without angle brackets", max_length=255),
                ),
                ("regex_pattern", models.CharField(blank=True, max_length=500)),
                ("table_index", models.PositiveIntegerField(blank=True, null=True)),
                ("is_enabled", models.BooleanField(default=True)),
                ("priority", models.PositiveIntegerField(default=1)),
                (
                    "template_type",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="extraction_rules", to="document_processor.templatetype"),
                ),
            ],
            options={"ordering": ["priority", "id"], "abstract": False},
        ),
        migrations.CreateModel(
            name="UploadedDocument",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "id",
                    models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
                ),
                ("file", models.FileField(upload_to="uploaded_pdfs/")),
                ("original_filename", models.CharField(max_length=255)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("uploaded", "Uploaded"),
                            ("processing", "Processing"),
                            ("extracted", "Extracted"),
                            ("verified", "Verified"),
                            ("generated", "Generated"),
                            ("failed", "Failed"),
                        ],
                        default="uploaded",
                        max_length=20,
                    ),
                ),
                ("upload_time", models.DateTimeField(default=django.utils.timezone.now)),
                ("processed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "template_type",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="uploaded_documents", to="document_processor.templatetype"),
                ),
                (
                    "uploaded_by",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="uploaded_documents", to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="TextractResult",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("raw_response", models.JSONField()),
                ("confidence_score", models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "document",
                    models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="textract_result", to="document_processor.uploadeddocument"),
                ),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="ProcessingLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("status_from", models.CharField(blank=True, max_length=20)),
                ("status_to", models.CharField(max_length=20)),
                ("message", models.TextField(blank=True)),
                (
                    "actor",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
                ),
                (
                    "document",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="processing_logs", to="document_processor.uploadeddocument"),
                ),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="GeneratedDocument",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("generated_file", models.FileField(upload_to="generated_docs/")),
                ("is_final", models.BooleanField(default=False)),
                (
                    "document",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="generated_versions", to="document_processor.uploadeddocument"),
                ),
                (
                    "generated_by",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="generated_documents", to=settings.AUTH_USER_MODEL),
                ),
                (
                    "template",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="generated_documents", to="document_processor.wordtemplate"),
                ),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="ExtractedField",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("field_name", models.CharField(max_length=255)),
                ("extracted_value", models.TextField(blank=True)),
                ("confidence", models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                ("is_table_value", models.BooleanField(default=False)),
                (
                    "document",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="extracted_fields", to="document_processor.uploadeddocument"),
                ),
                (
                    "extraction_rule",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="extracted_fields", to="document_processor.extractionrule"),
                ),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="UserFieldSelection",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("selected_value", models.TextField()),
                ("is_manual_override", models.BooleanField(default=False)),
                (
                    "document",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="field_selections", to="document_processor.uploadeddocument"),
                ),
                (
                    "edited_by",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="field_edits", to=settings.AUTH_USER_MODEL),
                ),
                (
                    "extracted_field",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="user_selections", to="document_processor.extractedfield"),
                ),
            ],
            options={"abstract": False},
        ),
        migrations.AddConstraint(
            model_name="wordtemplate",
            constraint=models.UniqueConstraint(fields=("template_type", "version"), name="uniq_template_type_version"),
        ),
        migrations.AddConstraint(
            model_name="extractionrule",
            constraint=models.UniqueConstraint(fields=("template_type", "source_key", "target_field"), name="uniq_rule_target_mapping"),
        ),
        migrations.AddIndex(
            model_name="extractedfield",
            index=models.Index(fields=["document", "field_name"], name="document_pr_document_1b4f26_idx"),
        ),
        migrations.AddConstraint(
            model_name="userfieldselection",
            constraint=models.UniqueConstraint(fields=("document", "extracted_field", "edited_by"), name="uniq_user_selection_per_field"),
        ),
    ]
