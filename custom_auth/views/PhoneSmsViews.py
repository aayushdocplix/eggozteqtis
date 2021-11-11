import base64
import uuid
from datetime import datetime, timedelta
from random import random

import pyotp
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework_jwt.settings import api_settings

from Eggoz import settings
from Eggoz.settings import CURRENT_ZONE
from base.response import Ok, InternalServerError, BadRequest
from custom_auth.api.serializers import GenerateOtpSerializer, ValidateOtpSerializer, DummyUserRegistrationSerializer, \
    UserSerializer, CustomerCreationSerializer, UserCustomerSerializer
from custom_auth.models import PhoneModel, User, LoginStamp, Department, UserProfile, Address
from custom_auth.tasks import send_sms_message
from ecommerce.models import Customer, CustomerWallet, CustomerReferral, ReferralData


class GenerateKey:
    @staticmethod
    def return_value(phone):
        return str(phone) + str(datetime.date(datetime.now(tz=CURRENT_ZONE))) + "Some Random Secret Key"


# FOR WEBAPP
class GenerateOtpViewset(APIView):
    permission_classes = [permissions.AllowAny]

    # Get to Create a call for OTP
    @staticmethod
    def post(request):
        print(request.data)
        serializer = GenerateOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_no = serializer.validated_data.get('phone_no')
        otp_type = serializer.validated_data.get('otp_type', "onboarding")
        sender_type = serializer.validated_data.get('sender_type', "Implicit")
        sms_mode = serializer.validated_data.get('sms_mode', True)
        user = User.objects.filter(phone_no=phone_no).first()
        if user:
            return BadRequest({'error_type': "Validation Error",
                               'errors': [{'message': "Phone number exist"}]})  # False Call
        phone_model, created = PhoneModel.objects.get_or_create(
            phone_no=phone_no)  # if Mobile already exists the take this else create New One
        phone_model.counter += 1  # Update Counter At every Call
        phone_model.isVerified = False
        phone_model.save()  # Save the data
        keygen = GenerateKey()
        key = base64.b32encode(keygen.return_value(phone_no).encode())  # Key is generated
        OTP = pyotp.HOTP(key)  # HOTP Model for OTP is created

        return Ok(
            {"Result": "Otp sent successfully", "otp": OTP.at(phone_model.counter),
             "message": "To sent actual otp set phone_sms_on true"})
        # if settings.PHONE_SMS_ON and sms_mode:
        #     try:
        #         send_sms_message(msg_str=(str(OTP.at(phone_model.counter))),
        #                          phone_number=str(phone_no), sms_type="otp", otp_type=otp_type, sender_type=sender_type)
        #         return Ok({"Result": "Otp sent successfully"})
        #     except Exception as e:
        #         print(e)
        #         return InternalServerError({'error_type': "Internal Error", 'errors': [{'message': e.args[1]}]})
        # else:
        #     return Ok(
        #         {"Result": "Otp sent successfully", "otp": OTP.at(phone_model.counter),
        #          "message": "To sent actual otp set phone_sms_on true"})


# For WEBAPP
class ValidateOtpViewset(APIView):
    permission_classes = [permissions.AllowAny]

    # This Method verifies the OTP
    @staticmethod
    def post(request):
        print(request.data)
        serializer = ValidateOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_no = serializer.validated_data.get('phone_no')
        try:
            phone_model = PhoneModel.objects.get(phone_no=phone_no)
        except ObjectDoesNotExist:
            return BadRequest({'error_type': "Validation Error",
                               'errors': [{'message': "Phone number does not exist"}]})  # False Call
        time_difference = datetime.now(tz=CURRENT_ZONE) - timedelta(minutes=5)
        phone_expiry = PhoneModel.objects.filter(phone_no=phone_no, updated_at__gte=time_difference, isVerified=False)
        if len(phone_expiry) > 0:
            keygen = GenerateKey()
            key = base64.b32encode(keygen.return_value(phone_no).encode())  # Generating Key
            OTP = pyotp.HOTP(key)  # HOTP Model
            if OTP.verify(request.data["otp"], phone_model.counter):  # Verifying the OTP
                phone_model.isVerified = True
                phone_model.login_count += 1
                phone_model.save()
                LoginStamp.objects.create(phone_model=phone_model)
                user = User.objects.filter(phone_no=phone_no).first()
                if user:
                    user.is_otp_verified = True
                    user.save()
                return Ok({"success": "Successfully Verified"}, status=200)
            LoginStamp.objects.create(phone_model=phone_model, login_response="Wrong Otp")
            return BadRequest({'error_type': "Validation Error",
                               'errors': [{'message': "OTP is wrong"}]})
        else:
            LoginStamp.objects.create(phone_model=phone_model, login_response="Otp Expired")
            return BadRequest({'error_type': "Validation Error",
                               'errors': [{
                                   'message': "Otp has been expired or already verified, please request for new otp"}]})  # Otp Expire


