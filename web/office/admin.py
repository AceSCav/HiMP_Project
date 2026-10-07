from django.contrib import admin
from .forms import TemplateAdminForm
from .models import AuditEvent, Configuration, DocumentTemplate, Entidade, Fase, Motivo, StatusPagamento, TipoProcesso

admin.site.site_header = 'HIMP · Administração'
admin.site.site_title = 'HIMP'
admin.site.index_title = 'Configurações e acessos'

@admin.register(Configuration)
class ConfigurationAdmin(admin.ModelAdmin):
    list_display = ['label', 'category', 'active', 'minutes', 'order']
    list_filter = ['category', 'active']
    search_fields = ['label']
    list_editable = ['active', 'order']

@admin.register(DocumentTemplate)
class TemplateAdmin(admin.ModelAdmin):
    form = TemplateAdminForm
    list_display = ['name', 'active']
    search_fields = ['name']
    # Templates execute a constrained template language: upload/edit is restricted
    # to trusted system administrators, even if a user is granted model permissions.
    def has_add_permission(self, request):
        return request.user.is_superuser
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

@admin.register(AuditEvent)
class AuditAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'actor', 'action', 'model', 'object_id']
    list_filter = ['action', 'model']
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False

for model in [Entidade, TipoProcesso, Fase, Motivo, StatusPagamento]:
    admin.site.register(model)
