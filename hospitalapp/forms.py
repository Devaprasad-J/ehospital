from django import forms
from .models import Patient, Appointment, MedicalHistory, HealthResource, Facility, EPrescription, Department
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


# Form for patient registration
class PatientLoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)


class PatientRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Patient
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'gender']

    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['email'],  # Email used as username
            password=self.cleaned_data['password'],
            email=self.cleaned_data['email'],
        )
        patient = super().save(commit=False)
        patient.user = user  # Link the created user to the patient
        if commit:
            patient.save()  # Save the patient object
        return patient


# Form for appointment booking
# Updated AppointmentForm without 'patient' field
class AppointmentForm(forms.ModelForm):
    TIME_SLOTS = [
        ("09:00", "9:00 AM"),
        ("09:30", "9:30 AM"),
        ("10:00", "10:00 AM"),
        ("10:30", "10:30 AM"),
        ("11:00", "11:00 AM"),
        ("11:30", "11:30 AM"),
        ("14:00", "2:00 PM"),
        ("14:30", "2:30 PM"),
        ("15:00", "3:00 PM"),
        ("15:30", "3:30 PM"),
        ("16:00", "4:00 PM"),
        ("16:30", "4:30 PM"),

    ]

    time = forms.ChoiceField(choices=TIME_SLOTS, label="Appointment Time")

    class Meta:
        model = Appointment
        fields = ['doctor', 'date', 'time', 'reason']

    def clean(self):
        cleaned_data = super().clean()
        appointment_date = cleaned_data.get("date")
        appointment_time = cleaned_data.get("time")

        if appointment_date and appointment_time:
            # Combine the date and time fields into a single datetime object
            from datetime import datetime
            appointment_time = datetime.strptime(appointment_time, '%H:%M').time()
            combined_datetime = datetime.combine(appointment_date, appointment_time)
            cleaned_data['date'] = combined_datetime

        return cleaned_data


# Form for medical history
class MedicalHistoryForm(forms.ModelForm):
    class Meta:
        model = MedicalHistory
        fields = ['diagnosis', 'treatment_plan', 'medication', 'notes']


# Form for facilities management
class FacilityForm(forms.ModelForm):
    class Meta:
        model = Facility
        fields = ['name', 'location', 'description']


# Form for user creation and management (admin view)
class UserForm(forms.ModelForm):
    phone_number = forms.CharField(max_length=15, required=False)
    gender = forms.ChoiceField(choices=[('Male', 'Male'), ('Female', 'Female')], required=False)
    specialization = forms.CharField(max_length=100, required=False)
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        label="Department"
    )
    role = forms.ChoiceField(choices=[
        ('Doctor', 'Doctor'),
        ('Patient', 'Patient')
    ])

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'gender', 'specialization',
                  'department', 'is_staff', 'is_active', 'role']

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        if self.instance.pk and hasattr(self.instance, 'userpermission'):
            self.fields['role'].initial = self.instance.userpermission.role
            if self.instance.userpermission.role == 'Patient' and hasattr(self.instance, 'patient'):
                self.fields['phone_number'].initial = self.instance.patient.phone_number
                self.fields['gender'].initial = self.instance.patient.gender
            elif self.instance.userpermission.role == 'Doctor' and hasattr(self.instance, 'doctor'):
                self.fields['phone_number'].initial = self.instance.doctor.phone_number
                self.fields['specialization'].initial = self.instance.doctor.specialization
                self.fields['department'].initial = self.instance.doctor.department


class CustomUserCreationForm(UserCreationForm):
    phone_number = forms.CharField(max_length=15, required=False)
    gender = forms.ChoiceField(choices=[('Male', 'Male'), ('Female', 'Female')], required=False)
    specialization = forms.CharField(max_length=100, required=False)
    department = forms.ModelChoiceField(queryset=Department.objects.all(), required=False, label="Department")
    role = forms.ChoiceField(choices=[
        ('Doctor', 'Doctor'),
        ('Patient', 'Patient')
    ])

    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 'phone_number',
            'specialization', 'department', 'password1', 'password2', 'role',
            'is_staff', 'is_active'
        ]


# Form for e-prescribing
class EPrescriptionForm(forms.ModelForm):
    class Meta:
        model = EPrescription
        fields = ['medication', 'dosage', 'instructions']


# Optional form for health resource creation if needed
class HealthResourceForm(forms.ModelForm):
    class Meta:
        model = HealthResource
        fields = ['name', 'description', 'link']


class DoctorLoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'location', 'overview']
