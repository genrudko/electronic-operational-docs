from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from .models import EnergySite, EquipmentAsset, EquipmentType
from .services import (
    active_aliases,
    build_site_tree,
    dispatcher_name_on,
    equipment_registry_rows,
    name_history_rows,
    require_equipment_employee,
    search_equipment,
)


@login_required
def registry(request: HttpRequest) -> HttpResponse:
    employee = require_equipment_employee(request.user)
    query = request.GET.get("q", "").strip()
    site_code = request.GET.get("site", "").strip()
    type_code = request.GET.get("type", "").strip()
    assets = search_equipment(
        organization=employee.organization,
        query=query,
        site_code=site_code,
        type_code=type_code,
    )
    sites = EnergySite.objects.filter(
        organization=employee.organization,
        is_active=True,
    ).order_by("name")
    types = EquipmentType.objects.filter(
        equipment_assets__organization=employee.organization,
        is_active=True,
    ).distinct().order_by("name")
    return render(
        request,
        "equipment/registry.html",
        {
            "employee": employee,
            "rows": equipment_registry_rows(assets),
            "sites": sites,
            "types": types,
            "query": query,
            "selected_site": site_code,
            "selected_type": type_code,
            "asset_count": assets.count(),
        },
    )


@login_required
def site_detail(request: HttpRequest, code: str) -> HttpResponse:
    employee = require_equipment_employee(request.user)
    site = get_object_or_404(
        EnergySite,
        organization=employee.organization,
        code=code,
    )
    return render(
        request,
        "equipment/site_detail.html",
        {
            "site": site,
            "tree_rows": build_site_tree(site),
        },
    )


@login_required
def equipment_detail(request: HttpRequest, public_id) -> HttpResponse:
    employee = require_equipment_employee(request.user)
    equipment = get_object_or_404(
        EquipmentAsset.objects.select_related(
            "organization",
            "site",
            "equipment_type",
            "parent",
        ),
        organization=employee.organization,
        public_id=public_id,
    )
    children = equipment.children.select_related(
        "equipment_type",
        "site",
    ).order_by("code")
    outgoing = equipment.outgoing_equipment_relations.select_related(
        "target_equipment__equipment_type",
        "target_equipment__site",
    ).order_by("relation_type", "target_equipment__code")
    incoming = equipment.incoming_equipment_relations.select_related(
        "source_equipment__equipment_type",
        "source_equipment__site",
    ).order_by("relation_type", "source_equipment__code")
    return render(
        request,
        "equipment/detail.html",
        {
            "equipment": equipment,
            "dispatcher_name": dispatcher_name_on(equipment),
            "name_history": name_history_rows(equipment),
            "aliases": active_aliases(equipment),
            "children": children,
            "outgoing_relations": outgoing,
            "incoming_relations": incoming,
        },
    )
