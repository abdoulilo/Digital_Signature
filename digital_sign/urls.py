from django.urls import path
from . import views

urlpatterns = [
    path('', views.upload_pdf_view, name='home'),
    path('upload/', views.upload_pdf_view, name='upload_pdf'),

    # Free signing flow, protected by signed token, not login
    path('sign/<str:token>/', views.sign_pdf_view, name='sign_pdf'),
    path('result/<str:token>/', views.result_view, name='result'),

    # General verification page
    path('verify/', views.verify_pdf_view, name='verify_pdf'),

    # Public certificate verification, protected by signed token
    path('verify/certificate/<str:token>/', views.certificate_page, name='certificate_page'),
    path('verify/certificate/<str:token>/upload/', views.qr_verify_upload, name='qr_verify_upload'),
    path('verify/certificate/<str:token>/download/', views.download_certificate_pdf, name='download_certificate_pdf'),

    path('signup/', views.signup_view, name='signup'),
]