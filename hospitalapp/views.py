from datetime import timezone
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils.timezone import now
import stripe
from .models import Patient, HealthResource, UserPermission
from django.contrib.auth.models import User
from .models import Facility, TreatmentPlan
from .forms import FacilityForm, AppointmentForm, DoctorLoginForm, PatientRegistrationForm, CustomUserCreationForm, \
    UserForm
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test
from .models import Doctor, Appointment, EPrescription, MedicalHistory, Billing
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import update_session_auth_hash
from .models import Location, Department
from django.contrib import messages
from .forms import PatientLoginForm, EPrescriptionForm, MedicalHistoryForm, DepartmentForm


def home(request):
    return render(request, 'home.html')


def logout_patient(request):
    logout(request)
    return redirect('home')


# Patient Registration View
def register_patient(request):
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            patient = form.save()  # This will create a User and Patient
            user = patient.user  # Link the patient to the user
            login(request, user)  # Log the user in automatically after registration
            return redirect('patient_dashboard')  # Redirect to dashboard after successful registration
    else:
        form = PatientRegistrationForm()

    return render(request, 'register_patient.html', {'form': form})


def login_patient(request):
    if request.method == 'POST':
        form = PatientLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                # Ensure that the logged-in user has a linked Patient object
                try:
                    patient = user.patient  # Fetch the associated Patient object
                    print(patient)
                    return redirect('patient_dashboard')  # Redirect to patient dashboard
                except Patient.DoesNotExist:
                    print("Patient does not exist for user")
                    messages.error(request, 'You must complete the registration to proceed.')
                    return redirect('register_patient')  # Redirect to registration page if Patient doesn't exist
            else:
                messages.error(request, 'Invalid credentials')
        else:
            messages.error(request, 'Form is not valid')
    else:
        form = PatientLoginForm()

    return render(request, 'login_patient.html', {'form': form})


# Dashboard View
@login_required
def patient_dashboard(request):
    try:
        # Try to fetch the Patient object linked to the logged-in user
        patient = request.user.patient
    except Patient.DoesNotExist:
        # If the Patient object does not exist, redirect to registration page
        return redirect('register_patient')

    # Fetch relevant data for the patient
    appointments = Appointment.objects.filter(patient=patient).exclude(status='Cancelled')
    medical_history = MedicalHistory.objects.filter(patient=patient)
    billing_details = Billing.objects.filter(appointment__patient=patient).filter(payment_status='Completed')

    if request.method == 'POST' and 'book_appointment' in request.POST:
        appointment_form = AppointmentForm(request.POST)
        if appointment_form.is_valid():
            appointment = appointment_form.save(commit=False)
            appointment.patient = patient
            appointment.save()
            return redirect('initiate_payment', appointment_id=appointment.id)

    else:
        appointment_form = AppointmentForm()

    context = {
        'appointments': appointments,
        'medical_history': medical_history,
        'appointment_form': appointment_form,
        'billing_details': billing_details,
    }
    return render(request, 'patient_dashboard.html', context)


# Appointment Booking View
@login_required
def book_appointment(request):
    if not hasattr(request.user, 'patient'):
        return HttpResponseForbidden("You are not a patient.")

    patient = request.user.patient
    form = AppointmentForm(request.POST or None)

    if form.is_valid():
        # Save the appointment without committing it to the database yet
        appointment = form.save(commit=False)
        appointment.patient = patient
        appointment.status = 'Pending'  # Status is pending until payment is completed
        appointment.save()

        # Create a Billing record for the appointment (pending payment)
        billing = Billing.objects.create(
            appointment=appointment,
            amount=150.00,  # Amount in INR
            payment_status='Pending',  # Initially, the payment is pending
        )

        messages.success(request, "Proceed with payment.")
        # Redirect to initiate payment (Payment will only be completed after this step)
        return redirect('initiate_payment', appointment_id=appointment.id)

    return render(request, 'book_appointment.html', {'form': form})



@login_required
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    if appointment.status == 'Scheduled':
        appointment.status = 'Cancelled'
        appointment.save()
        messages.success(request, "The appointment has been cancelled successfully.")
    else:
        messages.error(request, "This appointment cannot be cancelled.")
    return redirect('appointment_list')


