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
    if not valid_value_for_on_boarding_date(row["Date"]):
        return False, "Onboarding Date:-Incorrect date format, should be DD/MM/YYYY"

    if not valid_value_for_string(row["Shop Name"]):
        return False, "Shop Name:-Shop Name Required or not valid"

    # if not valid_value_for_string(row["bill no"]):
    #     return False, "bill no:-bill no Required or not valid"

    # if not valid_value_for_string(row["SP"]):
    #     return False, "SP:-SP Required or not valid"

    # if not valid_value_for_float(row["amount"]):
    #     return False, "Amount:-Amount Required or not valid"

    return True, None


def upload_missing_sales(csv_file):
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
    data_header_list = ['Date','CODE', 'Shop Name','Retailer Id', 'bill no','Beat No.','Sales Person', '6W', '10W', '25W',
                        '30W', '6B', '10B', '25B', '30B', '6N', '10N', 'Amount', 'Instant Pay', 'Billing Amount', 'Remark']
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
                print("*****")
                print(row['Shop Name'])
                print(row['Sales Person'])
                print("#####")

                print(str(index + 2))

                IST = pytz.timezone('Asia/Kolkata')
                datetime_ist = datetime.now(IST)
                if int(row['Retailer Id']) > 0:
                    retailer = Retailer.objects.filter(id=int(row['Retailer Id'])).first()
                    # salesPerson = SalesPersonProfile.objects.filter(id=int(row['SP Id'])).first()
                    print(row['Date'].strip())
                    city_name = retailer.city.city_name
                    city_tag = city_name[:3]
                    sales_person = retailer.salesPersonProfile
                    order_date = datetime_ist.strptime(row['Date'].strip(), "%d/%m/%Y")
                    order_price_amount = round(Decimal(row['Billing Amount']), 2)
                    # order_deviated_amount = Decimal(row['RETURN VALUE ADJUSTMENT']) if not str(row['RETURN VALUE ADJUSTMENT'])== "nan" else Decimal(0.000)
                    order_deviated_amount = Decimal(0.000)
                    print(order_date)
                    print(order_price_amount)
                    print(retailer.id)
                    if str(row['bill no']) == "nan":
                        row["Upload Status"] = "Fail"
                        data['error'].append(
                            {"index": index + 2, "shop_name": str(row['Shop Name']).strip(),
                             "error": "Some Product Is Not Found To upload"})
                        row_processed.append("Failed")
                        process_error.append("Some Product Is Not Found To upload")
                        continue
                    else:
                        orderId = str(row['bill no']) + row['CODE']
                        orderName = str(row['bill no']) + row['CODE']
                        orderBill = str(row['bill no'])
                        orders = Order.objects.filter(orderId=orderId).count()
                        # TODO preexisting code
                        if orders > 0:
                            print("order Found")
                            print(str(index+2))
                            row["Upload Status"] = "Found"
                            data['success'].append(
                                {"index": index + 2, "shop_name": str(row['Shop Name']).strip(),
                                 "success": "Ok"})
                            process_error.append("")
                            row_processed.append("Success")
                            continue
                        # TODO creating new orders
                        else:
                            print(str(index + 2))
                            print("Order Not Found")
                            # Make Order Line
                            cart_product_list = []
                            product_found = True
                            product_type_list = [ '6W', '10W', '25W', '30W', '6B', '10B', '25B', '30B','6N','10N']
                            for product_type in product_type_list:
                                if row[product_type] > 0:
                                    print(product_type)
                                    product_slug = 'Gurgaon-' + str(product_type[-1]) + "-" + str(product_type[:-1])
                                    print(product_slug)
                                    product = Product.objects.filter(slug=product_slug).first()
                                    if product:
                                        cart_product_dict = {"product": product.id, "quantity": row[product_type],
                                                             "single_sku_rate": round(Decimal(int(product.current_price * (1 - retailer.commission_slab.number/100))), 2)}
                                        cart_product_list.append(cart_product_dict)
                                    else:
                                        product_found = False
                            if product_found:
                                order_dict = {
                                    "name":orderName,
                                    "retailer": retailer.id,
                                    "delivery_date": order_date,
                                    "date": order_date,
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
                                            order_obj = order_create_serializer.save(name=orderName,
                                                                                     bill_no=orderBill,
                                                                                     orderId=orderId,
                                                                                     retailer=retailer,
                                                                                     order_type=order_type,
                                                                                     deviated_amount=order_deviated_amount,
                                                                                     salesPerson=sales_person,
                                                                                     delivery_date=delivery_date,
                                                                                     status='delivered',
                                                                                     is_geb=True,
                                                                                     is_geb_verified=False,
                                                                                     date=delivery_date)
                                            orders_list_dict = {'Brown': 0, 'White': 0, 'Nutra': 0}
                                            for cart_product in cart_products:
                                                order_line_serializer = OrderLineSerializer(data=cart_product)
                                                order_line_serializer.is_valid(raise_exception=False)
                                                line = order_line_serializer.save(order=order_obj)
                                                # Update Last Order Date of a

                                                eggs_sort_date = datetime_ist.strptime(row['Date'].strip(), "%d/%m/%Y")
                                                if line.product:
                                                    if orders_list_dict[str(line.product.name)] > 0:
                                                        orders_list_dict[str(line.product.name)] = orders_list_dict[
                                                                                                       line.product.name] \
                                                                                                   + line.quantity * line.product.SKU_Count
                                                    else:
                                                        orders_list_dict[
                                                            str(line.product.name)] = line.quantity * line.product.SKU_Count

                                            # TODO recheck eggs data later

                                            # if SalesEggsdata.objects.filter(date=eggs_sort_date,
                                            #                                 salesPerson=sales_person).first():
                                            #
                                            #     salesEggdata = SalesEggsdata.objects.get(date=eggs_sort_date,
                                            #                                              salesPerson=sales_person)
                                            #     salesEggdata.brown = salesEggdata.brown + orders_list_dict['Brown']
                                            #     salesEggdata.white = salesEggdata.white + orders_list_dict['White']
                                            #     salesEggdata.nutra = salesEggdata.nutra + orders_list_dict['Nutra']
                                            #     salesEggdata.save()
                                            # else:
                                            #     SalesEggsdata.objects.create(date=eggs_sort_date, salesPerson=sales_person,
                                            #                                  brown=orders_list_dict['Brown'],
                                            #                                  white=orders_list_dict['White'],
                                            #                                  nutra=orders_list_dict['Nutra'])
                                            #
                                            # if RetailerEggsdata.objects.filter(date=eggs_sort_date,
                                            #                                    retailer=retailer).first():
                                            #     retailerEggdata = RetailerEggsdata.objects.get(date=eggs_sort_date,
                                            #                                                    retailer=retailer)
                                            #     retailerEggdata.brown = retailerEggdata.brown + orders_list_dict[
                                            #         'Brown']
                                            #     retailerEggdata.white = retailerEggdata.white + orders_list_dict[
                                            #         'White']
                                            #     retailerEggdata.nutra = retailerEggdata.nutra + orders_list_dict[
                                            #         'Nutra']
                                            #     retailerEggdata.save()
                                            # else:
                                            #     RetailerEggsdata.objects.create(date=eggs_sort_date,
                                            #                                     retailer=retailer,
                                            #                                     brown=orders_list_dict['Brown'],
                                            #                                     white=orders_list_dict['White'],
                                            #                                     nutra=orders_list_dict['Nutra'])

                                            # order_obj.retailer.last_order_date = order_date
                                            # order_obj.retailer.save()

                                            # Now Make Invoice
                                            invoice = Invoice.objects.filter(order=order_obj).first()
                                            if not invoice:
                                                invoices = Invoice.objects.all()
                                                # might be possible model has no records so make sure to handle None
                                                invoice_max_id = invoices.aggregate(Max('id'))[
                                                                     'id__max'] + 1 if invoices else 1
                                                invoice_id = "E" + str(invoice_max_id)
                                                invoice = Invoice.objects.create(order=order_obj, invoice_id=invoice_id,
                                                                                 invoice_due=decimal.Decimal(row['Billing Amount'] - row['Amount']))
                                            if int(row['Billing Amount']) == int(row['Amount']):
                                                invoice.invoice_status = "Paid"
                                                invoice.save()
                                            else:
                                                invoice.invoice_status = "Pending"
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
                                                                                                salesPerson=sales_person,
                                                                                                transaction_id=transaction_id,
                                                                                                transaction_type="Debit",
                                                                                                transaction_amount=transaction_amount,
                                                                                                transaction_date=transaction_date)
                                            sales_transaction.retailer.amount_due = round(Decimal(
                                                sales_transaction.retailer.amount_due), 2) + round(Decimal(
                                                sales_transaction.transaction_amount), 2)
                                            sales_transaction.retailer.save()
                                            sales_transaction.invoices.add(invoice)
                                            sales_transaction.current_balance = sales_transaction.retailer.amount_due
                                            sales_transaction.save()

                                            if int(row['Amount']) >0:
                                                transactions = SalesTransaction.objects.all()
                                                # might be possible model has no records so make sure to handle None
                                                transaction_max_id = transactions.aggregate(Max('id'))[
                                                                         'id__max'] + 1 if transactions else 1
                                                transaction_id = "TR" + str(transaction_max_id)
                                                sales_transaction = SalesTransaction.objects.create(retailer=retailer,
                                                                                                    salesPerson=sales_person,
                                                                                                    transaction_id=transaction_id,
                                                                                                    transaction_type='Credit',
                                                                                                    transaction_amount=transaction_amount,
                                                                                                    transaction_date=transaction_date)
                                                sales_transaction.invoices.add(invoice)
                                                sales_transaction.save()
                                                row_payment_mode = row['Instant Pay']
                                                if row_payment_mode == 'PAYTM_WALLET' or row_payment_mode == 'RAZOR_PAY':
                                                    payment_mode_type = 'UPI'
                                                elif row_payment_mode == 'ICICI4178' or row_payment_mode == 'ICICI3901':
                                                    payment_mode_type = 'Cheque'
                                                elif row_payment_mode == 'CASH FREE':
                                                    payment_mode_type = 'CASH FREE'
                                                elif row_payment_mode == 'Return':
                                                    payment_mode_type = 'Return'
                                                else:
                                                    payment_mode_type = "Cash"
                                                Payment.objects.create(pay_choice='InstantPay',
                                                                       payment_type=payment_mode_type,
                                                                       payment_mode=row_payment_mode,
                                                                       pay_amount=transaction_amount,
                                                                       invoice=invoice,
                                                                       created_at=transaction_date,
                                                                       salesTransaction=sales_transaction)
                                                sales_transaction.retailer.amount_due = round(Decimal(
                                                    sales_transaction.retailer.amount_due), 2) - round(Decimal(
                                                    sales_transaction.transaction_amount), 2)
                                                sales_transaction.retailer.save()
                                                sales_transaction.current_balance = sales_transaction.retailer.amount_due
                                                sales_transaction.save()

                                            row["Upload Status"] = "Success"
                                            data['success'].append(
                                                {"index": index + 2, "shop_name": str(row['Shop Name']).strip(),
                                                 "success": "OK"})
                                            process_error.append("")
                                            row_processed.append("Success")
                                        except Exception as ex:
                                            print("Error %s" % ex.args[1])
                                            data['error'].append(
                                                {"index": index + 2, "shop_name": str(row['Shop Name']).strip(),
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
                        {"index": index + 2, "shop_name": str(row['Shop Name']).strip(), "bill_no": str(row['bill no']).strip(),
                         "error": "Retailer or SP Not Found"})
                    row_processed.append("Failed")
                    process_error.append("Retailer or SP Not Found")
                    continue

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


def upload_missing_payments(csv_file):
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
    data_header_list = ['Date','CODE', 'Shop Name','Retailer Id', 'bill no','Sales Person', 'Amount', 'Instant Pay', 'beat no.']
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
                print("*****")
                print(row['Shop Name'])
                print(row['Sales Person'])
                print("#####")
                print(str(index + 2))
                IST = pytz.timezone('Asia/Kolkata')
                datetime_ist = datetime.now(IST)
                orderId = str(row['bill no']).strip() + row['CODE']
                billNo = str(row['bill no']).strip()
                ordersCount = Order.objects.filter(bill_no=billNo).count()
                if ordersCount > 0:
                    retailer = Retailer.objects.filter(id=int(row['Retailer Id'])).first()
                    print(row['Date'].strip())
                    city_name = retailer.city.city_name
                    city_tag = city_name[:3]
                    sales_person = retailer.salesPersonProfile
                    transaction_date = datetime_ist.strptime(row['Date'].strip(), "%d/%m/%Y")
                    transaction_amount = round(Decimal(row['Amount']), 2)
                    order_obj = Order.objects.filter(bill_no=billNo).first()
                    invoice = Invoice.objects.filter(order=order_obj).first()
                    if invoice:
                        if int(row['Amount']) > 0:
                            invoice.invoice_due -= decimal.Decimal(row['Amount'])
                            if int(row['Amount']) >= int(invoice.invoice_due):
                                invoice.invoice_status  = "Paid"
                            invoice.save()

                            transactions = SalesTransaction.objects.all()
                            # might be possible model has no records so make sure to handle None
                            transaction_max_id = transactions.aggregate(Max('id'))[
                                                     'id__max'] + 1 if transactions else 1
                            transaction_id = "TR" + str(transaction_max_id)
                            sales_transaction = SalesTransaction.objects.create(retailer=retailer,
                                                                                salesPerson=sales_person,
                                                                                transaction_id=transaction_id,
                                                                                transaction_type='Credit',
                                                                                transaction_amount=transaction_amount,
                                                                                transaction_date=transaction_date)
                            sales_transaction.invoices.add(invoice)
                            sales_transaction.save()
                            row_payment_mode = row['Instant Pay']
                            if row_payment_mode == 'PAYTM_WALLET' or row_payment_mode == 'RAZOR_PAY':
                                payment_mode_type = 'UPI'
                            elif row_payment_mode == 'ICICI4178' or row_payment_mode == 'ICICI3901' or row_payment_mode == 'Neft':
                                payment_mode_type = 'Cheque'
                            elif row_payment_mode == 'CASH FREE':
                                payment_mode_type = 'CASH FREE'
                            elif row_payment_mode == 'Return':
                                payment_mode_type = 'Return'
                            else:
                                payment_mode_type = "Cash"
                            Payment.objects.create(pay_choice='LaterPay',
                                                   payment_type=payment_mode_type,
                                                   payment_mode=row_payment_mode,
                                                   pay_amount=transaction_amount,
                                                   invoice=invoice,
                                                   created_at=transaction_date,
                                                   salesTransaction=sales_transaction)
                            sales_transaction.retailer.amount_due = round(Decimal(
                                sales_transaction.retailer.amount_due), 2) - round(Decimal(
                                sales_transaction.transaction_amount), 2)
                            sales_transaction.retailer.save()
                            sales_transaction.current_balance = sales_transaction.retailer.amount_due
                            sales_transaction.save()

                        row["Upload Status"] = "Success"
                        data['success'].append(
                            {"index": index + 2, "shop_name": str(row['Shop Name']).strip(),
                             "success": "OK"})
                        process_error.append("")
                        row_processed.append("Success")
                    else:
                        print("Error %s" % "No invoice")
                        data['error'].append(
                            {"index": index + 2, "shop_name": str(row['Shop Name']).strip(), "error": "No invoice"})
                        row_processed.append("Failed")
                        process_error.append("No invoice")
                        continue
                else:
                    print("Error %s" % str(row['bill no']).strip() + row['CODE'])
                    data['error'].append(
                        {"index": index + 2, "shop_name": str(row['Shop Name']).strip(), "error": str(row['bill no']).strip() + row['CODE']})
                    row_processed.append("Failed")
                    process_error.append("No order")
                    continue

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