import base64
import json

import requests
from django.views.generic import TemplateView
from django_filters import rest_framework as filters
from rest_framework import viewsets, permissions

from base.response import BadRequest, Created, Ok
from custom_auth.models import Address, Department, UserProfile
from ecommerce.api.serializers import CustomerSerializer, CustomerCreateSerializer
from ecommerce.models.Customer import Customer


class IndexView(TemplateView):
    template_name = 'custom_auth/home.html'


class CustomerViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = CustomerSerializer
    queryset = Customer.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('user',)

    def create(self, request, *args, **kwargs):
        data = request.data
        user = request.user
        print(request.data)
        serializer = CustomerCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if request.user.id == data.get('user'):
            if Customer.objects.filter(user_id=data.get('user')):
                customer = Customer.objects.filter(user_id=data.get('user')).first()
                user.name = data.get('name', user.name)
                user.email = data.get('email', user.email)
                user.phone_no = data.get('phone_no', user.phone_no)
                if user.default_address:
                    address = Address.objects.get(pk=user.default_address.id)
                    address.pinCode = data.get('pinCode', user.default_address.pinCode)
                    address.save()
                user.save()
                return Created(CustomerSerializer(customer).data)
            else:
                customer, customer_created = Customer.objects.get_or_create(user_id=data.get('user'))
                if customer_created:
                    department, department_created = Department.objects.get_or_create(name="Customer")
                    customer_user_profile, customer_user_profile_created = UserProfile.objects.get_or_create(user=user)
                    customer_user_profile.department.add(department)
                    customer_user_profile.save()
                    user.name = data.get('name', user.name)
                    user.email = data.get('email', user.email)
                    user.phone_no = data.get('phone_no', user.phone_no)
                    if user.default_address:
                        address = Address.objects.get(pk=user.default_address.id)
                        address.pinCode = data.get('pinCode', user.default_address.pinCode)
                        address.save()
                    user.save()
                else:
                    return BadRequest({'error_type': "ValidationError",
                                       'errors': [{'message': "All ready Created customer"}]})
                return Created(CustomerSerializer(customer).data)
        else:
            return BadRequest({'error_type': "ValidationError",
                               'errors': [{'message': "user(customer) id invalid"}]})


class EcommerceWordpressViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.AllowAny]

    def list(self, request, *args, **kwargs):
        url = "http://blogs.eggoz.in/?rest_route=/wp/v2/posts&categories=4,3"
        user = "eggoz"
        password = "TjwH JmpO DqcA eHDn LB9x MC5A"
        credentials = user + ':' + password
        token = base64.b64encode(credentials.encode())
        header = {'Authorization': 'Basic ' + token.decode('utf-8')}
        print(header)
        response = requests.get(url, headers=header)
        if response.status_code == 200:
            results = json.loads(response.text)
            results_dict = {}
            results_dict["results"] = []
            for index, result in enumerate(results):
                result_dict = {"id": result["id"], "link": result["link"], "title": result["title"]["rendered"],
                               "date": result["date"],
                               "description": result["excerpt"]["rendered"],
                               "image_url": result["better_featured_image"]["source_url"],
                               "alt_text": result["better_featured_image"]["alt_text"]}

                results_dict["results"].append(result_dict)
            # return Ok({"results": json.loads(response.text)})
            return Ok({"results": results_dict})
        else:
            return BadRequest({'error_type': "WordPressError",
                               'errors': [{'message': "wordpress error"}]})
