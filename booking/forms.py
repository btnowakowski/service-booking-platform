from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Reservation, Service, TimeSlot


from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label="Email",
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2")
        labels = {
            "username": "Nazwa użytkownika",
        }
        help_texts = {
            "username": "Wymagane. Maks. 150 znaków. Litery, cyfry oraz @/./+/-/_",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # bootstrap + placeholdery + polskie etykiety
        for name, field in self.fields.items():
            if not field.widget.attrs.get("class"):
                field.widget.attrs["class"] = "form-control"
            field.widget.attrs["placeholder"] = field.label

        self.fields["password1"].label = "Hasło"
        self.fields["password2"].label = "Powtórz hasło"

        # czytelniejsze help_texty
        self.fields["password1"].help_text = (
            "<ul class='small mb-0'>"
            "<li>Minimum 8 znaków.</li>"
            "<li>Nie może być zbyt podobne do nazwy/emaila.</li>"
            "<li>Nie może być popularnym hasłem.</li>"
            "<li>Nie może składać się tylko z cyfr.</li>"
            "</ul>"
        )

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Ten email jest już zajęty.")
        return email


class CustomAuthForm(AuthenticationForm):
    username = forms.CharField(
        label="Nazwa użytkownika",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Nazwa użytkownika"}
        ),
    )
    password = forms.CharField(
        label="Hasło",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Hasło"}
        ),
    )


class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ["slot"]

    def __init__(self, *args, **kwargs):
        service = kwargs.pop("service", None)
        super().__init__(*args, **kwargs)

        if service:
            self.fields["slot"].queryset = TimeSlot.objects.filter(
                service=service, is_active=True
            ).exclude(reservation__isnull=False)


class ServiceAdminForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ["name", "description", "price", "slot_duration"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "slot_duration": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "15",
                    "step": "15",
                    "value": "30",
                }
            ),
        }
        labels = {
            "name": "Nazwa",
            "description": "Opis",
            "price": "Cena (zł)",
            "slot_duration": "Długość slotu (minuty)",
        }


from datetime import datetime, timedelta
from django.utils import timezone


class SlotAdminForm(forms.ModelForm):
    slot_date = forms.DateField(
        label="Data",
        widget=forms.DateInput(
            attrs={
                "class": "form-control",
                "type": "date",
                "id": "id_slot_date",
            }
        ),
        required=True,
    )
    generated_slots = forms.CharField(
        label="Wygenerowane sloty",
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-select",
                "id": "id_generated_slots",
                "readonly": "readonly",
                "style": "display: none;",
            }
        ),
    )
    # Dodaj ukryte pola dla start i end
    start = forms.DateTimeField(required=False, widget=forms.HiddenInput())
    end = forms.DateTimeField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = TimeSlot
        fields = ["service", "is_active"]
        widgets = {
            "service": forms.Select(
                attrs={"class": "form-select", "id": "id_service_select"}
            ),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["generated_slots"].required = False
        self.fields["start"].required = False
        self.fields["end"].required = False

        # If editing an existing instance, pre-fill the fields
        if self.instance and self.instance.pk:
            # Set slot_date
            self.fields["slot_date"].initial = self.instance.start.date()

            # Set generated_slots
            if self.instance.start and self.instance.end:
                self.fields["generated_slots"].initial = (
                    f"{self.instance.start.isoformat()}|{self.instance.end.isoformat()}"
                )

            # Set hidden start and end fields
            self.fields["start"].initial = self.instance.start
            self.fields["end"].initial = self.instance.end

    def clean(self):
        cleaned_data = super().clean()
        generated_slot = cleaned_data.get("generated_slots")
        slot_date = cleaned_data.get("slot_date")
        service = cleaned_data.get("service")

        if not service:
            raise forms.ValidationError("Musisz wybrać usługę.")

        if not slot_date:
            raise forms.ValidationError("Musisz wybrać datę.")

        if not generated_slot:
            raise forms.ValidationError("Musisz wybrać slot.")

        # Validate that slot_date is in the future
        if slot_date < timezone.now().date():
            raise forms.ValidationError("Data musi być w przyszłości.")

        try:
            start_str, end_str = generated_slot.split("|")

            # Parse the datetimes
            start = datetime.fromisoformat(start_str)
            end = datetime.fromisoformat(end_str)

            # If datetimes are naive, make them aware
            if start.tzinfo is None:
                start = timezone.make_aware(start)
            if end.tzinfo is None:
                end = timezone.make_aware(end)

            # Make sure the slot is free
            if TimeSlot.objects.filter(service=service, start=start, end=end).exists():
                raise forms.ValidationError("Ten slot już istnieje dla tej usługi.")

            cleaned_data["start"] = start
            cleaned_data["end"] = end

        except ValueError as e:
            raise forms.ValidationError(f"Nieprawidłowy format slotu: {e}")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.start = self.cleaned_data.get("start")
        instance.end = self.cleaned_data.get("end")
        if commit:
            instance.save()
        return instance
