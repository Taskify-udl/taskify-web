from django import template

from taskify_app.utils.i18n import t as translate_func

register = template.Library()


@register.simple_tag(takes_context=True, name="t")
def translate_tag(context, key: str):
    """
    Uso:
        {% load json_i18n %}
        {% t "nav_profile" %}
    """
    request = context.get("request", None)
    lang = "es"
    if request is not None:
        lang = request.session.get("lang", "es")

    return translate_func(key, lang)
