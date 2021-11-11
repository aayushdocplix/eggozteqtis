# -*- coding: utf-8 -*-

# Standard Library
import json

# Third Party Modules
import requests
from phonenumbers import parse as phone_parse

from Eggoz.settings import env

TRUSTSIGNAL_AUTH_KEY = env('SENDSMS_AUTH_KEY', default="")


api_url = "https://api.trustsignal.io/v1/sms?api_key=%s" % (TRUSTSIGNAL_AUTH_KEY)


def send_sms(message_format):
    parsed_phone_number = phone_parse(message_format.get('to')[0])
    sms_type = message_format.get('sms_type')
    otp_type = message_format.get('otp_type')
    sender_type = message_format.get('sender_type')
    hash_code = message_format.get('hash_code')
    msg_str = message_format.get('msg_str')
    phone_number = int(parsed_phone_number.national_number)
    headers = {
        "Content-Type": "application/json"
    }
    if sender_type == "Implicit":
        TRUSTSIGNAL_SENDER = env('SENDSMS_FROM_IMPLICIT_NUMBER', default="")
    elif sender_type == "Explicit":
        TRUSTSIGNAL_SENDER = env('SENDSMS_FROM_EXPLICIT_NUMBER', default="")
    else:
        TRUSTSIGNAL_SENDER = ""

    if otp_type == "login":
        if hash_code == "":
            TRUSTSIGNAL_TEMPLATE = env('SENDSMS_FROM_LOGIN_TEMPLATE', default="")
            message = "Eggoz Channel Login OTP : {}.".format(msg_str)
        elif hash_code == "release":
            TRUSTSIGNAL_TEMPLATE = env('SENDSMS_FROM_HASH_LOGIN_TEMPLATE', default="")
            message = "<#> Eggoz Channel Login OTP : {}. For any help, please contact us at contact@eggoz.in {}".\
                format(msg_str, env("HASHCODE_PROD", default=""))
        elif hash_code == "debug":
            TRUSTSIGNAL_TEMPLATE = env('SENDSMS_FROM_HASH_LOGIN_TEMPLATE', default="")
            message = "<#> Eggoz Channel Login OTP : {}. For any help, please contact us at contact@eggoz.in {}".\
                format(msg_str, env("HASHCODE_DEBUG", default=""))
        elif hash_code == "playstore":
            TRUSTSIGNAL_TEMPLATE = env('SENDSMS_FROM_HASH_LOGIN_TEMPLATE', default="")
            message = "<#> Eggoz Channel Login OTP : {}. For any help, please contact us at contact@eggoz.in {}".\
                format(msg_str, env("HASHCODE_PLAYSTORE", default=""))
    elif otp_type == "onboarding":
        TRUSTSIGNAL_TEMPLATE = env('SENDSMS_FROM_ONBOARD_TEMPLATE', default="")
        message = "Eggoz Channel Partner Onboarding OTP : {} . " \
                  "Share with Eggoz team members only to start selling Eggoz!".format(msg_str)
    else:
        TRUSTSIGNAL_TEMPLATE = ""
        message = ""

    payload = {"sender_id": TRUSTSIGNAL_SENDER, "to": [phone_number], "route": sms_type, "message": message,
               "template_id": TRUSTSIGNAL_TEMPLATE}
    if not TRUSTSIGNAL_SENDER == "" and not TRUSTSIGNAL_TEMPLATE == "":
        response = requests.post(api_url, headers=headers, json=payload)
        res_json = json.loads(response.text)
    else:
        res_json = {"message": "sender id or template id missing"}
    print(res_json)


def send_order_event_sms(message_format):
    parsed_phone_number = phone_parse(message_format.get('to')[0])
    sms_type = message_format.get('sms_type')
    if sms_type is None:
        sms_type="transactional"
    msg_var1 = message_format.get('msg_var1')
    msg_var2 = message_format.get('msg_var2')
    phone_number = int(parsed_phone_number.national_number)
    headers = {
        "Content-Type": "application/json"
    }
    TRUSTSIGNAL_SENDER = env('SENDSMS_FROM_IMPLICIT_NUMBER', default="")
    TRUSTSIGNAL_TEMPLATE = env('SENDSMS_FROM_ORDER_EVENT_TEMPLATE', default="uC8HoTgng")
    message = "Dear Customer, %s. %s. For any help, please contact us at po@eggoz.in"%(msg_var1,msg_var2)

    payload = {"sender_id": TRUSTSIGNAL_SENDER, "to": [phone_number], "route": sms_type, "message": message,
               "template_id": TRUSTSIGNAL_TEMPLATE}
    if not TRUSTSIGNAL_SENDER == "" and not TRUSTSIGNAL_TEMPLATE == "":
        response = requests.post(api_url, headers=headers, json=payload)
        res_json = json.loads(response.text)
    else:
        res_json = {"message": "sender id or template id missing"}
    print(res_json)