# View for listing and managing appointments
@login_required
def appointment_list(request):
    patient = request.user.patient
    scheduled_appointments = Appointment.objects.filter(patient=patient, status='Scheduled')
    canceled_appointments = Appointment.objects.filter(patient=patient, status='Cancelled')
    return render(request, 'appointment_list.html', {
        'scheduled_appointments': scheduled_appointments,
        'canceled_appointments': canceled_appointments,
    })


@login_required
def get_appointments(request):
    appointments = Appointment.objects.filter(doctor=request.user.doctor)  # Assuming you have a relationship with the doctor
    appointments_data = []
    for appointment in appointments:
        appointments_data.append({
            'patient_name': f"{appointment.patient.first_name} {appointment.patient.last_name}",
            'date': appointment.date.strftime('%Y-%m-%d %H:%M'),
            'reason': appointment.reason,
            'status': appointment.status,
            'patient_id': appointment.patient.id,
        })
    return JsonResponse({'appointments': appointments_data})


def view_patient_records(request, patient_id):
    patient = Patient.objects.get(id=patient_id)
    medical_history = MedicalHistory.objects.filter(patient=patient)
    return render(request, 'patient_records.html', {'patient': patient, 'medical_history': medical_history})


# Medical History View
@login_required
def view_medical_history(request, patient_id):
    patient = Patient.objects.get(id=patient_id)
    medical_history = MedicalHistory.objects.filter(patient=patient)
    return render(request, 'patient_records.html', {'patient': patient, 'medical_history': medical_history})


@login_required
def add_medical_history(request, patient_id):
    patient = Patient.objects.get(id=patient_id)

    if request.method == 'POST':
        form = MedicalHistoryForm(request.POST)
        if form.is_valid():
            medical_history = form.save(commit=False)
            medical_history.patient = patient
            medical_history.date_prescribed = now().date()
            medical_history.save()
            return redirect('patient_management', patient_id=patient.id)
    else:
        form = MedicalHistoryForm()

    return render(request, 'add_medical_history.html', {'form': form, 'patient': patient})


# Health Education Resources View
def health_resources(request):
    resources = HealthResource.objects.all()
    return render(request, 'health_resources.html', {'resources': resources})


# Check if the user is a doctor
def is_doctor(user):
    return hasattr(user, 'doctor')


# Doctor Dashboard/Patient Management View
# views.py
@user_passes_test(is_doctor)
def doctor_dashboard(request):
    doctor = Doctor.objects.get(user=request.user)
    appointments = Appointment.objects.filter(doctor=doctor)
    patients = Patient.objects.filter(appointment__doctor=doctor).distinct()  # Patients with appointments with the doctor

    # Check if the doctor submits medical history
    if request.method == 'POST':
        patient_id = request.POST.get('patient_id')
        medication = request.POST.get('medication')
        treatment_plan = request.POST.get('treatment_plan')
        diagnosis = request.POST.get('diagnosis')
        treatment = request.POST.get('treatment')

        patient = get_object_or_404(Patient, id=patient_id)

        # Create medical history entry
        medical_history = MedicalHistory(
            patient=patient,
            date=timezone.now().date(),
            diagnosis=diagnosis,
            treatment_plan=treatment_plan,
            medication=medication,
            treatment=treatment
        )
        medical_history.save()

        messages.success(request, "Medical history added successfully!")

    return render(request, 'doctor_dashboard.html', {
        'doctor': doctor,
        'appointments': appointments,
        'patients': patients
    })


