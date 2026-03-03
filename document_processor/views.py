from pathlib import Path

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DetailView, FormView, ListView, TemplateView, UpdateView

from .forms import ExtractionRuleForm, TemplateTypeForm, UploadDocumentForm, UserRoleForm, WordTemplateForm
from .models import (
    AuditTrail,
    ExtractedField,
    ExtractionRule,
    ProcessingLog,
    TemplateType,
    TextractResult,
    UploadedDocument,
    UserFieldSelection,
    UserProfile,
    WordTemplate,
)
from .permissions import AdminRequiredMixin, UserOrAdminRequiredMixin
from .services import DocumentBuilder, ExtractionEngine, TextractService

User = get_user_model()


class DocumentAccessMixin(UserOrAdminRequiredMixin):
    def get_document(self):
        document = get_object_or_404(UploadedDocument, pk=self.kwargs["document_id"])
        role = getattr(getattr(self.request.user, "profile", None), "role", "user")
        if role != "admin" and document.uploaded_by_id != self.request.user.id:
            raise Http404("Document not found")
        return document

    def log_status(self, document, status_from, status_to, message=""):
        ProcessingLog.objects.create(
            document=document,
            actor=self.request.user,
            status_from=status_from,
            status_to=status_to,
            message=message,
        )


class DashboardView(UserOrAdminRequiredMixin, TemplateView):
    template_name = "document_processor/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        role = getattr(getattr(self.request.user, "profile", None), "role", "user")
        context["role"] = role
        context["documents_count"] = UploadedDocument.objects.count()
        context["templates_count"] = WordTemplate.objects.filter(is_active=True).count()
        context["rules_count"] = ExtractionRule.objects.filter(is_enabled=True).count()
        return context


class UploadDocumentView(UserOrAdminRequiredMixin, FormView):
    template_name = "document_processor/user/upload.html"
    form_class = UploadDocumentForm
    success_url = reverse_lazy("document_processor:user-history")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        configured_types = TemplateType.objects.filter(
            is_active=True,
            templates__is_active=True,
            extraction_rules__is_enabled=True,
        ).distinct()
        form.fields["template_type"].queryset = configured_types
        return form

    def form_valid(self, form):
        template_type = form.cleaned_data["template_type"]
        if not template_type.templates.filter(is_active=True).exists() or not template_type.extraction_rules.filter(is_enabled=True).exists():
            messages.error(self.request, "Selected template type is not fully configured by admin.")
            return self.form_invalid(form)

        files = self.request.FILES.getlist("files")
        for file_obj in files:
            uploaded = UploadedDocument.objects.create(
                uploaded_by=self.request.user,
                template_type=template_type,
                file=file_obj,
                original_filename=file_obj.name,
                status=UploadedDocument.Status.UPLOADED,
            )
            ProcessingLog.objects.create(
                document=uploaded,
                actor=self.request.user,
                status_to=UploadedDocument.Status.UPLOADED,
                message="File uploaded",
            )
            AuditTrail.objects.create(
                user=self.request.user,
                action_type=AuditTrail.ActionType.CREATE,
                model_name="UploadedDocument",
                object_id=str(uploaded.pk),
                metadata={"filename": file_obj.name, "template_type": template_type.code},
            )

        messages.success(self.request, f"Uploaded {len(files)} file(s) successfully.")
        return super().form_valid(form)


class UserHistoryView(UserOrAdminRequiredMixin, ListView):
    model = UploadedDocument
    template_name = "document_processor/user/history.html"

    def get_queryset(self):
        qs = UploadedDocument.objects.select_related("template_type", "uploaded_by").order_by("-created_at")
        role = getattr(getattr(self.request.user, "profile", None), "role", "user")
        return qs if role == "admin" else qs.filter(uploaded_by=self.request.user)


class ExtractionPreviewView(DocumentAccessMixin, DetailView):
    model = UploadedDocument
    pk_url_kwarg = "document_id"
    template_name = "document_processor/user/preview.html"
    context_object_name = "document"

    def get_object(self, queryset=None):
        return self.get_document()


