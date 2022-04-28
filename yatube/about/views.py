from django.views.generic.base import TemplateView


class AboutAuthorView(TemplateView):
    template_name = 'about/auth.html'


class AboutTechView(TemplateView):
    template_name = 'about/tech.html'
