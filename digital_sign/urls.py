from django.urls import path
from . import views

urlpatterns = [
    path('', views.upload_pdf_view, name='home'),
    path('upload/', views.upload_pdf_view, name='upload_pdf'),
    path('sign/<int:document_id>/', views.sign_pdf_view, name='sign_pdf'),
    path('verify/', views.verify_pdf_view, name='verify_pdf'),
    path('result/<int:document_id>/', views.result_view, name='result'),
    path('signup/', views.signup_view, name='signup'),
]