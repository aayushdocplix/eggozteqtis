from datetime import datetime
from phonenumber_field.formfields import PhoneNumberField
from django import forms
from django.forms import ModelForm, ModelChoiceField, SplitDateTimeWidget
from phonenumber_field.widgets import PhoneNumberPrefixWidget

from base.models import Cluster, City
from retailer.models import Retailer
from custom_auth.models import User


class RetailerForm(forms.ModelForm):
    name_of_shop = forms.CharField(label='Name Of The Shop',
                                   widget=forms.TextInput(attrs={'class': 'input100', 'autocomplete': 'off',
                                                                 'placeholder': 'Enter Name of the shop'}))


    category = forms.ChoiceField(choices=(('GENERAL TRADER', 'GENERAL TRADER'),
                                          ('TRADER', 'TRADER')),
                                 widget=forms.Select(attrs={'class': 'select2-selection'})
                                 )

    sub_category = forms.ChoiceField(choices=(('KIRANA SOCIETY', 'KIRANA SOCIETY'),
                                              ('PICK AND GO MARKET', 'PICK AND GO MARKET'),
                                              ('KIRANA MARKET', 'KIRANA MARKET'),
                                              ('PICK AND GO SOCIETY', 'PICK AND GO SOCIETY'),
                                              ('SUPERMARKET', 'SUPERMARKET'),
                                              ('B2B', 'B2B'),
                                              ('', '---Select a Sub Category---')),
                                     widget=forms.Select(attrs={'class': 'select2-selection'})
                                     )

    code = forms.CharField(label='Code',
                           widget=forms.TextInput(attrs={'class': 'input100', 'autocomplete': 'off',
                                                         'placeholder': 'Enter Code'}))

    city = ModelChoiceField(queryset=City.objects.all(), empty_label='---Select a City---', required=True,
                            widget=forms.Select(attrs={'class': 'select2-selection'}))

    cluster = ModelChoiceField(queryset=Cluster.objects.none(), empty_label='-------', required=True,
                               widget=forms.Select(attrs={'class': 'select2-selection'}))

    sales_person = ModelChoiceField(queryset=User.objects.none(), empty_label='---Select a Sales Person---',
                                    required=True,
                                    widget=forms.Select(attrs={'class': 'select2-selection'}))
    onboarding_status = forms.ChoiceField(choices=(('Onboarded', 'Onboarded'),
                                                   ('Cold', 'Cold'),
                                                   ('Pending Interested', 'Pending Interested')),
                                          widget=forms.Select(attrs={'class': 'select2-selection'})
                                          )
    onboarding_date = forms.DateTimeField(widget=forms.SelectDateWidget)

    # last_order_date = forms.DateTimeField(widget=forms.SelectDateWidget)
    address = forms.CharField(label='Address',
                              widget=forms.TextInput(attrs={'class': 'input100', 'autocomplete': 'off',
                                                            'placeholder': 'Enter Address'}))
    # phone_no = forms.RegexField(regex=r'^\d{10,10}$', required=True,
    #                             widget=forms.TextInput(attrs={'class': 'input100', 'autocomplete': 'off',
    #                                                           'placeholder': 'Enter Phone No'}),
    #                             error_messages={'unique': "This mobile no has already been registered."})

    phone_no = PhoneNumberField(widget=PhoneNumberPrefixWidget(
        attrs={'placeholder': 'Enter Phone Number', 'class': "form-control mb-p"},
        initial='IN'))

    class Meta:
        model = Retailer
        exclude = ('last_order_date',)

    def __init__(self, *args, **kwargs):
        super(RetailerForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        retailer = super(RetailerForm, self).save(commit=False)
        retailer.name_of_shop = self.cleaned_data['name_of_shop']
        retailer.category = self.cleaned_data['category']
        retailer.sub_category = self.cleaned_data['sub_category']
        retailer.code = self.cleaned_data['code']
        retailer.city = self.cleaned_data['city']
        retailer.cluster = self.cleaned_data['cluster']
        retailer.sales_person = self.cleaned_data['sales_person']
        retailer.onboarding_status = self.cleaned_data['onboarding_status']
        retailer.onboarding_date = self.cleaned_data['onboarding_date']
        # retailer.last_order_date = self.cleaned_data['onboarding_date']
        retailer.address = self.cleaned_data['address']
        retailer.phone_no = self.cleaned_data['phone_no']
        if commit:
            retailer.save()
        return retailer
