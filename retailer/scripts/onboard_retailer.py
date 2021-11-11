import collections
# import datetime_ist
import decimal
import math
import os
import random
import re
from datetime import datetime
from decimal import Decimal
from Eggoz.settings import CURRENT_ZONE
import pandas as pd
import phonenumbers
import pytz
from django.core.files.storage import FileSystemStorage
from django.db.models import Max

from Eggoz.settings import BASE_DIR
from base.models import City, Cluster
from custom_auth.models import User, UserProfile, Department, Address
from order.api.serializers import OrderLineSerializer, OrderCreateSerializer
from order.models import Order
from payment.models import Invoice, SalesTransaction, Payment
from product.models import Product
from retailer.models import Retailer, RetailerEggsdata, RetailOwner
from saleschain.models import SalesEggsdata, SalesPersonProfile

regex = '^[a-zA-Z0-9]+[\._]?[a-zA-Z0-9]+[@]\w+[.]\w{2,3}$'


def check_product_csv_headers(header_values, data_header_list):
    print(data_header_list)
    print(header_values)
    if len(data_header_list) <= len(header_values):
        if collections.Counter(data_header_list) == collections.Counter(header_values):
            print("Headers are valid ")
            header_valid = True
        else:
            print("Headers not valid")
            header_valid = False
    else:
        print("Header length not same")
        header_valid = False
    return header_valid


def isfloat(value):
    try:
        value = float(value)
        if math.isnan(value):
            return False
        return True
    except ValueError:
        return False


def isstr(value):
    try:
        value = str(value)
        if value == "nan":
            return False
        return True
    except ValueError:
        return False


def is_int(value):
    try:
        int(value)
        return True
    except:
        return False


def is_nan_or_None(value):
    try:
        changed_value = str(value)
        if changed_value == "nan":
            return True
        elif value == None:
            return True
        else:
            return False
    except ValueError:
        return False


def valid_value_for_email(value, required=False):
    if required:
        if isstr(value):
            try:
                if (re.search(regex, value)):
                    return value.replace(' ', '')
                else:
                    return None
            except:
                return None
        else:
            return None
    else:
        if is_nan_or_None(value):
            return True
        else:
            try:
                if (re.search(regex, value)):
                    return value.replace(' ', '')
                else:
                    return None
            except:
                return None


def valid_value_for_mobile(value, required=False):
    if isinstance(value, float):
        if str(value) == "nan":
            if required:
                return None
            else:
                return value
        else:
            try:
                value = str(int(value)).replace(' ', '').replace('-', '').replace(".", "")
                value = value[-10:]
            except:
                return None
    elif isinstance(value, str):
        value = value.replace(' ', '').replace('-', '').replace(".", "")
        value = value[-10:]
    elif isinstance(value, int):
        value = str(value).replace(' ', '').replace('-', '').replace(".", "")
        value = value[-10:]
    else:
        return None

    try:
        z = phonenumbers.parse(value, "IN")
        phone_valid = phonenumbers.is_valid_number(z)
        if phone_valid:
            return "+" + str(z.country_code) + str(z.national_number)
        else:
            return None
    except Exception as e:
        print(e)
        return None


def valid_value_for_pin_code(value, required=False):
    if isinstance(value, float):
        if str(value) == "nan":
            if required:
                return None
            else:
                return value
        else:
            try:
                value = str(int(value))
            except:
                return None
    elif isinstance(value, int):
        value = str(value)

    try:
        if len(value) == 6:
            return value
        else:
            return None
    except Exception as e:
        print(e)
        return None


def valid_value_for_float(value):
    if value == "nan":
        return
    if value is None:
        return
    if not isfloat(value):
        return
    return value


def valid_value_for_on_boarding_date(value):
    try:
        # print(value)
        if value:
            datetime.strptime(value, '%d/%m/%Y')
            return value
        else:
            return
    except ValueError:
        return


def valid_value_for_alphanumeric(value):
    changed_value = str(value)
    if changed_value == "nan":
        return
    if value is None:
        return
    return value


def valid_value_for_string(value):
    changed_value = str(value)
    if changed_value == "nan":
        return
    if value is None:
        return
    if not isstr(value):
        return
    return value


def make_nan_to_None(value):
    change_value = str(value)
    if change_value == "nan":
        return None
    else:
        return value


def validate_row(row):
    # if not valid_value_for_on_boarding_date(row["Date"]):
    #     return False, "Onboarding Date:-Incorrect date format, should be DD/MM/YYYY"

    # if not valid_value_for_string(row["Shop Name"]):
    #     return False, "Shop Name:-Shop Name Required or not valid"

    # if not valid_value_for_string(row["bill no"]):
    #     return False, "bill no:-bill no Required or not valid"

    # if not valid_value_for_string(row["SP"]):
    #     return False, "SP:-SP Required or not valid"

    # if not valid_value_for_float(row["amount"]):
    #     return False, "Amount:-Amount Required or not valid"

    return True, None


