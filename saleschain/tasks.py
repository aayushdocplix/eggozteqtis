import json
from datetime import date, timedelta, datetime

import pytz
from celery import shared_task
from django.core.mail import send_mail
from django.http import HttpResponse

from Eggoz.celery import app
from Eggoz.settings import FROM_EMAIL
from base.response import Response
from order.models import Order
from order.models.Order import OrderReturnLine
from payment.models import SalesTransaction, Payment
from retailer.models import Retailer
from saleschain.models import SalesPersonProfile


@shared_task(bind=True, max_retries=3)
def sales_daily_report(self):
    yesterday = date.today() - timedelta(days=1)
    today = date.today()
    sales_persons = SalesPersonProfile.objects.all()
    indivisual_dict = {}
    for sales_person in sales_persons:
        indivisual_dict[sales_person.user.name] = {"total_orders": {}, "total_payment": 0, "total_replacement": {},
                                                   "total_returns": {}, "new_retailer": 0}
    report = {"overall": {"total_orders": {}, "total_payment": 0, "total_replacement": {}, "total_returns": {},
                          "new_retailer": 0}, "indivisual": indivisual_dict}

    delivered_orders = Order.objects.filter(delivery_date__gte=yesterday, delivery_date__lt=today,
                                            status__in=["delivered", "created"])
    print(delivered_orders)
    for order in delivered_orders:
        order_lines = order.lines.all()
        for order_line in order_lines:
            product_name = str(order_line.product.SKU_Count) + order_line.product.name[:1]
            # For Overall
            overall_total_orders = report['overall']['total_orders']
            if product_name in overall_total_orders.keys():
                overall_total_orders[product_name] = overall_total_orders[product_name] + order_line.quantity
            else:
                overall_total_orders[product_name] = order_line.quantity
            # For Indivisual
            indivisual_total_orders = report['indivisual'][order_line.order.salesPerson.user.name]['total_orders']
            if product_name in indivisual_total_orders.keys():
                indivisual_total_orders[product_name] = indivisual_total_orders[product_name] + order_line.quantity
            else:
                indivisual_total_orders[product_name] = order_line.quantity

    returned_orders = Order.objects.filter(return_picked_date__gte=yesterday, return_picked_date__lt=today,
                                           status="return_picked")
    print(returned_orders)
    for order in returned_orders:
        order_lines = order.lines.all()
        order_return_lines = OrderReturnLine.objects.filter(orderLine__in=order_lines, pickup_date__gte=yesterday,
                                                            pickup_date__lt=today)
        for order_return_line in order_return_lines:
            product_name = str(
                order_return_line.orderLine.product.SKU_Count) + order_return_line.orderLine.product.name[:1]
            # For Overall
            if order_return_line.line_type == "Replacement":
                overall_total_replacement = report['overall']['total_replacement']
                if product_name in overall_total_replacement.keys():
                    overall_total_replacement[product_name] = overall_total_replacement[
                                                                  product_name] + order_return_line.quantity
                else:
                    overall_total_replacement[product_name] = order_return_line.quantity

                # For Indivisual
                indivisual_total_replacements = \
                    report['indivisual'][order_return_line.orderLine.order.salesPerson.user.name][
                        'total_replacement']
                if product_name in indivisual_total_replacements.keys():
                    indivisual_total_replacements[product_name] = indivisual_total_replacements[
                                                                      product_name] + order_return_line.quantity
                else:
                    indivisual_total_replacements[product_name] = order_return_line.quantity
            elif order_return_line.line_type == "Refund":
                overall_total_returns = report['overall']['total_returns']
                if product_name in overall_total_returns.keys():
                    overall_total_returns[product_name] = overall_total_returns[
                                                              product_name] + order_return_line.quantity
                else:
                    overall_total_returns[product_name] = order_return_line.quantity

                # For Indivisual
                indivisual_total_returns = \
                    report['indivisual'][order_return_line.orderLine.order.salesPerson.user.name][
                        'total_returns']
                if product_name in indivisual_total_returns.keys():
                    indivisual_total_returns[product_name] = indivisual_total_returns[
                                                                 product_name] + order_return_line.quantity
                else:
                    indivisual_total_returns[product_name] = order_return_line.quantity

    sales_transactions = SalesTransaction.objects.filter(transaction_type="Credit", transaction_date__gte=yesterday,
                                                         transaction_date__lt=today)
    for sales_transaction in sales_transactions:
        report['overall']['total_payment'] = report['overall']['total_payment'] + sales_transaction.transaction_amount
        report['indivisual'][sales_transaction.salesPerson.user.name]['total_payment'] = \
            report['indivisual'][sales_transaction.salesPerson.user.name][
                'total_payment'] + sales_transaction.transaction_amount

    retailers = Retailer.objects.filter(onboarding_date__gte=yesterday, onboarding_date__lt=today)
    for retailer in retailers:
        report['overall']['new_retailer'] = report['overall']['new_retailer'] + 1
        report['indivisual'][retailer.salesPersonProfile.user.name]['new_retailer'] = \
            report['indivisual'][retailer.salesPersonProfile.user.name]['new_retailer'] + 1

    email_message = str(yesterday) + " Daily report for Branded Sales in NCR as follows:\n" + \
                    "Total Orders - " + make_order_in_format(
        report['overall']['total_orders']) + "\n" + "Total Payments collected - " + str(
        int(report['overall']['total_payment'])) + "\n" \
                                                   "Total Replacements  - " + make_order_in_format(
        report['overall']['total_replacement']) + "\n" \
                                                  "Total Returns  - " + make_order_in_format(
        report['overall']['total_returns']) + "\n" + "New Retailer onboarding  - " + str(
        int(report['overall']['new_retailer'])) + "\n" + make_indivisual_format(report['indivisual'])

    print(email_message)
    send_mail("Daily Sales Report", email_message, FROM_EMAIL,
              ['info@eggoz.in','mohit.mishra@eggoz.in','harshit@eggoz.in','ankur@eggoz.in'])

    return "Daily Sales Report Mailed Successfully"


