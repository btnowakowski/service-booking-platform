from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import (
    TemplateView,
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    FormView,
)
from django.utils import timezone

from .models import Service, TimeSlot, Reservation
from django.db.models import Q
from .forms import RegisterForm, ReservationForm


class HomeView(TemplateView):
    template_name = "home.html"


class ServiceListView(ListView):
    model = Service
    template_name = "service_list.html"

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["query"] = self.request.GET.get("q", "")
        return ctx


class ServiceDetailView(DetailView):
    model = Service
    template_name = "service_detail.html"


class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = "registration/register.html"
    success_url = reverse_lazy("booking:service_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)  # auto-login po rejestracji
        return response


class ReservationCreateView(LoginRequiredMixin, CreateView):
    model = Reservation
    form_class = ReservationForm
    template_name = "reservation_form.html"

    def get(self, request, *args, **kwargs):
        return redirect("booking:service_detail", pk=self.service.pk)

    def dispatch(self, request, *args, **kwargs):
        self.service = get_object_or_404(Service, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["service"] = self.service
        return kwargs

    def form_valid(self, form):
        slot = form.cleaned_data["slot"]

        # Slot must be in the future
        if slot.start < timezone.now():
            form.add_error("slot", "Nie możesz zarezerwować terminu w przeszłości.")
            return self.form_invalid(form)

        if Reservation.objects.filter(
            slot=slot,
            status__in=[Reservation.Status.PENDING, Reservation.Status.APPROVED],
        ).exists():
            form.add_error("slot", "Termin już zajęty.")
            return self.form_invalid(form)

        form.instance.user = self.request.user
        form.instance.service = self.service
        return super().form_valid(form)

    def get_success_url(self):
        return redirect("booking:my_reservations").url


# class MyReservationsView(LoginRequiredMixin, ListView):
#     template_name = "my_reservations.html"

#     def get_queryset(self):
#         return Reservation.objects.filter(user=self.request.user)


class MyReservationsView(LoginRequiredMixin, ListView):
    model = Reservation
    template_name = "my_reservations.html"
    context_object_name = "reservations"

    def get_queryset(self):
        qs = Reservation.objects.filter(user=self.request.user).select_related(
            "service", "slot"
        )

        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)

        service = self.request.GET.get("service")
        if service:
            qs = qs.filter(service__id=service)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["services"] = Service.objects.all()
        ctx["selected_status"] = self.request.GET.get("status", "")
        ctx["selected_service"] = self.request.GET.get("service", "")
        return ctx


class ReservationUpdateView(LoginRequiredMixin, UpdateView):
    model = Reservation
    form_class = ReservationForm
    template_name = "reservation_form.html"

    def get_queryset(self):
        return Reservation.objects.filter(user=self.request.user, status="pending")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["service"] = self.object.service
        return kwargs

    def get_success_url(self):
        return redirect("booking:my_reservations").url


class ReservationDetailView(LoginRequiredMixin, DetailView):
    model = Reservation
    template_name = "reservation_detail.html"
    context_object_name = "reservation"

    def get_queryset(self):
        # użytkownik może zobaczyć tylko swoje rezerwacje
        return Reservation.objects.filter(user=self.request.user)


def cancel_reservation(request, pk):
    res = get_object_or_404(Reservation, pk=pk, user=request.user)
    if res.slot:
        res.archived_start = res.slot.start
        res.archived_end = res.slot.end
        res.slot = None
    res.status = Reservation.Status.CANCELLED
    res.save(update_fields=["status", "slot", "archived_start", "archived_end"])
    return redirect("booking:my_reservations")


def free_slots_api(request, pk):
    service = get_object_or_404(Service, pk=pk)
    qs = TimeSlot.objects.filter(
        service=service, is_active=True, start__gte=timezone.now()
    ).exclude(
        reservation__status__in=[
            Reservation.Status.PENDING,
            Reservation.Status.APPROVED,
        ]
    )
    data = [
        {"id": s.id, "start": s.start.isoformat(), "end": s.end.isoformat()} for s in qs
    ]
    return JsonResponse(data, safe=False)