class ProcessDocumentView(DocumentAccessMixin, TemplateView):
    template_name = "document_processor/user/preview.html"

    def post(self, request, *args, **kwargs):
        document = self.get_document()
        previous = document.status

        try:
            document.status = UploadedDocument.Status.PROCESSING
            document.save(update_fields=["status", "updated_at"])
            self.log_status(document, previous, document.status, "Textract processing started")

            textract = TextractService()
            with document.file.open("rb") as pdf_handle:
                output = textract.analyze_document(pdf_handle.read())

            textract_result, _ = TextractResult.objects.get_or_create(
                document=document,
                defaults={"raw_response": output.raw_response},
            )
            textract_result.raw_response = output.raw_response
            textract_result.confidence_score = output.average_confidence
            textract_result.completed_at = timezone.now()
            textract_result.save(update_fields=["raw_response", "confidence_score", "completed_at", "updated_at"])

            ExtractedField.objects.filter(document=document).delete()
            ExtractionEngine().apply_rules(document, output.raw_response)

            document.status = UploadedDocument.Status.EXTRACTED
            document.processed_at = timezone.now()
            document.save(update_fields=["status", "processed_at", "updated_at"])
            self.log_status(document, UploadedDocument.Status.PROCESSING, document.status, "Textract completed")
            messages.success(request, "Textract processing completed.")
        except Exception as exc:
            document.status = UploadedDocument.Status.FAILED
            document.save(update_fields=["status", "updated_at"])
            self.log_status(document, UploadedDocument.Status.PROCESSING, document.status, f"Processing failed: {exc}")
            messages.error(request, "Document processing failed. Please contact an administrator.")

        return redirect("document_processor:verify-fields", document_id=document.pk)


class VerifyFieldsView(DocumentAccessMixin, TemplateView):
    template_name = "document_processor/user/verify_fields.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        document = self.get_document()
        context["document"] = document
        context["fields"] = document.extracted_fields.all().order_by("field_name", "id")
        return context

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        document = self.get_document()

        for extracted in document.extracted_fields.all():
            selected = request.POST.get(f"field_{extracted.id}", extracted.extracted_value)
            UserFieldSelection.objects.update_or_create(
                document=document,
                extracted_field=extracted,
                edited_by=request.user,
                defaults={
                    "selected_value": selected,
                    "is_manual_override": selected != extracted.extracted_value,
                },
            )

        old_status = document.status
        document.status = UploadedDocument.Status.VERIFIED
        document.save(update_fields=["status", "updated_at"])
        self.log_status(document, old_status, document.status, "Fields verified by user")
        messages.success(request, "Field selections saved.")
        return redirect("document_processor:generate-document", document_id=document.pk)


class GenerateDocumentView(DocumentAccessMixin, TemplateView):
    template_name = "document_processor/user/download.html"

    def get(self, request, *args, **kwargs):
        document = self.get_document()
        selected_template = (
            WordTemplate.objects.filter(template_type=document.template_type, is_active=True)
            .order_by("-version")
            .first()
        )
        if not selected_template:
            messages.error(request, "No active template found for selected type.")
            return HttpResponseRedirect(reverse("document_processor:preview", kwargs={"document_id": document.pk}))

        selections = UserFieldSelection.objects.filter(document=document, edited_by=request.user).select_related("extracted_field")
        replacements = {selection.extracted_field.field_name: selection.selected_value for selection in selections}
        if not replacements:
            replacements = {field.field_name: field.extracted_value for field in document.extracted_fields.all()}

        output_dir = Path("media/generated_docs/runtime")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{document.pk}.docx"

        builder = DocumentBuilder()
        builder.populate_template(selected_template.file.path, replacements, output_path)
        generated = builder.create_generated_record(document, selected_template, request.user, output_path, is_final=True)

        old_status = document.status
        document.status = UploadedDocument.Status.GENERATED
        document.save(update_fields=["status", "updated_at"])
        self.log_status(document, old_status, document.status, "Generated final DOCX")

        AuditTrail.objects.create(
            user=request.user,
            action_type=AuditTrail.ActionType.PROCESS,
            model_name="GeneratedDocument",
            object_id=str(generated.id),
            metadata={"document": str(document.id), "template": selected_template.name},
        )

        messages.success(request, "Document generated successfully.")
        return self.render_to_response(self.get_context_data(document=document, generated=generated))


