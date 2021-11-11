import collections
# import datetime_ist
import decimal
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

from Eggoz.settings import BASE_DIR
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
    if not valid_value_for_on_boarding_date(row["Date of Payment"]):
        return False, "Onboarding Date:-Incorrect date format, should be DD/MM/YYYY"

    if not valid_value_for_string(row["code"]):
        return False, "Shop Name:-code Required or not valid"

    return True, None


def update_mt_payments(csv_file):
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
    data_header_list = ['bill_no','code', 'invoice_due','Date of Payment',]
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
                        {"index": index + 2, "bill_no": str(row['bill_no']).strip(), "error": error})
                    continue
            except Exception as ex:
                row_processed.append("Failed")
                process_error.append(ex.args[1])
                print("Error %s" % ex.args[1])
                row["Upload Status"] = "Fail"
                data['error'].append(
                    {"index": index + 2, "bill_no": str(row['bill_no']).strip(), "error": ex.args[1]})
                continue
            try:
                order = Order.objects.filter(name=str(row['bill_no']).strip())
                if order:
                    order = order.first()
                    if order.invoice:
                        IST = pytz.timezone('Asia/Kolkata')
                        datetime_ist = datetime.now(IST)
                        transaction_date = datetime_ist.strptime(row['Date of Payment'].strip(), "%d/%m/%Y")
                        invoice = order.invoice
                        if int(str(row['invoice_due']).strip()):
                            transaction_amount = decimal.Decimal(int(str(row['invoice_due']).strip()))
                            transactions = SalesTransaction.objects.all()
                            # might be possible model has no records so make sure to handle None
                            transaction_max_id = transactions.aggregate(Max('id'))[
                                                     'id__max'] + 1 if transactions else 1
                            transaction_id = "TR" + str(transaction_max_id)
                            sales_transaction = SalesTransaction.objects.create(retailer=order.retailer,
                                                                                salesPerson_id=11,
                                                                                financePerson_id=5,
                                                                                transaction_id=transaction_id,
                                                                                transaction_type='Credit',
                                                                                remarks="mt clearence",
                                                                                transaction_amount=transaction_amount,
                                                                                transaction_date=transaction_date)
                            Payment.objects.create(pay_choice='LaterPay',
                                                   payment_type='UPI',
                                                   payment_mode='AXIS',
                                                   pay_amount=transaction_amount,
                                                   invoice=invoice,
                                                   created_at=transaction_date,
                                                   salesTransaction=sales_transaction)
                            sales_transaction.retailer.amount_due = round(Decimal(
                                sales_transaction.retailer.amount_due), 2) - round(Decimal(
                                sales_transaction.transaction_amount), 2)
                            sales_transaction.retailer.save()
                            sales_transaction.current_balance = sales_transaction.retailer.amount_due
                            invoice.invoice_due = decimal.Decimal(0.000)
                            invoice.invoice_status = "Paid"
                            invoice.save()
                            sales_transaction.invoices.add(invoice)

                            row["Upload Status"] = "Success"
                            data['success'].append(
                                {"index": index + 2, "shop_name": str(row['code']).strip(),
                                 "success": "OK"})
                            process_error.append("")
                            row_processed.append("Success")
                        else:
                            print("Error %s" % "invalid invoice due")
                            data['error'].append(
                                {"index": index + 2, "bill_no": str(row['bill_no']).strip(), "error": "invalid invoice due"})
                            row_processed.append("Failed")
                            process_error.append("invalid invoice due")
                            continue
                    else:
                        print("Error %s" % "No invoice")
                        data['error'].append(
                            {"index": index + 2, "bill_no": str(row['bill_no']).strip(), "error": "No invoice"})
                        row_processed.append("Failed")
                        process_error.append("No invoice")
                        continue
                else:
                    print("Error %s" % "No order")
                    data['error'].append(
                        {"index": index + 2, "bill_no": str(row['bill_no']).strip(), "error": "No order"})
                    row_processed.append("Failed")
                    process_error.append("No order")
                    continue
            except Exception as ex:
                print("Error %s" % ex.args[1])
                data['error'].append(
                    {"index": index + 2, "bill_no": str(row['bill_no']).strip(), "error": ex.args[1]})
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
