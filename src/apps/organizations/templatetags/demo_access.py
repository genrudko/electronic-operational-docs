from __future__ import annotations

from django import template
from django.conf import settings

from apps.organizations.demo_access import development_demo_access_presentation

register = template.Library()


@register.simple_tag
def development_demo_access():
    return development_demo_access_presentation(
        deployment_mode=settings.EOD_DEPLOYMENT_MODE,
    )
