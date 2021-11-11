from Eggoz.settings import EGGOZ_ENV
from custom_auth.api.serializers import UserSerializer


def my_jwt_response_handler(token, user=None, request=None):
    user_data = UserSerializer(user, context={'request': request}).data
    if EGGOZ_ENV == "PROD":
        if not user.is_phone_verified:
            user_phone_number = str(user.phone_no)
            return {'error_type': "Validation Error",
                                           'errors': [{'message': "This Phone No- %s is Not Verified, Please Verify"%(user_phone_number)}]}
    return {
        'token': token,
        'user': user_data
    }