@login_required
@user_passes_test(is_doctor)
def patient_management(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    medical_history = MedicalHistory.objects.filter(patient=patient).order_by('-date_prescribed')
    e_prescriptions = EPrescription.objects.filter(patient=patient).order_by('-date_prescribed')
    treatment_plan = TreatmentPlan.objects.filter(patient=patient).first()  # Assuming a model for treatment plan
    return render(request, 'patient_management.html', {
        'patient': patient,
        'medical_history': medical_history,
        'e_prescriptions': e_prescriptions,
        'treatment_plan': treatment_plan,
    })


@login_required
def view_treatment_plan(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    medical_history = MedicalHistory.objects.filter(patient=patient).order_by('-date_prescribed')  # Get the latest history

    return render(request, 'view_treatment_plan.html', {'patient': patient, 'medical_history': medical_history})


@login_required
def view_medication(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    medical_history = MedicalHistory.objects.filter(patient=patient).order_by('-date_prescribed')  # Get the latest history

    return render(request, 'view_medication.html', {'patient': patient, 'medical_history': medical_history})


# Appointment Schedule View
@login_required
@user_passes_test(is_doctor)
def appointment_schedule(request):
    doctor = Doctor.objects.get(user=request.user)
    appointments = Appointment.objects.filter(doctor=doctor).order_by('date')
    return render(request, 'appointment_schedule.html', {
        'appointments': appointments,
    })


# E-Prescribing View
# views.py
@login_required
@user_passes_test(is_doctor)
def e_prescribe(request, patient_id):
    doctor = Doctor.objects.get(user=request.user)
    patient = Patient.objects.get(id=patient_id)
    if request.method == 'POST':
        form = EPrescriptionForm(request.POST)
        if form.is_valid():
            prescription = form.save(commit=False)
            prescription.doctor = doctor
            prescription.patient = patient
            prescription.save()
            MedicalHistory.objects.create(
                patient=patient,
                diagnosis='E-Prescription',  # Assuming a generic diagnosis
                treatment_plan=f"Prescribed by Dr. {doctor.user.username}",
                medication=prescription.medication,
                notes=f"Dosage: {prescription.dosage}, Instructions: {prescription.instructions}",
                date_prescribed=prescription.date_prescribed
            )
            return redirect('doctor_dashboard')  # Redirect to doctor dashboard after successful submission
    else:
        form = EPrescriptionForm()
    return render(request, 'e_prescribe.html', {'form': form, 'patient': patient})




def login_doctor(request):
    if request.method == 'POST':
        form = DoctorLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)

            if user is not None:
                # Check if the user is a doctor by querying the Doctor model
                try:
                    doctor = Doctor.objects.get(user=user)
                    login(request, user)
                    return redirect('doctor_dashboard')  # Assuming you have a doctor dashboard page
                except Doctor.DoesNotExist:
                    form.add_error(None, 'This user is not a doctor.')
            else:
                form.add_error(None, 'Invalid username or password.')
    else:
        form = DoctorLoginForm()

    return render(request, 'login_doctor.html', {'form': form})


def login_admin(request):
    # Initialize form for both GET and POST requests
    form = AuthenticationForm()

    # Handle POST request for form submission
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('admin_dashboard')  # Adjust this to your admin dashboard URL

    return render(request, 'login_admin.html', {'form': form})


@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        return redirect('login_admin')  # Redirect non-admin users to the login page

    # Fetch data as before
    patients = Patient.objects.all()
    doctors = Doctor.objects.all()
    appointments = Appointment.objects.all()

    return render(request, 'admin_dashboard.html', {
        'patients': patients,
        'doctors': doctors,
        'appointments': appointments
    })


@staff_member_required
def create_user(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True
            user.set_password(form.cleaned_data['password1'])
            user.save()

            user_permission, created = UserPermission.objects.get_or_create(user=user, defaults={
                'role': form.cleaned_data['role']
            })
            if not created:
                user_permission.role = form.cleaned_data['role']
                user_permission.save()

            if user_permission.role == 'Patient':
                Patient.objects.get_or_create(
                    user=user,
                    defaults={
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'email': user.email,
                        'phone_number': form.cleaned_data['phone_number'],
                        'gender': form.cleaned_data['gender']
                    }
                )
            elif user_permission.role == 'Doctor':
                Doctor.objects.get_or_create(
                    user=user,
                    defaults={
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'email': user.email,
                        'phone_number': form.cleaned_data['phone_number'],
                        'specialization': form.cleaned_data['specialization'],
                        'department': form.cleaned_data['department']  # Save department
                    }
                )

            messages.success(request, 'User created successfully!')
            return redirect('manage_users')
    else:
        form = CustomUserCreationForm()
    return render(request, 'create_user.html', {'form': form})


@receiver(post_save, sender=User)
def create_user_permission(sender, instance, created, **kwargs):
    if created:
        # Create UserPermission only for newly created users
        UserPermission.objects.create(user=instance, role='Patient')  # Default role
    else:
        # Ensure UserPermission exists for existing users
        if not UserPermission.objects.filter(user=instance).exists():
            UserPermission.objects.create(user=instance, role='Patient')


@staff_member_required
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user_permission = get_object_or_404(UserPermission, user=user)
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            user_permission.role = form.cleaned_data['role']
            user_permission.save()

            # Update Patient or Doctor instance based on role
            if user_permission.role == 'Patient':
                patient, created = Patient.objects.get_or_create(user=user)
                patient.phone_number = form.cleaned_data['phone_number']
                patient.gender = form.cleaned_data['gender']
                patient.save()
            elif user_permission.role == 'Doctor':
                doctor, created = Doctor.objects.get_or_create(user=user)
                doctor.phone_number = form.cleaned_data['phone_number']
                doctor.specialization = form.cleaned_data['specialization']
                doctor.department = form.cleaned_data.get('department')  # Update department field
                doctor.save()

            messages.success(request, 'User updated successfully!')
            return redirect('manage_users')
    else:
        form = UserForm(instance=user)
    return render(request, 'edit_user.html', {'form': form, 'user_permission': user_permission})


@login_required
@staff_member_required
def user_management(request):
    if not request.user.is_staff:
        return redirect('login_admin')
    users = User.objects.all()
    user_permissions = UserPermission.objects.all()
    user_roles = {permission.user.id: permission.role for permission in user_permissions}
    for user in users:
        user.role = user_roles.get(user.id, 'Unknown')  # Default to 'Unknown' if no role is assigned
    return render(request, 'user_management.html', {'users': users})


@staff_member_required
def delete_user(request, user_id):
    if not request.user.is_staff:
        return redirect('login_admin')

    user = get_object_or_404(User, id=user_id)

    # Prevent deletion of superuser or admin account
    if user.is_superuser or user.username == "admin":
        messages.error(request, "Cannot delete admin or superuser accounts.")
        return redirect('manage_users')

    if request.method == 'POST':
        user.delete()
        messages.success(request, f"User '{user.username}' deleted successfully!")
        return redirect('manage_users')

    return render(request, 'delete_user.html', {'user': user})


@login_required
def facility_management(request):
    if not request.user.is_staff:
        return redirect('login_admin')

    facilities = Facility.objects.all()
    locations = Location.objects.all()
    departments = Department.objects.all()

    return render(request, 'facility_management.html', {
        'facilities': facilities,
        'locations': locations,
        'departments': departments,
    })


@staff_member_required
def create_facility(request):
    if request.method == 'POST':
        form = FacilityForm(request.POST, request.FILES)
        if form.is_valid():
            print("Form is valid")
            form.save()
            messages.success(request, 'Facility added successfully!')
            return redirect('manage_facilities')
    else:
        form = FacilityForm()
    facilities = Facility.objects.all()
    return render(request, 'create_facility.html', {'form': form})


@staff_member_required
def edit_facility(request, facility_id):
    facility = get_object_or_404(Facility, id=facility_id)
    if request.method == 'POST':
        form = FacilityForm(request.POST, request.FILES, instance=facility)
        if form.is_valid():
            form.save()
            messages.success(request, 'Facility updated successfully!')
            return redirect('manage_facilities')
    else:
        form = FacilityForm(instance=facility)
    return render(request, 'edit_facility.html', {'form': form, 'facility': facility})


@staff_member_required
def delete_facility(request, facility_id):
    facility = get_object_or_404(Facility, id=facility_id)
    if request.method == 'POST':
        facility.delete()
        messages.success(request, 'Facility deleted successfully!')
        return redirect('manage_facilities')
    return render(request, 'delete_facility.html', {'facility': facility})


@login_required
def appointment_management(request):
    if not request.user.is_staff:
        return redirect('login_admin')

    appointments = Appointment.objects.all()
    return render(request, 'manage_appointments.html', {'appointments': appointments})


@login_required
def create_appointment(request):
    if not request.user.is_staff:
        return redirect('login_admin')

    if request.method == 'POST':
        patient = Patient.objects.get(id=request.POST['patient_id'])
        doctor = Doctor.objects.get(id=request.POST['doctor_id'])
        date = request.POST['date']
        time = request.POST['time']

        # Combine date and time
        from datetime import datetime
        appointment_time = datetime.strptime(time, '%H:%M').time()
        combined_datetime = datetime.combine(datetime.strptime(date, '%Y-%m-%d').date(), appointment_time)

        # Save the appointment
        appointment = Appointment(patient=patient, doctor=doctor, date=combined_datetime)
        appointment.save()
        return redirect('manage_appointments')

    doctors = Doctor.objects.all()
    patients = Patient.objects.all()
    time_slots = AppointmentForm.TIME_SLOTS  # Fetch time slots from the form
    return render(request, 'create_appointment.html', {
        'doctors': doctors,
        'patients': patients,
        'time_slots': time_slots,
    })


@staff_member_required
def edit_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    if request.method == 'POST':
        form = AppointmentForm(request.POST, instance=appointment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Appointment updated successfully!')
            return redirect('manage_appointments')
    else:
        form = AppointmentForm(instance=appointment)
    return render(request, 'edit_appointment.html', {'form': form, 'appointment': appointment})


@staff_member_required
def delete_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    if request.method == 'POST':
        appointment.delete()
        messages.success(request, 'Appointment deleted successfully!')
        return redirect('manage_appointments')
    return render(request, 'delete_appointment.html', {'appointment': appointment})


@login_required
def initiate_payment(request, appointment_id):
    try:
        appointment = Appointment.objects.get(id=appointment_id)
    except Appointment.DoesNotExist:
        return HttpResponse("Appointment not found", status=404)

    stripe.api_key = settings.STRIPE_TEST_SECRET_KEY

    # Create a Checkout session
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'inr',
                'product_data': {
                    'name': 'Appointment Booking',
                },
                'unit_amount': 15000,  # 150 INR in cents
            },
            'quantity': 1,
        }],
        metadata={'appointment_id': appointment.id},
        mode='payment',
        success_url=request.build_absolute_uri(reverse('payment_success')) + '?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=request.build_absolute_uri(reverse('payment_failed'))
    )

    return redirect(session.url, code=303)


