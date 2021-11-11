import collections
# import datetime
import math
import os
import re
from datetime import datetime
from decimal import Decimal

import pandas as pd
import phonenumbers
from django.core.files.storage import FileSystemStorage
from django.db.models import Max

from Eggoz import settings
from Eggoz.settings import BASE_DIR
from order.api.serializers import OrderLineSerializer, OrderCreateSerializer
from order.models import Order
from payment.models import Invoice, SalesTransaction, Payment
from product.models import Product
from retailer.models import Retailer

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
    if not valid_value_for_on_boarding_date(row["Date"]):
        return False, "Onboarding Date:-Incorrect date format, should be DD/MM/YYYY"

    if not valid_value_for_string(row["Shop Name"]):
        return False, "Shop Name:-Shop Name Required or not valid"

    if not valid_value_for_string(row["Bill no."]):
        return False, "Bill no.:-Bill no. Required or not valid"

    if not valid_value_for_string(row["Sales Person"]):
        return False, "Sales Person:-Sales Person Required or not valid"

    # if not valid_value_for_float(row["amount"]):
    #     return False, "Amount:-Amount Required or not valid"

    return True, None


def upload_eggs_sales(csv_file):
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
    data_header_list = ['Date', 'Year', 'Month', 'Day', 'Bill no.', 'Shop Name', 'PENDING', 'Sales Person', 'Category',
                        'Sub Category', 'Cluster', '6W', '6W Rate', '10W', '10W Rate', '12W', '12W Rate', '25W',
                        '25W Rate', '6B', '6B Rate', '10B', '10B Rate', '25B', '25B Rate', '1W', '1W Rate', '1B',
                        '1B Rate', '30W', '30W Rate', '30B', '30B Rate', '210p Qty', '210p Rate', '30 Chatki Qty',
                        '30 Chatki Rate', 'amount','Acc pay', 'instant pay', 'Mode', 'later pay','mode for later pay','date','amount pending','Paid? Status',]
    header_valid = check_product_csv_headers(list(df.columns.values), data_header_list)
    if header_valid:
        data = {}
        data['total_rows'] = len(df)
        data['total_success'] = 0
        data['total_failed'] = 0
        data["error"] = []
        data["success"] = []
        row_processed = []
        process_error = []
        for index, row in df.iterrows():
            try:
                validation_status, error = validate_row(row)
                if not validation_status:
                    row_processed.append("Failed")
                    process_error.append(error)

                    data['error'].append({"index": index + 2, "shop_name": str(row['Shop Name']).strip(), "error": error})
                    continue
            except Exception as ex:
                row_processed.append("Failed")
                process_error.append(ex.args[1])
                print("Error %s" % ex.args[1])
                row["Upload Status"] = "Fail"
                data['error'].append({"index": index + 2, "shop_name": str(row['Shop Name']).strip(), "error": ex.args[1]})
                continue
            try:

                print("*****")
                print(row['Shop Name'])
                print(row['Sales Person'])
                print("#####")
                retailer = Retailer.objects.filter(name_of_shop=str(row['Shop Name']).strip(),
                                                   salesPersonProfile__user__name__icontains=row[
                                                       'Sales Person']).first()
                if retailer:
                    print(row['Date'].strip())
                    city_name = retailer.city.city_name
                    order_date = datetime.strptime(row['Date'].strip(), "%d/%m/%Y")
                    order_price_amount = round(Decimal(row['amount']), 2)
                    print(order_date)
                    print(order_price_amount)
                    print(retailer.id)
                    orders = Order.objects.filter(orderId=row['Bill no.'] + city_name).count()
                    # orders = Order.objects.filter(retailer=retailer.id,
                    #                               delivery_date=order_date,
                    #                               order_price_amount=order_price_amount).count()
                    if orders > 0:
                        print("order Found")
                        row["Upload Status"] = "Success"
                        data['success'].append(
                            {"index": index + 2, "shop_name": str(row['Shop Name']).strip(),
                             "success": "OK"})
                        process_error.append("")
                        row_processed.append("Success")
                        continue

                    else:
                        print("Order Not Found")

                        # Make Order Line
                        cart_product_list = []
                        product_found = True
                        product_type_list = ['1W', '6W', '10W', '12W', '25W', '30W', '1B', '6B', '10B', '25B', '30B']
                        for product_type in product_type_list:
                            if row[product_type] > 0:
                                if row[product_type + " Rate"] > 0:
                                    print(product_type)
                                    # product_slug = city_name + '-' + str(product_type[-1]) + "-" + str(
                                    #     re.findall(r'(\d+)', product_type)[0])
                                    product_slug = 'Gurgaon-' + str(product_type[-1]) + "-" + str(product_type[:-1])
                                    print(product_slug)
                                    product = Product.objects.filter(slug=product_slug).first()
                                    if product:
                                        cart_product_dict = {"product": product.id, "quantity": row[product_type],
                                                             "single_sku_rate": round(Decimal(
                                                                 row[product_type + " Rate"]), 2)}
                                        cart_product_list.append(cart_product_dict)
                                    else:
                                        product_found = False
                        if product_found:
                            order_dict = {
                                "retailer": retailer.id,
                                "delivery_date": order_date,
                                "cart_products": cart_product_list,
                                "order_price_amount": order_price_amount,
                                "warehouse": 1
                            }
                            print(order_dict)

                            order_create_serializer = OrderCreateSerializer(data=order_dict)
                            order_create_serializer_valid = order_create_serializer.is_valid(raise_exception=False)
                            if not order_create_serializer_valid:
                                data['error'].append(
                                    {"index": index + 2, "shop_name": str(row['Shop Name']).strip(),
                                     "error": order_create_serializer._errors})
                                row_processed.append("Failed")
                                process_error.append(order_create_serializer._errors)
                                continue
                            else:
                                delivery_date = order_dict['delivery_date']
                                order_type = "Retailer"
                                cart_products = order_dict['cart_products']

                                order_line_valid = True

                                if len(cart_products) > 0:
                                    for cart_product in cart_products:
                                        order_line_serializer = OrderLineSerializer(data=cart_product)
                                        order_line_serializer_valid = order_line_serializer.is_valid(
                                            raise_exception=False)
                                        if not order_line_serializer_valid:
                                            order_line_valid = False
                                if not order_line_valid:
                                    # TODO Validate Payment without orders
                                    row["Upload Status"] = "Fail"
                                    data['error'].append(
                                        {"index": index + 2, "shop_name": str(row['Shop Name']).strip(),
                                         "error": "Order Line not valid" + str(cart_products)})
                                    row_processed.append("Failed")
                                    process_error.append("Order Line not valid")
                                    continue
                                else:
                                    try:
                                        order_obj = order_create_serializer.save(name=row['Bill no.'],
                                                                                 orderId=row['Bill no.'] + city_name,
                                                                                 order_type=order_type,
                                                                                 salesPerson=retailer.salesPersonProfile,
                                                                                 delivery_date=delivery_date,
                                                                                 status='delivered',date=delivery_date)

                                        for cart_product in cart_products:
                                            order_line_serializer = OrderLineSerializer(data=cart_product)
                                            order_line_serializer.is_valid(raise_exception=False)
                                            order_line_serializer.save(order=order_obj)
                                            # Update Last Order Date of a Retailer
                                        order_obj.retailer.last_order_date = order_date
                                        order_obj.retailer.save()

                                        # Now Make Invoice
                                        invoice = Invoice.objects.filter(order=order_obj).first()
                                        if not invoice:
                                            invoices = Invoice.objects.all()
                                            # might be possible model has no records so make sure to handle None
                                            invoice_max_id = invoices.aggregate(Max('id'))[
                                                                 'id__max'] + 1 if invoices else 1
                                            invoice_id = "E" + str(invoice_max_id)
                                            invoice = Invoice.objects.create(order=order_obj, invoice_id=invoice_id,
                                                                   invoice_due=order_obj.retailer.calc_amount_due)
                                        if str(row['Paid? Status'])=="paid":
                                            invoice.invoice_status="Paid"
                                            invoice.save()

                                        # Make Debit Transaction
                                        transactions = SalesTransaction.objects.all()
                                        # might be possible model has no records so make sure to handle None
                                        transaction_max_id = transactions.aggregate(Max('id'))[
                                                                 'id__max'] + 1 if transactions else 1
                                        transaction_id = "TR" + str(transaction_max_id)
                                        transaction_amount = order_obj.order_price_amount
                                        transaction_date = order_date
                                        sales_transaction = SalesTransaction.objects.create(retailer=retailer,
                                                                                            salesPerson=retailer.salesPersonProfile,
                                                                                            transaction_id=transaction_id,
                                                                                            transaction_type="Debit",
                                                                                            invoice=invoice,
                                                                                            transaction_amount=transaction_amount,transaction_date=transaction_date)
                                        sales_transaction.retailer.calc_amount_due = round(Decimal(
                                            sales_transaction.retailer.calc_amount_due), 2) + round(Decimal(
                                            sales_transaction.transaction_amount), 2)
                                        sales_transaction.retailer.save()
                                        sales_transaction.current_balance = sales_transaction.retailer.calc_amount_due
                                        sales_transaction.save()

                                        payment_type_list = ['instant pay', 'later pay']
                                        # Now Made  Credit Transactions for Instant Pay
                                        for payment_type in payment_type_list:
                                            if payment_type == 'instant pay':
                                                pay_choice = 'InstantPay'
                                            else:
                                                pay_choice='LaterPay'
                                            if not str(row[payment_type]) == 'nan' and int(row[payment_type]) > 0:
                                                transactions = SalesTransaction.objects.all()
                                                # might be possible model has no records so make sure to handle None
                                                transaction_max_id = transactions.aggregate(Max('id'))[
                                                                         'id__max'] + 1 if transactions else 1
                                                transaction_id = "TR" + str(transaction_max_id)
                                                transaction_amount = row[payment_type]
                                                if payment_type == "instant pay":
                                                    transaction_date=order_date
                                                else:
                                                    if row['date'] == "na":
                                                        transaction_date = datetime.strptime("10/09/2020",
                                                                                             "%d/%m/%Y")
                                                    else:
                                                        transaction_date=datetime.strptime(row['date'].strip(), "%d/%m/%Y")
                                                sales_transaction = SalesTransaction.objects.create(retailer=retailer,
                                                                                                    salesPerson=retailer.salesPersonProfile,
                                                                                                    transaction_id=transaction_id,
                                                                                                    transaction_type="Credit",
                                                                                                    invoice=invoice,
                                                                                                    transaction_amount=transaction_amount,transaction_date=transaction_date)
                                                if payment_type=="instant pay":
                                                    row_payment_mode = row['Mode']
                                                else:
                                                    row_payment_mode = row['mode for later pay']
                                                if row_payment_mode == 'PAYTM_WALLET' or row_payment_mode == 'RAZOR_PAY':
                                                    payment_mode_type = 'UPI'
                                                elif row_payment_mode == 'ICICI4178' or row_payment_mode == 'ICICI3901':
                                                    payment_mode_type = 'Cheque'
                                                else:
                                                    payment_mode_type = "Cash"
                                                Payment.objects.create(pay_choice=pay_choice, payment_type=payment_mode_type,
                                                                       salesTransaction=sales_transaction)
                                                sales_transaction.retailer.calc_amount_due = round(Decimal(
                                                    sales_transaction.retailer.calc_amount_due), 2) - round(Decimal(
                                                    sales_transaction.transaction_amount), 2)
                                                sales_transaction.retailer.save()
                                                sales_transaction.current_balance = sales_transaction.retailer.calc_amount_due
                                                sales_transaction.save()

                                        row["Upload Status"] = "Success"
                                        data['success'].append(
                                            {"index": index + 2, "shop_name": str(row['Shop Name']).strip(),
                                             "success": "OK"})
                                        process_error.append("")
                                        row_processed.append("Success")
                                    except Exception as ex:
                                        print("Error %s" % ex.args[1])
                                        data['error'].append({"index": index + 2, "shop_name": str(row['Shop Name']).strip(),
                                                              "error": ex.args[1]})
                                        row_processed.append("Failed")
                                        process_error.append(ex.args[1])
                                        continue
                        else:
                            row["Upload Status"] = "Fail"
                            data['error'].append(
                                {"index": index + 2, "shop_name": str(row['Shop Name']).strip(),
                                 "error": "Some Product Is Not Found To upload"})
                            row_processed.append("Failed")
                            process_error.append("Some Product Is Not Found To upload")
                            continue
                else:
                    row["Upload Status"] = "Fail"
                    data['error'].append(
                        {"index": index + 2, "shop_name": str(row['Shop Name']).strip(),
                         "error": "Retailer or Sales Person Not Found"})
                    row_processed.append("Failed")
                    process_error.append("Retailer or Sales Person Not Found")
                    continue

            except Exception as ex:
                print("Error %s" % ex.args[1])
                data['error'].append({"index": index + 2, "shop_name": str(row['Shop Name']).strip(), "error": ex.args[1]})
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
