from django.urls import path
from slots.api.views import slot_delete, slot_list, slot_create, slot_detail, slot_update

urlpatterns = [
    path('<int:doctor_id>', slot_list, name='slot_list'),
    path('create', slot_create, name='slot_create'),
    path('<int:slot_id>/details', slot_detail, name='slot_detail'),
    path('<int:slot_id>/update', slot_update, name='slot_update'),
    path('<int:slot_id>/delete', slot_delete, name='slot_delete'),
]