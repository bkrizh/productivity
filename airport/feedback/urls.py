from django.urls import path

from . import views

app_name = 'feedback'


urlpatterns = [
    path('', views.index, name='index'),

    path('offers/', views.offers, name='offers'),
    path('all_offers/', views.all_offers, name='all_offers'),
    path('offer/<int:offer_id>/', views.offer, name='offer'),
    path('offer_add/', views.offer_add, name='offer_add'),
    path('offer/download/<int:offer_id>/', views.offer_document_download, name='offer_document_download'),
    path('offer/edit/<int:offer_id>/', views.offer_edit, name='offer_edit'),
    path('offer/delete/<int:offer_id>/', views.offer_delete, name='offer_delete'),

    path('register/', views.register, name='register'),
    path('verify_email/', views.verify_email, name='verify_email'),

    path('reset_password/', views.reset_password, name='reset_password'),
    path('verify_password/', views.verify_password, name='verify_password'),

    path('success/', views.success, name='success'),
    path('error/', views.error, name='error'),


    path('media/<path:path>', views.protected_media_view, name='protected_media_view'),

    path('export_user_xls/<int:offer_id>/', views.export_user_xls, name='export_user_xls'),
    path('export_xls/', views.export_users_xls, name='export_users_xls'),

    path('recipients/', views.recipients_list, name='recipients_list'),
    path('add_recipient/', views.add_recipient, name='add_recipient'),
    path('edit_recipient/<int:pk>/', views.edit_recipient, name='edit_recipient'),
    path('delete_recipient/<int:pk>/', views.delete_recipient, name='delete_recipient'),
]
