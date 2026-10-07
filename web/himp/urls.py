from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path
from office import views, google_calendar, google_drive

urlpatterns = [
    path('admin/', admin.site.urls),
    path('entrar/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('sair/', auth_views.LogoutView.as_view(), name='logout'),
    path('conta/senha/', auth_views.PasswordChangeView.as_view(template_name='registration/password_change.html'), name='password_change'),
    path('conta/senha/alterada/', auth_views.PasswordChangeDoneView.as_view(template_name='registration/password_done.html'), name='password_change_done'),
    path('', views.dashboard, name='dashboard'),
    path('health/', views.health, name='health'),
    path('relatorios/financeiro/', views.financial_report, name='financial_report'),
    path('gerar-documento/', views.generate_document, name='generate_document'),
    path('google/ligar/', google_calendar.connect, name='google_connect'),
    path('google/callback/', google_calendar.callback, name='google_callback'),
    path('google/drive/ligar/', google_drive.connect, name='drive_connect'),
    path('google/drive/callback/', google_drive.callback, name='drive_callback'),
    path('clientes/<int:pk>/pasta-drive/', views.client_drive_folder, name='client_drive_folder'),
    path('documentos/<int:pk>/enviar-drive/', views.document_upload, name='document_upload'),
    path('agenda/<int:pk>/sincronizar/', views.calendar_sync, name='calendar_sync'),
    path('gestao/<str:resource>/', views.record_list, name='record_list'),
    path('gestao/<str:resource>/novo/', views.record_edit, name='record_create'),
    path('gestao/<str:resource>/<int:pk>/', views.record_detail, name='record_detail'),
    path('gestao/<str:resource>/<int:pk>/editar/', views.record_edit, name='record_edit'),
    path('gestao/<str:resource>/<int:pk>/eliminar/', views.record_delete, name='record_delete'),
]
