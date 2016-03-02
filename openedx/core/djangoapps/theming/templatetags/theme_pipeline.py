"""
Theme aware pipeline template tags.
"""

from django import template
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from pipeline.templatetags.pipeline import StylesheetNode, JavascriptNode
from pipeline.utils import guess_type

from openedx.core.djangoapps.theming.helpers import get_static_file_url

register = template.Library()


class ThemeStylesheetNode(StylesheetNode):
    """
    Overrides StyleSheetNode from django pipeline so that stylesheets are served based on the applied theme.
    """
    def render_css(self, package, path):
        """
        Override render_css from django-pipline so that stylesheets urls are based on the applied theme
        """
        template_name = package.template_name or "pipeline/css.html"
        context = package.extra_context
        context.update({
            'type': guess_type(path, 'text/css'),
            'url': mark_safe(get_static_file_url(path))
        })
        return render_to_string(template_name, context)


class ThemeJavascriptNode(JavascriptNode):
    """
    Overrides JavascriptNode from django pipeline so that js files are served based on the applied theme.
    """
    def render_js(self, package, path):
        """
        Override render_js from django-pipline so that js file urls are based on the applied theme
        """
        template_name = package.template_name or "pipeline/js.html"
        context = package.extra_context
        context.update({
            'type': guess_type(path, 'text/javascript'),
            'url': mark_safe(get_static_file_url(path))
        })
        return render_to_string(template_name, context)


@register.tag
def stylesheet(parser, token):
    """
    Template tag to serve stylesheets from django-pipeline. This definition uses the theming aware ThemeStyleSheetNode.
    """
    try:
        tag_name, name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            '%r requires exactly one argument: the name of a group in the PIPELINE_CSS setting' %
            token.split_contents()[0]
        )
    return ThemeStylesheetNode(name)


@register.tag
def javascript(parser, token):
    """
    Template tag to serve javascript from django-pipeline. This definition uses the theming aware ThemeJavascriptNode.
    """
    try:
        tag_name, name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            '%r requires exactly one argument: the name of a group in the PIPELINE_JS setting' %
            token.split_contents()[0]
        )
    return ThemeJavascriptNode(name)