class LoginGenerateOtpViewset(APIView):
    permission_classes = [permissions.AllowAny]

    # Get to Create a call for OTP
    @staticmethod
    def post(request):
        print(request.data)
        serializer = GenerateOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_no = serializer.validated_data.get('phone_no')
        otp_type = serializer.validated_data.get('otp_type', "login")
        sender_type = serializer.validated_data.get('sender_type', "Implicit")
        sms_mode = serializer.validated_data.get('sms_mode', True)
        hash_code = serializer.validated_data.get('hash_code', "")
        phone_model, created = PhoneModel.objects.get_or_create(
            phone_no=phone_no)  # if Mobile already exists the take this else create New One
        phone_model.counter += 1  # Update Counter At every Call
        phone_model.isVerified = False
        phone_model.save()  # Save the data
        user = User.objects.filter(phone_no=phone_no).first()
        if user:
            user.is_otp_verified = False
            user.save()
        else:
            dummy_user_serializer = DummyUserRegistrationSerializer(data=request.data)
            dummy_user_serializer.is_valid(raise_exception=True)
            dummy_user_serializer.save()
        keygen = GenerateKey()
        key = base64.b32encode(keygen.return_value(phone_no).encode())  # Key is generated
        OTP = pyotp.HOTP(key)  # HOTP Model for OTP is created
        if settings.PHONE_SMS_ON and sms_mode:
            try:
                send_sms_message(msg_str=(str(OTP.at(phone_model.counter))), hash_code=hash_code, phone_number=str(phone_no), sms_type="otp", otp_type=otp_type, sender_type=sender_type)
                return Ok({"Result": "Otp sent successfully"})
            except Exception as e:
                print(e)
                return InternalServerError({'error_type': "Internal Error", 'errors': [{'message': e.args[1]}]})
        else:
            return Ok(
                {"Result": "Otp sent successfully", "otp": OTP.at(phone_model.counter),
                 "message": "To sent actual otp set phone_sms_on true"})


class LoginValidateOtpViewset(APIView):
    permission_classes = [permissions.AllowAny]

    # This Method verifies the OTP
    @staticmethod
    def post(request):
        print(request.data)
        serializer = ValidateOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_no = serializer.validated_data.get('phone_no')
        try:
            phone_model = PhoneModel.objects.get(phone_no=phone_no)
        except ObjectDoesNotExist:
            return BadRequest({'error_type': "Validation Error",
                               'errors': [{'message': "Phone number does not exist"}]})  # False Call
        user = User.objects.filter(phone_no=phone_no).first()
        if not user:
            return BadRequest({'error_type': "Validation Error",
                               'errors': [{'message': "Phone number does not exist"}]})  # False Call
        else:
            if user.is_otp_verified:
                return BadRequest({'error_type': "Validation Error",
                                   'errors': [{'message': "Phone number already verified"}]})  # False Call
        time_difference = datetime.now(tz=CURRENT_ZONE) - timedelta(minutes=5)
        phone_expiry = PhoneModel.objects.filter(phone_no=phone_no, updated_at__gte=time_difference, isVerified=False)
        if len(phone_expiry) > 0:
            keygen = GenerateKey()
            key = base64.b32encode(keygen.return_value(phone_no).encode())  # Generating Key
            OTP = pyotp.HOTP(key)  # HOTP Model
            if OTP.verify(request.data["otp"], phone_model.counter):  # Verifying the OTP
                phone_model.isVerified = True
                phone_model.login_count += 1
                phone_model.save()
                LoginStamp.objects.create(phone_model=phone_model)
                user.is_otp_verified = True
                user.save()
                jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
                jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

                payload = jwt_payload_handler(user)
                token = jwt_encode_handler(payload)
                user_data = UserSerializer(user, context={'request': request}).data
                return Ok({"success": "Successfully Verified", "token": token, "user": user_data}, status=200)
            LoginStamp.objects.create(phone_model=phone_model, login_response="Wrong Otp")
            return BadRequest({'error_type': "Validation Error",
                               'errors': [{'message': "OTP is wrong"}]})
        else:
            LoginStamp.objects.create(phone_model=phone_model, login_response="Otp Expired")
            return BadRequest({'error_type': "Validation Error",
                               'errors': [{
                                   'message': "Otp has been expired or already verified, please request for new otp"}]})  # Otp Expire


