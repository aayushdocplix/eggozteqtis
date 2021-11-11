import base64
import json
import time
from datetime import datetime, timedelta

import requests
from django.core.mail import send_mail
from django.views.generic import TemplateView
from rest_framework import viewsets, permissions, decorators

from Eggoz import settings
from Eggoz.settings import FROM_EMAIL, IOT_KEY
from base.response import BadRequest, Created, Ok, Response
from rest_framework.filters import BaseFilterBackend
import coreapi

from pyfcm import FCMNotification
from Eggoz.settings import FCM_SERVER_KEY
from custom_auth.models.User import FcmToken

from farmer.models import Farmer


class IndexView(TemplateView):
    template_name = 'custom_auth/home.html'


class FarmerHelpViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user = request.user
        sender_name = request.data.get("name", None)
        if sender_name is None:
            if not user.is_anonymous:
                sender_name = request.user.name
            else:
                return BadRequest({'error_type': "ValidationError",
                                   'errors': [{'message': "name required"}]})
        farmer = Farmer.objects.filter(farmer=user).first()
        if farmer:
            farmer_id = farmer.id
        else:
            farmer_id = None
        message = request.data.get("message", None)
        if message is None:
            return BadRequest({'error_type': "ValidationError",
                               'errors': [{'message': "message required"}]})
        contact_eggoz_msg_body = {
            "subject": "Farmer Help",
            "body": "Farmer Name:- " + user.name + "\nFarmer Id:-" + str(farmer_id) + "\nMessage:-" + message
        }
        send_mail(contact_eggoz_msg_body.get('subject'), contact_eggoz_msg_body.get('body'), FROM_EMAIL,
                  ['info@eggoz.in'])
        return Created({"success": "help message send successfully"})


class FarmerConsultingViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user = request.user
        sender_name = request.data.get("name", None)
        if sender_name is None:
            if not user.is_anonymous:
                sender_name = request.user.name
            else:
                return BadRequest({'error_type': "ValidationError",
                                   'errors': [{'message': "name required"}]})
        farmer = Farmer.objects.filter(farmer=user).first()
        if farmer:
            farmer_id = farmer.id
        else:
            farmer_id = None
        issue_title = request.data.get("issue_title", None)
        if issue_title is None:
            return BadRequest({'error_type': "ValidationError",
                               'errors': [{'message': "issue_title required"}]})
        issue = request.data.get("issue", None)
        if issue is None:
            return BadRequest({'error_type': "ValidationError",
                               'errors': [{'message': "issue required"}]})
        email_body = "Farmer Name:- " + sender_name + "\nFarmer Id:-" + str(farmer_id) + "\nIssue Title:-" + str(
            issue_title) + "\nissue:-" + str(issue)
        contact_eggoz_msg_body = {
            "subject": "Farmer Issue",
            "body": email_body
        }
        send_mail(contact_eggoz_msg_body.get('subject'), contact_eggoz_msg_body.get('body'), FROM_EMAIL,
                  ['contact@eggoz.in', 'info@eggoz.in'])
        return Created({"success": "issue send successfully"})


class FarmerIotEnquiryViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user = request.user
        farmer = Farmer.objects.filter(farmer=user).first()
        if farmer:
            farmer_id = farmer.id
        else:
            farmer_id = None
        issue_title = request.data.get("title", None)
        if issue_title is None:
            return BadRequest({'error_type': "ValidationError",
                               'errors': [{'message': "title required"}]})
        issue = request.data.get("message", None)
        if issue is None:
            return BadRequest({'error_type': "ValidationError",
                               'errors': [{'message': "message required"}]})
        email_body = "Farmer Name:- " + user.name + "\nFarmer Id:-" + str(farmer_id) + "\nIssue Title:-" + str(
            issue_title) + "\nissue:-" + str(issue)
        contact_eggoz_msg_body = {
            "subject": "IOT Enquiry",
            "body": email_body
        }
        send_mail(contact_eggoz_msg_body.get('subject'), contact_eggoz_msg_body.get('body'), FROM_EMAIL,
                  ['info@eggoz.in'])
        return Created({"success": "Iot Enquiry Submitted successfully"})


class WordpressViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        language = request.GET.get('language', 'English')
        if language == 'English':
            url = "https://blogs.eggoz.in/?rest_route=/wp/v2/posts&categories=62"
        else:
            url = "https://blogs.eggoz.in/?rest_route=/wp/v2/posts&categories=63"

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
                               "description": result["excerpt"]["rendered"],
                               "image_url": result["better_featured_image"]["source_url"]}

                results_dict["results"].append(result_dict)
            # return Ok({"results": json.loads(response.text)})
            return Ok({"results": results_dict})
        else:
            return BadRequest({'error_type': "WordPressError",
                               'errors': [{'message': "wordpress error"}]})


