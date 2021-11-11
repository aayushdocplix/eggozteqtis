from custom_auth.sms_backends import send_sms, send_order_event_sms


def send_sms_message(msg_str, hash_code, phone_number, otp_type, sms_type, sender_type):
    to = [phone_number]
    message_format = {
        "msg_str": msg_str,
        "to": to,
        "otp_type": otp_type,
        "sms_type": sms_type,
        "sender_type": sender_type,
        "hash_code": hash_code
    }
    print(message_format)
    send_sms(message_format)


def order_event_sms(msg_var1,msg_var2,phone_number,sms_type=None):
    to = [phone_number]
    message_format = {
        "msg_var1": msg_var1,
        "msg_var2": msg_var2,
        "to": to,
        "sms_type": sms_type
    }
    print(message_format)
    send_order_event_sms(message_format)