def onboard_ub_retailer(csv_file):
    file_response = {}
    csv_file_name = csv_file.name
    temp_folder_path = os.path.join(BASE_DIR, 'temp_files')
    tmp_root = os.path.join(temp_folder_path, 'tmp')
    FileSystemStorage(location=tmp_root).save(csv_file.name, csv_file)

    index_of_dot = csv_file_name.index('.')
    csv_file_name_without_extension = csv_file_name[:index_of_dot]

    df = pd.read_csv(f'{tmp_root}/{csv_file_name_without_extension}.csv')
    total_rows = (len(df))
    print(total_rows)

    print("total Rows to be processed " + str(total_rows))
    data_header_list = ['Shop Name', 'city', 'city_id', 'SP', 'SP_id']
    header_valid = check_product_csv_headers(list(df.columns.values), data_header_list)
    if header_valid:
        data = {'total_rows': len(df), 'total_success': 0, 'total_failed': 0, "error": [], "success": []}
        row_processed = []
        process_error = []
        for index, row in df.iterrows():
            try:
                validation_status, error = validate_row(row)
                if not validation_status:
                    row_processed.append("Failed")
                    process_error.append(error)

                    data['error'].append(
                        {"index": index + 2, "shop_name": str(row['Shop Name']).strip(), "error": error})
                    continue
            except Exception as ex:
                row_processed.append("Failed")
                process_error.append(ex.args[1])
                print("Error %s" % ex.args[1])
                row["Upload Status"] = "Fail"
                data['error'].append(
                    {"index": index + 2, "shop_name": str(row['Shop Name']).strip(), "error": ex.args[1]})
                continue
            try:
                start = 6000000000
                end = 9999999999
                phone_no = random.randint(start, end)
                retailer_name = str(row['Shop Name']).strip()
                city_id = int(row['city_id'])
                while User.objects.filter(phone_no="+91" + str(phone_no)):
                    phone_no = random.randint(start, end)
                user = User.objects.create_user(name=retailer_name, phone_no="+91" + str(phone_no),
                                                email=str(phone_no) + "@gmail.com")
                retailer_user_profile, created = UserProfile.objects.get_or_create(user=user)
                retailer_department, created = Department.objects.get_or_create(name="Retailer")
                retailer_user_profile.department.add(retailer_department)
                address = Address.objects.create(city_id=city_id)
                user.addresses.add(address)
                if user.default_address is None:
                    user.default_address = address
                user.save()

                beat_number = 0
                classification_id = 1
                short_name_id = 1
                payment_cycle_id = 1
                commission_slab_id = 1
                discount_slab_id = 1
                category_id = 1
                sub_category_id = 1
                salesPersonProfile_id = int(row['SP_id'])
                data_city = City.objects.get(id=city_id)
                cluster_id = Cluster.objects.filter(city=data_city).first().id
                code_string = data_city.city_string
                retailers = Retailer.objects.filter(code_string=code_string)
                retailer_max_code_id = retailers.aggregate(Max('code_int'))[
                                           'code_int__max'] + 1 if retailers else 0
                onboarding_date = datetime.strptime("01/05/2021", '%d/%m/%Y')
                code_int = str(retailer_max_code_id)
                print(retailer_name)
                retailer = Retailer.objects.create(
                    salesPersonProfile_id=salesPersonProfile_id,
                    retailer=user,
                    code=str(code_string) + str(code_int) + "* " + retailer_name,
                    name_of_shop=retailer_name,
                    billing_name_of_shop=retailer_name,
                    category_id=category_id,
                    sub_category_id=sub_category_id,
                    city_id=city_id,
                    cluster_id=cluster_id,
                    code_int=code_int,
                    code_string=code_string,
                    onboarding_date=onboarding_date,
                    beat_number=beat_number,
                    commission_slab_id=commission_slab_id,
                    classification_id=classification_id,
                    rate_type="unbranded",
                    discount_slab_id=discount_slab_id,
                    short_name_id=short_name_id,
                    payment_cycle_id=payment_cycle_id,
                    shipping_address=address,
                    billing_address=address)

                retailerOwner = RetailOwner.objects.create(retail_shop=retailer,phone_no="+91"+str(phone_no))

                row["Upload Status"] = "Success"
                data['success'].append(
                    {"index": index + 2, "shop_name": str(row['Shop Name']).strip(),
                     "success": "OK"})
                process_error.append("")
                row_processed.append("Success")

            except Exception as ex:
                print("Error %s" % ex.args[1])
                data['error'].append(
                    {"index": index + 2, "shop_name": str(row['Shop Name']).strip(), "error": ex.args[1]})
                row_processed.append("Failed")
                process_error.append(ex.args[1])
                continue

        total_rows = total_rows - 1
        print("remaining rows " + str(total_rows))
        df["Process Status"] = row_processed
        df["Process error"] = process_error
        df.to_csv(f'{tmp_root}/{csv_file}')

        os.remove(f'{tmp_root}/{csv_file}')

        file_response['status'] = "success"
        data['total_success'] = data['total_success'] + len(data.get('success'))
        data['total_failed'] = data['total_failed'] + len(data.get('error'))
        file_response['data'] = data
        return file_response

    else:
        os.remove(f'{tmp_root}/{csv_file}')
        file_response['status'] = "failed"
        file_response['data'] = {"error": "File Headers Invalid", "valid_file_headers": data_header_list}
        return file_response