def make_order_in_format(total_order_dict):
    total_order_format = None
    for key, value in total_order_dict.items():
        if total_order_format:
            total_order_format = total_order_format + "; " + str(value) + "X" + str(key)
        else:
            total_order_format = str(value) + "X" + str(key)
    return str(total_order_format)


def make_indivisual_format(indivisual_dict):
    indivisual_format = ""
    for key, value in indivisual_dict.items():
        sales_person_data = str(key) + ": \n" + "Total Orders - " + make_order_in_format(
            value['total_orders']) + "\n" + "Total Payments collected - " + str(
            int(value['total_payment'])) + "\n" + \
                            "Total Replacements  - " + make_order_in_format(
            value['total_replacement']) + "\n" \
                                          "Total Returns  - " + make_order_in_format(
            value['total_returns']) + "\n" + "New Retailer onboarding  - " + str(
            int(value['new_retailer'])) + "\n"

        indivisual_format = indivisual_format + "\n" + sales_person_data

    return indivisual_format

@app.task
def sales_bills_list(warehouse_id, from_date, to_date):
    print(warehouse_id)
    print(from_date)
    print(to_date)
    from_delivery_date = datetime.strptime(from_date, '%d/%m/%Y')
    to_delivery_date = datetime.strptime(to_date, '%d/%m/%Y')

    from_delivery_date = from_delivery_date.replace(hour=0, minute=0, second=0)
    to_delivery_date = to_delivery_date.replace(hour=0, minute=0, second=0)

    delta = timedelta(hours=23, minutes=59, seconds=59)
    from_delivery_date = from_delivery_date
    to_delivery_date = to_delivery_date + delta
    print(from_delivery_date)
    print(to_delivery_date)
    orders = Order.objects.filter(delivery_date__gte=from_delivery_date,status__in=["delivered", "completed"],warehouse_id=warehouse_id,
                                                             delivery_date__lte=to_delivery_date,is_trial=False,is_geb=False).order_by('id')

    sales_results = []
    for order in orders:
        sales_dict = get_order_data(order.id)
        sales_results.append(sales_dict)

    return sales_results