class EcommerceLoginGenerateOtpViewset(APIView):
    permission_classes = [permissions.AllowAny]

    # Get to Create a call for OTP
    @staticmethod
    def post(request):
        print(request.data)
        serializer = GenerateOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_no = serializer.validated_data.get('phone_no')
        otp_type = serializer.validated_data.get('otp_type', "login")
        sender_type = serializer.validated_data.get('sender_type', "Implicit")
        sms_mode = serializer.validated_data.get('sms_mode', True)
        hash_code = serializer.validated_data.get('hash_code', "")
        email = serializer.validated_data.get('email', "")
        phone_model, created = PhoneModel.objects.get_or_create(
            phone_no=phone_no)  # if Mobile already exists the take this else create New One
        phone_model.counter += 1  # Update Counter At every Call
        phone_model.isVerified = False
        phone_model.save()  # Save the data
        is_existing_user = False
        is_customer = False
        user = User.objects.filter(phone_no=phone_no).first()
        if user:
            user.is_otp_verified = False
            user.save()
            is_existing_user=True
            customer = Customer.objects.filter(user=user).first()
            if customer:
                is_customer = True
        else:
            user2 = User.objects.filter(email=email).first()
            if user2:
                return BadRequest({'error_type': "Validation Error",
                                   'errors': [{'message': "User with Email already exists"}]})

        keygen = GenerateKey()
        key = base64.b32encode(keygen.return_value(phone_no).encode())  # Key is generated
        OTP = pyotp.HOTP(key)  # HOTP Model for OTP is created
        if settings.PHONE_SMS_ON and sms_mode:
            try:
                send_sms_message(msg_str=(str(OTP.at(phone_model.counter))), hash_code=hash_code, phone_number=str(phone_no), sms_type="otp", otp_type=otp_type, sender_type=sender_type)
                return Ok({"Result": "Otp sent successfully","existing_user":is_existing_user,"is_customer":is_customer})
            except Exception as e:
                print(e)
                return InternalServerError({'error_type': "Internal Error", 'errors': [{'message': e.args[1]}]})
        else:
            return Ok(
                {"Result": "Otp sent successfully","existing_user":is_existing_user,"is_customer":is_customer, "otp": OTP.at(phone_model.counter),
                 "message": "To sent actual otp set phone_sms_on true"})


