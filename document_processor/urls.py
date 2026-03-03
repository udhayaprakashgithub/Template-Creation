from django.urls import path

from . import views

app_name = "document_processor"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("upload/", views.UploadDocumentView.as_view(), name="upload"),
    path("history/", views.UserHistoryView.as_view(), name="user-history"),
    path("documents/<uuid:document_id>/preview/", views.ExtractionPreviewView.as_view(), name="preview"),
    path("documents/<uuid:document_id>/process/", views.ProcessDocumentView.as_view(), name="process-document"),
    path("documents/<uuid:document_id>/verify/", views.VerifyFieldsView.as_view(), name="verify-fields"),
    path("documents/<uuid:document_id>/generate/", views.GenerateDocumentView.as_view(), name="generate-document"),
    path("admin-portal/", views.AdminDashboardView.as_view(), name="admin-dashboard"),
    path("admin-portal/template-types/", views.TemplateTypeListView.as_view(), name="admin-template-type-list"),
    path("admin-portal/template-types/new/", views.TemplateTypeCreateView.as_view(), name="admin-template-type-create"),
    path("admin-portal/template-types/<int:pk>/edit/", views.TemplateTypeUpdateView.as_view(), name="admin-template-type-edit"),
    path("admin-portal/templates/", views.WordTemplateListView.as_view(), name="admin-template-list"),
    path("admin-portal/templates/new/", views.WordTemplateCreateView.as_view(), name="admin-template-create"),
    path("admin-portal/rules/", views.ExtractionRuleListView.as_view(), name="admin-rule-list"),
    path("admin-portal/rules/new/", views.ExtractionRuleCreateView.as_view(), name="admin-rule-create"),
    path("admin-portal/rules/<int:pk>/edit/", views.ExtractionRuleUpdateView.as_view(), name="admin-rule-edit"),
    path("admin-portal/logs/", views.ProcessingLogListView.as_view(), name="admin-logs"),
    path("admin-portal/users/", views.UserManagementView.as_view(), name="admin-user-management"),
    path("admin/templates/", views.WordTemplateListView.as_view(), name="admin-template-list"),
    path("admin/templates/new/", views.WordTemplateCreateView.as_view(), name="admin-template-create"),
    path("admin/rules/", views.ExtractionRuleListView.as_view(), name="admin-rule-list"),
    path("admin/rules/new/", views.ExtractionRuleCreateView.as_view(), name="admin-rule-create"),
    path("admin/rules/<int:pk>/edit/", views.ExtractionRuleUpdateView.as_view(), name="admin-rule-edit"),
    path("admin/logs/", views.ProcessingLogListView.as_view(), name="admin-logs"),
    path("admin/users/", views.UserManagementView.as_view(), name="admin-user-management"),
]
