from django.urls import path, include
from . import views
from . import views_admin


app_name = "booking"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("services/", views.ServiceListView.as_view(), name="service_list"),
    path(
        "services/<int:pk>/", views.ServiceDetailView.as_view(), name="service_detail"
    ),
    path(
        "services/<int:pk>/book/",
        views.ReservationCreateView.as_view(),
        name="reservation_create",
    ),
    path("my/", views.MyReservationsView.as_view(), name="my_reservations"),
    path(
        "my/<int:pk>/edit/",
        views.ReservationUpdateView.as_view(),
        name="reservation_edit",
    ),
    path(
        "my/<int:pk>/", views.ReservationDetailView.as_view(), name="reservation_detail"
    ),
    path("my/<int:pk>/cancel/", views.cancel_reservation, name="reservation_cancel"),
    path("api/services/<int:pk>/slots/", views.free_slots_api, name="free_slots_api"),
    path(
        "admin-panel/api/slots/",
        views_admin.get_slots_for_service,
        name="api_get_slots",
    ),
    path("accounts/register/", views.RegisterView.as_view(), name="register"),
    path(
        "admin-panel/", views_admin.AdminDashboardView.as_view(), name="admin_dashboard"
    ),
    path(
        "admin-panel/res/<int:pk>/approve/",
        views_admin.approve_reservation,
        name="admin_approve",
    ),
    path(
        "admin-panel/res/<int:pk>/reject/",
        views_admin.reject_reservation,
        name="admin_reject",
    ),
    path(
        "admin-panel/services/",
        views_admin.ServiceAdminList.as_view(),
        name="admin_services",
    ),
    path(
        "admin-panel/services/add/",
        views_admin.ServiceAdminCreate.as_view(),
        name="admin_services_add",
    ),
    path(
        "admin-panel/services/<int:pk>/edit/",
        views_admin.ServiceAdminUpdate.as_view(),
        name="admin_services_edit",
    ),
    path(
        "admin-panel/services/<int:pk>/delete/",
        views_admin.ServiceAdminDelete.as_view(),
        name="admin_services_delete",
    ),
    path("admin-panel/slots/", views_admin.SlotAdminList.as_view(), name="admin_slots"),
    path(
        "admin-panel/slots/add/",
        views_admin.SlotAdminCreate.as_view(),
        name="admin_slots_add",
    ),
    path(
        "admin-panel/slots/<int:pk>/edit/",
        views_admin.SlotAdminUpdate.as_view(),
        name="admin_slots_edit",
    ),
    path(
        "admin-panel/slots/<int:pk>/delete/",
        views_admin.SlotAdminDelete.as_view(),
        name="admin_slots_delete",
    ),
    path(
        "admin-panel/reservations/",
        views_admin.ReservationAdminList.as_view(),
        name="admin_reservations",
    ),
]