class EcommerceLoginValidateOtpViewset(APIView):
    permission_classes = [permissions.AllowAny]

    # This Method verifies the OTP
    @staticmethod
    def post(request):
        print(request.data)
        serializer = ValidateOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_no = serializer.validated_data.get('phone_no')

        try:
            phone_model = PhoneModel.objects.get(phone_no=phone_no)
        except ObjectDoesNotExist:
            return BadRequest({'error_type': "Validation Error",
                               'errors': [{'message': "Phone number does not exist"}]})  # False Call
        time_difference = datetime.now(tz=CURRENT_ZONE) - timedelta(minutes=5)
        phone_expiry = PhoneModel.objects.filter(phone_no=phone_no, updated_at__gte=time_difference, isVerified=False)
        if len(phone_expiry) > 0:
            keygen = GenerateKey()
            key = base64.b32encode(keygen.return_value(phone_no).encode())  # Generating Key
            OTP = pyotp.HOTP(key)  # HOTP Model
            if OTP.verify(request.data["otp"], phone_model.counter):  # Verifying the OTP
                print("in otp verify")
                user = User.objects.filter(phone_no=phone_no).first()
                if not user:
                    # name = serializer.validated_data.get('name')
                    # email = serializer.validated_data.get('email')
                    customer_serializer = CustomerCreationSerializer(data=request.data)
                    customer_serializer.is_valid(raise_exception=True)
                    dummy_user_serializer = DummyUserRegistrationSerializer(data=request.data)
                    dummy_user_serializer.is_valid(raise_exception=True)
                    user = dummy_user_serializer.save()
                    customer_user_profile, customer_user_profile_created = UserProfile.objects.get_or_create(
                        user=user)
                    department, department_created = Department.objects.get_or_create(name="Customer")
                    customer_user_profile.department.add(department)
                    customer_user_profile.save()
                    address = Address.objects.create(name=request.data.get("name"),ecommerce_sector_id=request.data.get('ecommerce_sector'),city_id=request.data.get('city'),phone_no=phone_no)
                    user.default_address=address
                    user.addresses.add(address)
                    user.save()
                    customer_code = str(phone_no)[-10:]

                    customer = Customer.objects.create(name=request.data.get("name"),user=user,phone_no=phone_no,code=customer_code)

                    customer.shipping_address=address
                    customer.billing_address=address
                    customer.billing_shipping_address_same=True
                    customer.onboarding_date=datetime.now(tz=CURRENT_ZONE)
                    customer.save()
                    if request.data["referral_code"] and not request.data["referral_code"] == "":
                        customer_referral = CustomerReferral.objects.filter(referral_code=request.data["referral_code"])
                        if customer_referral:
                            ref_data = ReferralData.objects.create(used_by=customer,
                                                                   start_date=datetime.now(tz=CURRENT_ZONE),
                                                                   expiry_date=datetime.now(tz=CURRENT_ZONE) + timedelta(days=30))
                            customer_referral.referral_data.add(ref_data)

                else:
                    customer = Customer.objects.filter(user=user).first()
                    if not customer:
                        customer_serializer = CustomerCreationSerializer(data=request.data)
                        customer_serializer.is_valid(raise_exception=True)
                        customer_user_profile, customer_user_profile_created = UserProfile.objects.get_or_create(
                            user=user)
                        department, department_created = Department.objects.get_or_create(name="Customer")
                        customer_user_profile.department.add(department)
                        customer_user_profile.save()
                        address = Address.objects.create(name=request.data.get("name"),ecommerce_sector_id=request.data.get('ecommerce_sector'),city_id=request.data.get('city'),phone_no=phone_no)
                        user.default_address = address
                        user.addresses.add(address)
                        user.save()
                        customer_code = str(phone_no)[-10:]
                        customer = Customer.objects.create(name=request.data.get("name"),user=user, phone_no=phone_no, code=customer_code)
                        customer.shipping_address = address
                        customer.billing_address = address
                        customer.billing_shipping_address_same = True
                        customer.onboarding_date = datetime.now(tz=CURRENT_ZONE)
                        customer.save()

                    else:
                        if user.is_otp_verified:
                            return BadRequest({'error_type': "Validation Error",
                                               'errors': [{'message': "Phone number already verified"}]})  # False Call
                phone_model.isVerified = True
                phone_model.login_count += 1
                phone_model.save()
                LoginStamp.objects.create(phone_model=phone_model)
                user.is_otp_verified = True
                user.save()
                jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
                jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
                payload = jwt_payload_handler(user)
                token = jwt_encode_handler(payload)
                user_data = UserCustomerSerializer(user, context={'request': request}).data
                return Ok({"success": "Successfully Verified", "token": token,"token_exp":datetime.fromtimestamp(payload.get('exp')), "user": user_data}, status=200)
            print("in not otp verify")
            LoginStamp.objects.create(phone_model=phone_model, login_response="Wrong Otp")
            return BadRequest({'error_type': "Validation Error",
                               'errors': [{'message': "OTP is wrong"}]})
        else:
            LoginStamp.objects.create(phone_model=phone_model, login_response="Otp Expired")
            return BadRequest({'error_type': "Validation Error",
                               'errors': [{
                                   'message': "Otp has been expired or already verified, please request for new otp"}]})  # Otp Expire