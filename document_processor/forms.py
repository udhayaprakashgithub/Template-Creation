from django import forms
from .models import ExtractionRule, UploadedDocument, WordTemplate, UserFieldSelection


class UploadDocumentForm(forms.ModelForm):
    files = forms.FileField(
        widget=forms.ClearableFileInput(attrs={"multiple": True, "class": "form-control"}),
        required=True,
        help_text="Upload one or more PDF files.",
    )

    class Meta:
        model = UploadedDocument
        fields = ["template_type"]
        widgets = {"template_type": forms.Select(attrs={"class": "form-select"})}


class WordTemplateForm(forms.ModelForm):
    class Meta:
        model = WordTemplate
        fields = ["name", "template_type", "file", "version", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "template_type": forms.Select(attrs={"class": "form-select"}),
            "file": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "version": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class ExtractionRuleForm(forms.ModelForm):
    class Meta:
        model = ExtractionRule
        fields = [
            "template_type",
            "rule_type",
            "source_key",
            "target_field",
            "regex_pattern",
            "table_index",
            "priority",
            "is_enabled",
        ]


class FieldSelectionForm(forms.ModelForm):
    class Meta:
        model = UserFieldSelection
        fields = ["selected_value", "is_manual_override"]
        widgets = {
            "selected_value": forms.TextInput(attrs={"class": "form-control"}),
            "is_manual_override": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
