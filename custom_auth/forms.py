from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.forms import PasswordInput
from django_countries.fields import CountryField

# from base.i18n import AddressMetaForm, get_address_form_class
from custom_auth.models import User


from phonenumbers.phonenumberutil import country_code_for_region


class RegistrationForm(UserCreationForm):
    username = forms.CharField(label='Name Of The Person',
                                   widget=forms.TextInput(attrs={'class': 'input100', 'autocomplete': 'off',
                                                                 'placeholder': 'Enter Name of the person'}))

    email = forms.EmailField(label='Email Id',max_length=254, widget=forms.TextInput(attrs={'class': 'input100', 'autocomplete': 'off',
                                                                 'placeholder': 'Enter Email of the person'}))

    street_address_1 = forms.CharField(label='Street Address 1', max_length=200, required=True,
                                 widget=forms.TextInput(attrs={'placeholder': 'Enter Street Address 1 here'}))
    strret_address_2 = forms.CharField(label='Street Address 2', max_length=200, required=True,
                                 widget=forms.TextInput(attrs={'placeholder': 'Enter Street Address 2 here'}))
    city = forms.CharField(label='City', max_length=200, required=True,
                                 widget=forms.TextInput(attrs={'placeholder': 'Enter City here'}))
    postal_code = forms.CharField(label='Postal Code', max_length=200, required=True,
                                 widget=forms.TextInput(attrs={'placeholder': 'Enter Postal Code here'}))
    country = CountryField(blank_label='(select country)')

    class Meta:
        model = User
        fields =['username', 'email', 'phone_no', 'password1', 'password2']
        exclude = ('is_staff',
                   'is_superuser', 'jwt_token_key', 'last_login', 'date_joined')

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.fields['password1'].widget = PasswordInput(attrs={'placeholder': 'Password', 'class': 'form-control'})
        self.fields['password2'].widget = PasswordInput(
            attrs={'placeholder': 'Confirm Password', 'class': 'form-control'})
        # self.fields['name'].help_text = "Use Letters, Numbers and @/./+/-/_ only. Do not use Space"
        for field in ['password1']:
            self.fields[field].help_text = "Your password can't be too similar to your Username or Email."

    def save(self, commit=True):
        user = super(RegistrationForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        user.username = self.cleaned_data['username']
        user.phone_no = self.cleaned_data['phone_no']
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.fields['password'].widget = PasswordInput(
            attrs={'placeholder': 'Password', 'class': 'form-control'})

        for field in ['username', 'password']:
            self.fields[field].help_text = None

