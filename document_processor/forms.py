from django import forms

from .models import ExtractionRule, TemplateType, UploadedDocument, UserFieldSelection, UserProfile, WordTemplate


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        single_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_clean(d, initial) for d in data]
        return [single_clean(data, initial)] if data else []


class UploadDocumentForm(forms.ModelForm):
    files = MultipleFileField(
        widget=MultipleFileInput(attrs={"multiple": True, "class": "form-control"}),
        required=True,
        help_text="Upload one or more PDF files.",
    )

    class Meta:
        model = UploadedDocument
        fields = ["template_type"]
        widgets = {"template_type": forms.Select(attrs={"class": "form-select"})}


class TemplateTypeForm(forms.ModelForm):
    class Meta:
        model = TemplateType
        fields = ["code", "name", "description", "is_active"]
        widgets = {
            "code": forms.Select(attrs={"class": "form-select"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


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
        widgets = {
            "template_type": forms.Select(attrs={"class": "form-select"}),
            "rule_type": forms.Select(attrs={"class": "form-select"}),
            "source_key": forms.TextInput(attrs={"class": "form-control"}),
            "target_field": forms.TextInput(attrs={"class": "form-control"}),
            "regex_pattern": forms.TextInput(attrs={"class": "form-control"}),
            "table_index": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "priority": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "is_enabled": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class UserRoleForm(forms.Form):
    role = forms.ChoiceField(choices=UserProfile.Role.choices, widget=forms.Select(attrs={"class": "form-select"}))


class FieldSelectionForm(forms.ModelForm):
    class Meta:
        model = UserFieldSelection
        fields = ["selected_value", "is_manual_override"]
        widgets = {
            "selected_value": forms.TextInput(attrs={"class": "form-control"}),
            "is_manual_override": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
