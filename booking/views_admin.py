from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.generic import (
    TemplateView,
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.urls import reverse_lazy

from .models import Service, TimeSlot, Reservation
from .utils.permissions import admin_required
from .forms import ServiceAdminForm, SlotAdminForm


from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta
import json
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib import messages


@method_decorator(admin_required, name="dispatch")
class AdminDashboardView(TemplateView):
    template_name = "admin/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # zwykłe statystyki
        ctx["stats"] = {
            "all": Reservation.objects.count(),
            "pending": Reservation.objects.filter(status="pending").count(),
            "approved": Reservation.objects.filter(status="approved").count(),
            "cancelled": Reservation.objects.filter(status="cancelled").count(),
            "rejected": Reservation.objects.filter(status="rejected").count(),
            "services": Service.objects.count(),
            "slots_active": TimeSlot.objects.filter(is_active=True).count(),
        }

        # pending do tabeli na dole dashboardu
        ctx["pending"] = Reservation.objects.filter(status="pending").select_related(
            "user", "service", "slot"
        )

        # ---- WYKRES 1: REZERWACJE WG STATUSU ----
        status_labels = ["Oczekujące", "Zatwierdzone", "Anulowane", "Odrzucone"]
        status_values = [
            ctx["stats"]["pending"],
            ctx["stats"]["approved"],
            ctx["stats"]["cancelled"],
            ctx["stats"]["rejected"],
        ]
        ctx["chart_status_labels"] = json.dumps(status_labels)
        ctx["chart_status_values"] = json.dumps(status_values)

        # ---- WYKRES 2: OSTATNIE 14 DNI ----
        since = timezone.now().date() - timedelta(days=13)

        daily_qs = (
            Reservation.objects.filter(created_at__date__gte=since)
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(c=Count("id"))
            .order_by("day")
        )

        # pełna lista dni (żeby wykres był ciągły)
        days = [since + timedelta(days=i) for i in range(14)]
        daily_map = {x["day"]: x["c"] for x in daily_qs}

        ctx["chart_daily_labels"] = json.dumps([d.strftime("%d.%m") for d in days])
        ctx["chart_daily_values"] = json.dumps([daily_map.get(d, 0) for d in days])

        return ctx


@admin_required
def approve_reservation(request, pk):
    r = get_object_or_404(Reservation, pk=pk)
    r.status = Reservation.Status.APPROVED
    r.save(update_fields=["status"])
    return redirect("booking:admin_dashboard")


@admin_required
def reject_reservation(request, pk):
    r = get_object_or_404(Reservation, pk=pk)
    if r.slot:
        r.archived_start = r.slot.start
        r.archived_end = r.slot.end
        r.slot = None
    r.status = Reservation.Status.REJECTED
    r.save(update_fields=["status", "slot", "archived_start", "archived_end"])
    return redirect("booking:admin_dashboard")


@method_decorator(admin_required, name="dispatch")
class ServiceAdminList(ListView):
    model = Service
    template_name = "admin/service_list.html"


@method_decorator(admin_required, name="dispatch")
class ServiceAdminCreate(CreateView):
    model = Service
    form_class = ServiceAdminForm
    template_name = "admin/service_form.html"
    success_url = reverse_lazy("booking:admin_services")


@method_decorator(admin_required, name="dispatch")
class ServiceAdminUpdate(UpdateView):
    model = Service
    form_class = ServiceAdminForm
    template_name = "admin/service_form.html"
    success_url = reverse_lazy("booking:admin_services")


@method_decorator(admin_required, name="dispatch")
class ServiceAdminDelete(DeleteView):
    model = Service
    template_name = "admin/service_confirm_delete.html"
    success_url = reverse_lazy("booking:admin_services")


@method_decorator(admin_required, name="dispatch")
class SlotAdminList(ListView):
    model = TimeSlot
    template_name = "admin/slot_list.html"


@method_decorator(admin_required, name="dispatch")
class SlotAdminCreate(CreateView):
    model = TimeSlot
    form_class = SlotAdminForm
    template_name = "admin/slot_form.html"
    success_url = reverse_lazy("booking:admin_slots")

    def form_valid(self, form):
        start = form.cleaned_data.get("start")
        end = form.cleaned_data.get("end")
        service = form.cleaned_data.get("service")

        # Finalnie, zawsze ustaw wartości
        form.instance.start = start
        form.instance.end = end
        form.instance.service = service

        response = super().form_valid(form)
        messages.success(
            self.request,
            f"✓ Termin '{self.object.service.name}' został pomyślnie utworzony!",
        )
        return response


@method_decorator(admin_required, name="dispatch")
class SlotAdminUpdate(UpdateView):
    model = TimeSlot
    form_class = SlotAdminForm
    template_name = "admin/slot_form.html"
    success_url = reverse_lazy("booking:admin_slots")

    def form_valid(self, form):
        start = form.cleaned_data.get("start")
        end = form.cleaned_data.get("end")
        service = form.cleaned_data.get("service")

        # Finalnie, zawsze ustaw wartości
        form.instance.start = start
        form.instance.end = end
        form.instance.service = service

        response = super().form_valid(form)
        messages.success(
            self.request,
            f"✓ Termin '{self.object.service.name}' został pomyślnie zaktualizowany!",
        )
        return response


@method_decorator(admin_required, name="dispatch")
class SlotAdminDelete(DeleteView):
    model = TimeSlot
    template_name = "admin/slot_confirm_delete.html"
    success_url = reverse_lazy("booking:admin_slots")


@method_decorator(admin_required, name="dispatch")
class ReservationAdminList(ListView):
    model = Reservation
    template_name = "admin/reservation_list.html"
    paginate_by = 20

    def get_queryset(self):
        return Reservation.objects.select_related("user", "service", "slot").order_by(
            "-created_at"
        )


from django.utils import timezone
from datetime import datetime, timedelta


@require_GET
@admin_required
def get_slots_for_service(request):
    """API endpoint returning available slots for a service and date."""
    service_id = request.GET.get("service_id")
    slot_date = request.GET.get("slot_date")

    if not service_id or not slot_date:
        return JsonResponse({"slots": []})

    try:
        service = Service.objects.get(id=service_id)
    except Service.DoesNotExist:
        return JsonResponse({"slots": [], "error": "Usługa nie znaleziona"}, status=404)

    try:
        # Parsuj datę
        slot_date_obj = datetime.fromisoformat(slot_date).date()
    except ValueError:
        return JsonResponse(
            {"slots": [], "error": "Nieprawidłowy format daty"}, status=400
        )

    # Twórz aware datetimes
    start_time = timezone.make_aware(
        datetime.combine(slot_date_obj, datetime.min.time()).replace(
            hour=9, minute=0, second=0, microsecond=0
        )
    )
    end_time = timezone.make_aware(
        datetime.combine(slot_date_obj, datetime.min.time()).replace(
            hour=22, minute=0, second=0, microsecond=0
        )
    )

    # Pobierz zajęte sloty
    occupied_slots = TimeSlot.objects.filter(
        service=service,
        start__date=slot_date_obj,
        is_active=True,
    ).values_list("start", "end")

    slots = []
    current = start_time

    while current + timedelta(minutes=service.slot_duration) <= end_time:
        slot_end = current + timedelta(minutes=service.slot_duration)

        # Sprawdź czy slot jest zajęty
        is_occupied = any(
            start <= current < end or start < slot_end <= end
            for start, end in occupied_slots
        )

        if not is_occupied:
            slots.append(
                {
                    "value": f"{current.isoformat()}|{slot_end.isoformat()}",
                    "label": f"{current.strftime('%H:%M')} - {slot_end.strftime('%H:%M')}",
                }
            )

        current = slot_end

    return JsonResponse({"slots": slots})
