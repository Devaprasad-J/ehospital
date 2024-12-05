from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.db.models.signals import post_save
from django.dispatch import receiver


# Patient Module Models
class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, related_name="patient")  # Link to User model
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female')])

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, related_name="doctor")
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15)
    specialization = models.CharField(max_length=100)
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='doctors')

    def __str__(self):
        return f"Dr. {self.first_name} {self.last_name}"


class Appointment(models.Model):
    patient = models.ForeignKey('Patient', on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    date = models.DateTimeField()
    reason = models.TextField()  # Reason for appointment
    status = models.CharField(
        max_length=20,
        choices=[
            ('Scheduled', 'Scheduled'),
            ('Completed', 'Completed'),
            ('Cancelled', 'Cancelled')
        ],
        default='Scheduled',
    )
    billing = models.OneToOneField('Billing', on_delete=models.CASCADE, null=True, blank=True, related_name='appointment_billing')

    def __str__(self):
        return f"{self.patient.user.username} with {self.doctor.user.username} on {self.date}"


class Billing(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='billing_appointment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, choices=[
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
    ], default='Pending')
    payment_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Billing for {self.appointment.patient.user.username} on {self.payment_date}"


class MedicalHistory(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="medical_history")
    diagnosis = models.TextField()
    treatment_plan = models.TextField()
    medication = models.CharField(max_length=255)
    notes = models.TextField(blank=True, null=True)
    date_prescribed = models.DateField()

    def __str__(self):
        return f"Medical History of {self.patient.user.username}"


class TreatmentPlan(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    diagnosis = models.TextField()
    treatment = models.TextField()
    prescribed_medication = models.CharField(max_length=255)

    def __str__(self):
        return f"Treatment plan for {self.patient.user.username}"


class EPrescription(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    medication = models.CharField(max_length=255)
    dosage = models.CharField(max_length=100)
    instructions = models.TextField()
    date_prescribed = models.DateTimeField(default=now)

    def __str__(self):
        return f"Prescription for {self.patient.user.username} by Dr. {self.doctor.user.username}"


class HealthResource(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    link = models.URLField()  # Add this line if missing

    def __str__(self):
        return self.name


# Admin Module Models
class Facility(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    description = models.TextField()  # Ensure this field exists

    def __str__(self):
        return self.name


class UserPermission(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)
    role = models.CharField(max_length=50, choices=[
        ('Admin', 'Admin'),
        ('Doctor', 'Doctor'),
        ('Patient', 'Patient')
    ])

    def __str__(self):
        return f"{self.user.username} - {self.role}"


class Location(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Department(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    overview = models.TextField(default="Overview not available")  # Add this line

    def __str__(self):
        return self.name



