from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', views.home, name='home'),  # Home page URL
    path('login-link/', views.login_links, name='login_links'),
    path('facilities/', views.facility_list, name='facility_list'),
    path('login/patient/', views.login_patient, name='login_patient'),
    path('dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('register/', views.register_patient, name='register_patient'),
    path('book-appointment/', views.book_appointment, name='book_appointment'),
    path('appointments/', views.appointment_list, name='appointment_list'),
    path('medical-history/<int:patient_id>/', views.view_medical_history, name='view_medical_history'),
    path('resources/', views.health_resources, name='health_resources'),
    path('cancel_appointment/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    path('payment/initiate/<int:appointment_id>/', views.initiate_payment, name='initiate_payment'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/failed/', views.payment_failed, name='payment_failed'),
    path('doctors/', views.doctor_list, name='doctor_list'),

    path('login/doctor/', views.login_doctor, name='login_doctor'),
    path('doctor/dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('doctor/appointments/', views.get_appointments, name='get_appointments'),
    path('doctor/patient/<int:patient_id>/records/', views.patient_management, name='patient_management'),
    path('doctor/patient/<int:patient_id>/add-record/', views.add_medical_history, name='add_medical_history'),
    path('doctor/patient/<int:patient_id>/prescribe/', views.e_prescribe, name='e_prescribe'),

    path('login/admin/', views.login_admin, name='login_admin'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),

    path('custom-admin/users/', views.user_management, name='manage_users'),
    path('custom-admin/users/create/', views.create_user, name='create_user'),
    path('custom-admin/users/edit/<int:user_id>/', views.edit_user, name='edit_user'),
    path('custom-admin/users/delete/<int:user_id>/', views.delete_user, name='delete_user'),

    path('custom-admin/facilities/', views.facility_management, name='manage_facilities'),
    path('custom-admin/facilities/create/', views.create_facility, name='create_facility'),
    path('custom-admin/facilities/edit/<int:facility_id>/', views.edit_facility, name='edit_facility'),
    path('custom-admin/facilities/delete/<int:facility_id>/', views.delete_facility, name='delete_facility'),

    path('custom-admin/appointments/', views.appointment_management, name='manage_appointments'),
    path('custom-admin/appointments/create/', views.create_appointment, name='create_appointment'),
    path('custom-admin/appointments/edit/<int:appointment_id>/', views.edit_appointment, name='edit_appointment'),
    path('custom-admin/appointments/delete/<int:appointment_id>/', views.delete_appointment, name='delete_appointment'),

    path('departments/', views.department_list, name='department_list'),
    path('department/<int:department_id>/', views.department_detail, name='department_detail'),
    path('department/create/', views.create_department, name='create_department'),
    path('department/edit/<int:department_id>/', views.edit_department, name='edit_department'),
    path('department/delete/<int:department_id>/', views.delete_department, name='delete_department'),
    path('manage_departments/', views.manage_departments, name='manage_departments'),

    path('logout/', views.logout_patient, name='logout_patient'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)