class AdminDashboardView(AdminRequiredMixin, TemplateView):
    template_name = "document_processor/admin/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["template_type_count"] = TemplateType.objects.count()
        context["template_count"] = WordTemplate.objects.count()
        context["rule_count"] = ExtractionRule.objects.count()
        context["user_count"] = User.objects.count()
        return context


class TemplateTypeListView(AdminRequiredMixin, ListView):
    model = TemplateType
    template_name = "document_processor/admin/template_type_list.html"
    queryset = TemplateType.objects.order_by("name")


class TemplateTypeCreateView(AdminRequiredMixin, CreateView):
    model = TemplateType
    form_class = TemplateTypeForm
    template_name = "document_processor/admin/template_type_form.html"
    success_url = reverse_lazy("document_processor:admin-template-type-list")


class TemplateTypeUpdateView(AdminRequiredMixin, UpdateView):
    model = TemplateType
    form_class = TemplateTypeForm
    template_name = "document_processor/admin/template_type_form.html"
    success_url = reverse_lazy("document_processor:admin-template-type-list")


class WordTemplateListView(AdminRequiredMixin, ListView):
    model = WordTemplate
    template_name = "document_processor/admin/template_list.html"
    queryset = WordTemplate.objects.select_related("template_type", "uploaded_by").order_by("template_type__name", "-version")


class WordTemplateCreateView(AdminRequiredMixin, CreateView):
    model = WordTemplate
    form_class = WordTemplateForm
    template_name = "document_processor/admin/template_form.html"
    success_url = reverse_lazy("document_processor:admin-template-list")

    def form_valid(self, form):
        form.instance.uploaded_by = self.request.user
        messages.success(self.request, "Template saved.")
        return super().form_valid(form)


class ExtractionRuleListView(AdminRequiredMixin, ListView):
    model = ExtractionRule
    template_name = "document_processor/admin/rule_list.html"
    queryset = ExtractionRule.objects.select_related("template_type").order_by("template_type__name", "priority")


class ExtractionRuleCreateView(AdminRequiredMixin, CreateView):
    model = ExtractionRule
    form_class = ExtractionRuleForm
    template_name = "document_processor/admin/rule_form.html"
    success_url = reverse_lazy("document_processor:admin-rule-list")


class ExtractionRuleUpdateView(AdminRequiredMixin, UpdateView):
    model = ExtractionRule
    form_class = ExtractionRuleForm
    template_name = "document_processor/admin/rule_form.html"
    success_url = reverse_lazy("document_processor:admin-rule-list")


class ProcessingLogListView(AdminRequiredMixin, ListView):
    model = ProcessingLog
    template_name = "document_processor/admin/logs.html"
    queryset = ProcessingLog.objects.select_related("document", "actor").order_by("-created_at")


class UserManagementView(AdminRequiredMixin, TemplateView):
    template_name = "document_processor/admin/user_management.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        users = User.objects.select_related("profile").order_by("username")
        context["rows"] = [
            {
                "user": user,
                "form": UserRoleForm(initial={"role": getattr(getattr(user, "profile", None), "role", UserProfile.Role.USER)}),
            }
            for user in users
        ]
        return context

    def post(self, request, *args, **kwargs):
        user_id = request.POST.get("user_id")
        target = get_object_or_404(User, id=user_id)
        form = UserRoleForm(request.POST)
        if form.is_valid():
            profile, _ = UserProfile.objects.get_or_create(user=target)
            profile.role = form.cleaned_data["role"]
            profile.save(update_fields=["role", "updated_at"])
            messages.success(request, f"Updated role for {target.username}.")
        else:
            messages.error(request, "Invalid role selection.")
        return redirect("document_processor:admin-user-management")