def payment_success(request):
    session_id = request.GET.get('session_id')

    if not session_id:
        return redirect('payment_failed')

    stripe.api_key = settings.STRIPE_TEST_SECRET_KEY

    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except stripe.error.InvalidRequestError:
        return redirect('payment_failed')

    if session.payment_status == 'paid':
        appointment_id = session.metadata['appointment_id']
        billing = Billing.objects.get(appointment_id=appointment_id)

        billing.payment_status = 'Completed'
        billing.payment_date = now()
        billing.save()

        appointment = billing.appointment
        appointment.status = 'Confirmed'
        appointment.save()

        return render(request, 'payment_success.html', {'billing': billing})

    return redirect('payment_failed')


def payment_failed(request):
    return render(request, 'payment_failed.html')


def doctor_list(request):
    doctors = Doctor.objects.all()
    return render(request, 'doctor_list.html', {'doctors': doctors})


def login_links(request):
    return render(request, 'login_links.html')


def facility_list(request):
    facilities = Facility.objects.all()
    return render(request, 'facility_list.html', {'facilities': facilities})


def department_detail(request, department_id):
    department = get_object_or_404(Department, id=department_id)
    doctors = department.doctors.all()  # Access the related doctors
    context = {
        'department': department,
        'doctors': doctors,
    }
    return render(request, 'department_detail.html', context)


def department_list(request):
    departments = Department.objects.prefetch_related('doctors').all()
    return render(request, 'department_list.html', {'departments': departments})



def manage_departments(request):
    departments = Department.objects.all()
    return render(request, 'manage_departments.html', {'departments': departments})


def create_department(request):
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('manage_departments')
    else:
        form = DepartmentForm()
    return render(request, 'create_department.html', {'form': form})


def edit_department(request, department_id):
    department = get_object_or_404(Department, id=department_id)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            return redirect('manage_departments')
    else:
        form = DepartmentForm(instance=department)
    return render(request, 'edit_department.html', {'form': form})


def delete_department(request, department_id):
    department = get_object_or_404(Department, id=department_id)
    if request.method == 'POST':
        department.delete()
        return redirect('manage_departments')
    return render(request, 'delete_department.html', {'department': department})
