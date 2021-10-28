from django import template
register = template.Library()

from ..models import Search

@register.tag(name="recent_searches")
class RecentSearches(template.Node):
    def __init__(self, *args, **kwargs):
        super().__init__()
    def render(self, context):
        user = context['request'].user
        context['recent_searches'] = Search.objects.filter(user=user).order_by('-timestamp')[:5]
        return ''