class SimpleFilterBackend(BaseFilterBackend):
    def get_schema_fields(self, view):
        return [coreapi.Field(
            name='lat',
            location='query',
            required=True,
            type='float'
        ),
            coreapi.Field(
                name='lon',
                location='query',
                required=True,
                type='float'
            )]


class PinCodeFilterBackend(BaseFilterBackend):
    def get_schema_fields(self, view):
        return [coreapi.Field(
            name='pincode',
            location='query',
            required=True,
            type='int'
        )]


class WeatherMapViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = (SimpleFilterBackend,)

    def list(self, request, *args, **kwargs):
        print(request.GET)
        lat = str(request.GET.get("lat", ""))
        lon = str(request.GET.get("lon", ""))
        url = "http://api.openweathermap.org/data/2.5/weather?lat={}&lon={}&appid={}".format(
            lat, lon, settings.WEATHER_API)
        response = requests.get(url).json()
        if response:
            if response['cod'] == 200:
                return Ok({"results": response})
            else:
                return BadRequest({'error_type': response['message'],
                                   'errors': [{'code': response['cod']}]})
        else:
            return BadRequest({'error_type': "Weather Error",
                               'errors': [{'code': "Weather Error"}]})


class PinWeatherMapViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = (PinCodeFilterBackend,)

    def list(self, request, *args, **kwargs):
        print(request.GET)
        zip = str(request.GET.get("pincode", ""))
        url = "https://api.openweathermap.org/data/2.5/weather?zip={},IN&appid={}".format(
            zip, settings.WEATHER_API)
        response = requests.get(url).json()
        if response:
            if response['cod'] == 200:
                return Ok({"results": response})
            else:
                return BadRequest({'error_type': response['message'],
                                   'errors': [{'code': response['cod']}]})
        else:
            return BadRequest({'error_type': "Weather Error",
                               'errors': [{'code': "Weather Error"}]})


class NotificationViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @decorators.action(detail=False, methods=['post'], url_path="send_notification")
    def send_notification(self, request, *args, **kwargs):
        try:
            data = request.data
            print(data)
            user_ids = request.data.get('user_ids', None)
            title = request.data.get('title', "title")
            message = request.data.get('message', "message")
            data = request.data.get('data', {"title": title, "body": message, "image_url": "image_url",
                                             "activity_id": 1, "item_id": 1})
            push_service = FCMNotification(api_key=FCM_SERVER_KEY)
            fcm_token = []
            if user_ids:
                if FcmToken.objects.filter(user_id__in=user_ids):
                    tokens = FcmToken.objects.filter(user_id__in=user_ids)
                    for token in tokens:
                        fcm_token.append(token.token)
            else:
                tokens = FcmToken.objects.all()
                for token in tokens:
                    fcm_token.append(token.token)
            result = push_service.notify_multiple_devices(
                registration_ids=fcm_token, data_message=data)
            return Response({"results": result})

        except Exception as e:
            print(e.args)

    @decorators.action(detail=False, methods=['post'], url_path="send_single_notification")
    def send_single_notification(self, request, *args, **kwargs):
        data = request.data
        print(data)
        user_id = request.data.get('user_id', 1)
        title = request.data.get('title', "title")
        message = request.data.get('message', "message")
        data = request.data.get('data', {"title": title, "body": message, "image_url": "image_url",
                                         "activity_id": 1, "item_id": 1})
        try:
            if FcmToken.objects.filter(user_id=user_id):
                registration_id = FcmToken.objects.get(user_id=user_id).token
                push_service = FCMNotification(api_key=FCM_SERVER_KEY)
                result = push_service.notify_single_device(registration_id=registration_id, data_message=data)
                return Response({"results": result})
            else:
                return BadRequest({'error_type': "ValidationError",
                                   'errors': [{'message': "Users Do not have Devices"}]})

        except Exception as e:
            print(e.args)


class IotViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @decorators.action(detail=False, methods=['get'], url_path="historic_data")
    def historic_data(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        if user:
            pattern = '%d-%m-%Y %H:%M:%S'
            from_date = request.GET.get('from_date')
            to_date = request.GET.get('to_date')
            device_id = request.GET.get('device_id')
            epoch_from = int(time.mktime(time.strptime(from_date, pattern))) * 1000
            epoch_to = int(time.mktime(time.strptime(to_date, pattern))) * 1000
            print(epoch_from)
            print(epoch_to)

            url = "https://bk9ohdsb8d.execute-api.us-east-2.amazonaws.com/poultryGetData?device_id={}&start_epoch={}&final_epoch={}".format(
                device_id, epoch_from, epoch_to)
            response = requests.get(url, headers={"Authorization": settings.IOT_KEY})
            return Response(response.json())
        else:
            return BadRequest({'error_type': "ValidationError",
                               'errors': [{'message': "User Not Logged in"}]})

    @decorators.action(detail=False, methods=['get'], url_path="current_data")
    def current_data(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        if user:

            device_id = request.GET.get('device_id')
            # registration_id = request.GET.get('fcm_token')
            shedDataList = []
            feedDataList = []
            waterDataList = []
            bioSecurityList = []
            message = ""
            title = ""
            url = "https://l2kre966we.execute-api.us-east-2.amazonaws.com/poultryCurrentData?device_id={}".format(
                device_id)
            response = requests.get(url, headers={"Authorization": settings.IOT_KEY}).json()
            if response:
                if response['temperature'] < 17:
                    shedDataList.append("Close all the curtains to protect birds from outside chilled winds.")
                    shedDataList.append("For ventilation Vents should be placed towards the roof of the shed,"
                                        " where the cold air isn’t able to flow directly onto your birds.")
                    shedDataList.append("For chicks use Gas or electric brooder in grower shed.")
                    shedDataList.append("For chicks Increase bedding material in grower floor to comfort chicks "
                                        "in harsh conditions.")




                    waterDataList.append("Water must be fresh and clean. If water is cold enough, then it should be "
                                         "given to chicken after adding hot water to it, so that the water comes to "
                                         "normal temperature. ")
                    waterDataList.append("Water should have normal temperature.")
                    waterDataList.append("If water is cold enough, then it should be given to chiken after adding "
                                         "hot water to it, so that the water comes to normal temperature.")

                    # feedDataList.append("")
                    # bioSecurityList.append("")
                    message = "Low Temperature"
                    title = "Your shed temperature in too low please follow the given instructions"
                if response['temperature'] > 30 and response['humidity'] < 75:
                    shedDataList.append("Turn ON fogger and fans.")
                    shedDataList.append("Turn ON spriklers on the roof.")
                    shedDataList.append("Supply of plenty of clean and cool water (17-21oC).")
                    # feedDataList.append("")
                    waterDataList.append("Supply of plenty of clean and cool water (17-21oC).")
                    waterDataList.append("Provide electrolyte (1-2 gm/liter) in water during hot hours.")
                    waterDataList.append("Cover water tanks with wet gunny bags to avoid direct exposure to sun heat.")
                    # bioSecurityList.append("")
                    message = "Ideal Humidity"
                    title = "Your shed temperature is high please follow the given instructions"

                if response['temperature'] > 30 and response['humidity'] > 75:
                    shedDataList.append("Turn ON fan and raise curtains.")
                    shedDataList.append("Turn OFF fogger and sprinkler.")
                    shedDataList.append("Supply of plenty of clean and cool water (17-21oC).")

                    # feedDataList.append("")
                    waterDataList.append("Supply of plenty of clean and cool water (17-21oC).")
                    waterDataList.append("Provide electrolyte (1-2 gm/liter) in water during hot hours.")
                    waterDataList.append("Cover water tanks with wet gunny bags to avoid direct exposure to sun heat.")
                    # bioSecurityList.append("")
                    message = "High Humidity"
                    title = "Your shed temperature and humidity is high please follow the given instructions"

                if shedDataList or feedDataList or waterDataList or bioSecurityList:
                    data_body = {
                        "title": title,
                        "body": message,
                        "image_url": "image_url",
                        "activity_id": 1,
                        "item_id": 1,
                        "alertData": {
                            "shedAlerts": shedDataList,
                            "feedAlerts": feedDataList,
                            "waterAlerts": waterDataList,
                            "bioAlerts": bioSecurityList
                        },
                    }
                    if FcmToken.objects.filter(user_id=user.id):
                        registration_id = FcmToken.objects.filter(user_id=user.id).first().token

                        push_service = FCMNotification(api_key=FCM_SERVER_KEY)
                        result = push_service.notify_single_device(
                            registration_id=registration_id, data_message=data_body)

            return Response(response)
        else:
            return BadRequest({'error_type': "ValidationError",
                               'errors': [{'message': "User Not Logged in"}]})