def get_order_data(order_id):
    order = Order.objects.get(id=order_id)
    city_id = order.retailer.city.id if order.retailer else \
        order.customer.shipping_address.city.id if order.customer.shipping_address.city else None
    city_name = order.retailer.city.city_name if order.retailer else \
        order.customer.shipping_address.city.city_name if order.customer.shipping_address.city else None
    sales_dict = {}

    instant_amount = 0
    instant_mode = ""
    later_mode = ""
    later_amount = 0
    later_mode_date = None
    if order.invoice:
        payments = Payment.objects.filter(invoice=order.invoice, salesTransaction__is_trial=False)
        if payments:
            for payment in payments:
                # print(payment.payment_mode)
                # print(payment.payment_type)
                if payment.pay_choice == "InstantPay":
                    instant_amount += payment.pay_amount
                    instant_mode += payment.payment_mode
                else:
                    later_amount += payment.pay_amount
                    later_mode += payment.payment_mode
                    later_mode_date = payment.created_at + timedelta(hours=5, minutes=30, seconds=0)
    order_date = order.date + timedelta(hours=5, minutes=30, seconds=0)
    order_delivery_date = order.delivery_date + timedelta(hours=5, minutes=30, seconds=0)
    sales_dict['Beat no.'] = order.retailer.beat_number if order.retailer else 0
    sales_dict['Del. Guy'] = order.distributor.user.name if order.distributor else ""
    sales_dict[
        'Operator'] = order.distributor.user.name if order.distributor else order.salesPerson.user.name if order.salesPerson else ""
    IST = pytz.timezone('Asia/Kolkata')
    sales_dict['Date'] = order_delivery_date.replace(tzinfo=IST).strftime(
        '%d/%m/%Y %H:%M:%S') if order.delivery_date else ""
    sales_dict['Party Name'] = str(order.retailer.code) if order.retailer else ""
    sales_dict['Sales Person'] = order.salesPerson.user.name if order.salesPerson else ""
    sales_dict['emp1'] = ""
    sales_dict['bill no'] = order.name
    sales_dict['Manual bill no'] = order.bill_no if order.bill_no else ""
    sales_dict['PENDING'] = int(order.invoice.invoice_due) if order.invoice else None
    sales_dict.update(get_order_line_dict(order)["Qty"])
    sales_dict['Instant Pay'] = instant_amount
    sales_dict['Mode'] = instant_mode
    sales_dict['C.D'] = ""
    sales_dict.update(get_order_line_dict(order)["Rate"])
    # sales_dict['Year'] = order_delivery_date.replace(tzinfo=IST).strftime('%Y') if order.delivery_date else None
    # sales_dict['Month'] = order_delivery_date.replace(tzinfo=IST).strftime(
    #     '%m') if order.delivery_date else None
    # sales_dict['Day'] = str(
    #     int(order_delivery_date.replace(tzinfo=IST).strftime('%d'))) if order.delivery_date else None
    sales_dict['amount'] = order.order_price_amount if order.order_price_amount else 0
    sales_dict['Acc pay'] = ""
    sales_dict['Later pay'] = later_amount
    sales_dict['Later pay date'] = later_mode_date.replace(tzinfo=IST).strftime(
        '%d/%m/%Y %H:%M:%S') if later_mode_date != None else ""
    sales_dict['pending'] = order.invoice.invoice_due if order.invoice else ""
    sales_dict['paid status'] = order.invoice.invoice_status if order.invoice else ""
    sales_dict['RETURN VALUE ADJUSTMENT'] = int(order.deviated_amount) if order.deviated_amount else 0
    sales_dict['order_date'] = order_date
    sales_dict['status'] = order.status
    sales_dict['secondary_status'] = order.secondary_status
    sales_dict['city_name'] = city_name
    sales_dict['city_id'] = city_id
    sales_dict['is_geb'] = order.is_geb
    sales_dict['is_geb_verified'] = order.is_geb_verified

    return sales_dict


def get_order_line_dict(order_obj):
    # Mapped Dict
    mapped_dict = {}
    mapped_dict['6W'] = ""
    mapped_dict['10W'] = ""
    mapped_dict['12W'] = ""
    mapped_dict['25W'] = ""
    mapped_dict['30W'] = ""

    mapped_dict['6B'] = ""
    mapped_dict['10B'] = ""
    mapped_dict['25B'] = ""
    mapped_dict['30B'] = ""

    mapped_dict['6N'] = ""
    mapped_dict['10N'] = ""

    mapped_rate_dict = {}
    mapped_rate_dict['6W R'] = ""
    mapped_rate_dict['10W R'] = ""
    mapped_rate_dict['12W R'] = ""
    mapped_rate_dict['25W R'] = ""
    mapped_rate_dict['30W R'] = ""

    mapped_rate_dict['6B R'] = ""
    mapped_rate_dict['10B R'] = ""
    mapped_rate_dict['25B R'] = ""
    mapped_rate_dict['30B R'] = ""

    mapped_rate_dict['6N R'] = ""
    mapped_rate_dict['10N R'] = ""

    order_lines = order_obj.lines.all()
    if order_lines:
        for order_line in order_lines:
            # print(str(order_line.product.SKU_Count) + order_line.product.name[:1])
            if str(order_line.product.SKU_Count) + order_line.product.name[:1] in mapped_dict.keys():
                mapped_dict[str(order_line.product.SKU_Count) + order_line.product.name[:1]] = order_line.quantity
                mapped_rate_dict[str(order_line.product.SKU_Count) + order_line.product.name[:1] +" R"] = order_line.single_sku_rate

    return {"Qty":mapped_dict, "Rate":mapped_rate_dict}
