from django import template
from shop.models import Cart

register = template.Library()

@register.simple_tag
def cart_item_count(user):
    if user.is_authenticated:
        return Cart.objects.filter(user=user).count()
    return 0
