import collections
# import datetime_ist
import math
import os
import re
from datetime import datetime
from decimal import Decimal

import pandas as pd
import phonenumbers
import pytz
from django.core.files.storage import FileSystemStorage
from django.db.models import Max
from django.utils import timezone

from Eggoz import settings
from Eggoz.settings import BASE_DIR, CURRENT_ZONE
from feedwarehouse.models import FeedProduct, FeedProductDivision, FeedProductSubDivision, ProductVendor, \
    FeedProductSpecification
from order.api.serializers import OrderLineSerializer, OrderCreateSerializer
from order.models import Order
from payment.models import Invoice, SalesTransaction, Payment
from product.models import Product
from retailer.models import Retailer, RetailerEggsdata
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
        datetime.strptime(value, '%d/%m/%Y')
        return value
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
    return True, None


def upload_feed_product(csv_file):
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
    data_header_list = ['Equipment Type', 'Category', 'Specifications', 'Vendor', 'Image']
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
                        {"index": index + 2, "item_name": str(row['Equipment Type']).strip(), "error": error})
                    continue
            except Exception as ex:
                row_processed.append("Failed")
                process_error.append(ex.args[1])
                print("Error %s" % ex.args[1])
                row["Upload Status"] = "Fail"
                data['error'].append(
                    {"index": index + 2, "item_name": str(row['Equipment Type']).strip(), "error": ex.args[1]})
                continue
            try:
                feed_product = FeedProduct.objects.filter(name=str(row['Equipment Type']).strip()).first()
                if feed_product:
                    FeedProductSpecification.objects.create(specification=row['Specifications'],
                                                            feedProduct=feed_product)
                    row["Upload Status"] = "Product Exists"
                    data['success'].append(
                        {"index": index + 2, "item_name": str(row['Equipment Type']).strip(),
                         "message": "Specification Added"})
                    row_processed.append("Success")
                    process_error.append("Specification Added")
                    continue
                else:
                    feed_product_division, created = FeedProductDivision.objects.get_or_create(
                        name=str(row['Category']).strip(), description=str(row['Category']).strip(),
                        code=str(row['Category']).strip())
                    feed_product_sub_division, created = FeedProductSubDivision.objects.get_or_create(
                        name=str(row['Category']).strip(), description=str(row['Category']).strip(),
                        code=str(row['Category']).strip(), feedProductDivision=feed_product_division)
                    vendor, created = ProductVendor.objects.get_or_create(name=str(row['Vendor']).strip())
                    feed_product, created = FeedProduct.objects.get_or_create(name=str(row['Equipment Type']).strip(),
                                                                             description=str(
                                                                                 row['Equipment Type']).strip(),
                                                                             slug=str(
                                                                                 row['Equipment Type']).strip().replace(
                                                                                 " ", "-"),
                                                                             vendor=vendor,
                                                                             feedProductDivision=feed_product_division,
                                                                             feedProductSubDivision=feed_product_sub_division,
                                                                             feed_product_image=row['Image'],
                                                                             updated_at=datetime.now(tz=CURRENT_ZONE)
                                                                             )
                    FeedProductSpecification.objects.create(specification=row['Specifications'],
                                                            feedProduct=feed_product)
                    row["Upload Status"] = "Product Created"
                    data['success'].append(
                        {"index": index + 2, "item_name": str(row['Equipment Type']).strip(),
                         "message": "Product Created"})
                    row_processed.append("Success")
                    process_error.append("Product Created")
                    continue

            except Exception as ex:
                print("Error %s" % ex.args[1])
                data['error'].append(
                    {"index": index + 2, "item_name": str(row['Equipment Type']).strip(), "error": ex.args[1]})
                row_processed.append("Failed")
                process_error.append(ex.args[1])
                continue

        total_rows = total_rows - 1
        print("remaining rows " + str(total_rows))
        df["Process Status"] = row_processed
        df["Process error"] = process_error
        df.to_csv(f'{tmp_root}/{csv_file}')

        # os.remove(f'{tmp_root}/{csv_file}')

        file_response['status'] = "success"
        data['total_success'] = data['total_success'] + len(data.get('success'))
        data['total_failed'] = data['total_failed'] + len(data.get('error'))
        file_response['data'] = data
        return file_response

    else:
        # os.remove(f'{tmp_root}/{csv_file}')
        file_response['status'] = "failed"
        file_response['data'] = {"error": "File Headers Invalid", "valid_file_headers": data_header_list}
        return file_response
