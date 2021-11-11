from django.urls import reverse_lazy
from django.views import generic
from django.views.generic import TemplateView
from custom_auth.forms import RegistrationForm


class IndexView(TemplateView):
    template_name = 'custom_auth/home.html'


class SignupView(generic.FormView):
    template_name = 'custom_auth/register.html'
    form_class = RegistrationForm
    success_url = reverse_lazy('base:add-retail')

    def form_valid(self, form):
        form.save()
        return super(SignupView, self).form_valid(form)
