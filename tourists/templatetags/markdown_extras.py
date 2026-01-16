import markdown
from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
@stringfilter
def convert_markdown(value):
    # This converts Gemini's raw markdown into clean HTML tags
    return markdown.markdown(value, extensions=['fenced_code', 'tables'])