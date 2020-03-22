from django.utils.timezone import datetime,timedelta
from django import template
from django.utils.safestring import mark_safe
from django.core.exceptions import FieldDoesNotExist

register = template.Library()


@register.simple_tag()
def render_enroll_contract(enroll_obj):

    return enroll_obj.enrolled_class.contract.template.format(course_name=enroll_obj.enrolled_class, stu_name=enroll_obj.customer.qq)