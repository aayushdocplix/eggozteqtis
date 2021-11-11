import asyncio
import decimal
import json
from datetime import datetime, timedelta

import pytz
import requests
from asgiref.sync import async_to_sync
from django.core.mail import send_mail
from django.db.models import Max
from django.shortcuts import redirect
from django.template import loader
from django.utils import timezone
from django.views.generic import TemplateView
from num2words import num2words
from rest_framework import viewsets, permissions, mixins, decorators, status
from order.tasks import ecomm_create_order

from Eggoz.settings import PAYMENT_SUCCESS_REDIRECT_URL, CASHFREE_BASE_URL, \
    CASHFREE_APP_ID, CASHFREE_SECRET_KEY, PAYMENT_FAILED_REDIRECT_UNPAID_URL, PAYMENT_FAILED_REDIRECT_FAIL_URL, \
    PAYMENT_SUCCESS_REDIRECT_WALLET_URL, PAYMENT_SUCCESS_REDIRECT_CARD_URL, CURRENT_ZONE, TIME_ZONE, FROM_EMAIL
from base.response import BadRequest, Forbidden, Created, Ok
from base.views import PaginationWithNoLimit
from custom_auth.models import UserProfile
from distributionchain.models import DistributionPersonProfile
from ecommerce.models import CashFreeTransaction, WalletRecharge, CustomerWallet, CustomerPromoWallet, \
    CustomerVoucherPromo, Customer
from ecommerce.models.Subscriptions import CustomerMemberShip, CustomerSubscription
from finance.models import FinanceProfile
from order.api.serializers import EcommerceOrderCreateSerializer, OrderLineSerializer
from order.models import Order, OrderEvent
from order.models.Order import OrderPendingTransaction
from payment.api.serializers import PaymentValidationSerializer, \
    SalesTransactionCreateSerializer, PaymentSerializer, \
    SalesTransactionShortSerializer
from payment.models import SalesTransaction, Payment, Invoice, InvoiceLine
from retailer.models import Retailer
from saleschain.models import SalesPersonProfile

from django_filters import rest_framework as filters
from rest_framework import viewsets, mixins, permissions
from rest_framework.response import Response


class IndexView(TemplateView):
    template_name = 'custom_auth/home.html'


class SalesTransactionViewset(viewsets.GenericViewSet, mixins.CreateModelMixin):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = SalesTransactionCreateSerializer
    pagination_class = PaginationWithNoLimit
    queryset = SalesTransaction.objects.all()

    def create(self, request, *args, **kwargs):
        print(request.data)
        data = request.data
        user_profile = UserProfile.objects.filter(user=request.user, department__name__in=['Sales']).first()
        if user_profile:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            # Validate Payment Modes
            payment_modes = json.loads(data.get('payment_modes', []))
            if len(payment_modes) > 0:
                for payment_mode in payment_modes:
                    payment_mode_serializer = PaymentValidationSerializer(data=payment_mode)
                    payment_mode_serializer.is_valid(raise_exception=True)
            else:
                return BadRequest({'error_type': "ValidationError",
                                   'errors': [{'message': "Payment Modes can not be empty"}]})
            salesPersonProfile = SalesPersonProfile.objects.filter(user=request.user).first()
            transactions = SalesTransaction.objects.all()
            # might be possible model has no records so make sure to handle None
            transaction_max_id = transactions.aggregate(Max('id'))['id__max'] + 1 if transactions else 1
            transaction_id = "TR" + str(transaction_max_id)
            transaction_amount = request.data.get('transaction_amount')
            if request.data.get('transaction_date'):
                transaction_date = datetime.strptime(request.data.get('transaction_date'), "%Y-%m-%d %H:%M")
            else:
                transaction_date = timezone.now
            sales_transaction = serializer.save(transaction_amount=transaction_amount, salesPerson=salesPersonProfile,
                                                transaction_date=transaction_date,
                                                transaction_id=transaction_id)
            for payment_mode in payment_modes:
                payment_mode['salesTransaction'] = sales_transaction
                payment = Payment(**payment_mode)
                payment.save()

            # TODO Update Amount Due of Retailer while creating a transaction
            if sales_transaction.retailer:
                if sales_transaction.transaction_type == "Credit":
                    sales_transaction.retailer.amount_due = decimal.Decimal(
                        sales_transaction.retailer.amount_due) - decimal.Decimal(sales_transaction.transaction_amount)
                    sales_transaction.retailer.save()
                    sales_transaction.current_balance = sales_transaction.retailer.amount_due
                    sales_transaction.save()

                    # Handle Retailer Pending Invoices
                    transaction_amount = sales_transaction.transaction_amount
                    # pending_invoices = Invoice.objects.filter(retailer=sales_transaction.retailer,invoice_status="Pending")
                    pending_invoices = Invoice.objects.filter(order__in=sales_transaction.retailer.OrderRetailer.all(),
                                                              invoice_status="Pending")
                    print(pending_invoices)
                    for pending_invoice in pending_invoices:
                        if int(transaction_amount) > 0:
                            if int(pending_invoice.invoice_due) <= int(transaction_amount):
                                InvoiceLine.objects.create(invoice=pending_invoice,
                                                           amount_received=pending_invoice.invoice_due)
                                transaction_amount = int(transaction_amount) - int(pending_invoice.invoice_due)
                                pending_invoice.invoice_status = 'Paid'
                                pending_invoice.invoice_due = decimal.Decimal(0)
                                pending_invoice.save()
                                sales_transaction.invoices.add(pending_invoice)
                            else:
                                InvoiceLine.objects.create(invoice=pending_invoice,
                                                           amount_received=transaction_amount)
                                pending_invoice.invoice_due = pending_invoice.invoice_due - decimal.Decimal(
                                    transaction_amount)
                                pending_invoice.save()
                                sales_transaction.invoices.add(pending_invoice)
                                break
                        else:
                            break

                if sales_transaction.transaction_type == "Debit":
                    sales_transaction.retailer.amount_due = decimal.Decimal(
                        sales_transaction.retailer.amount_due) + decimal.Decimal(sales_transaction.transaction_amount)
                    sales_transaction.retailer.save()
                    sales_transaction.current_balance = sales_transaction.retailer.amount_due
                    sales_transaction.save()

            return Created({})
        else:
            return Forbidden({'error_type': "permission_denied",
                              'errors': [{'message': "You do not have permission to perform this action."}]})


class SalesTransactionAmountViewset(viewsets.GenericViewSet, mixins.ListModelMixin):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = SalesTransactionShortSerializer
    queryset = SalesTransaction.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('retailer', 'salesPerson', 'distributor')

    def list(self, request, *args, **kwargs):
        salesPersonId = request.GET.get('salesPersonId')
        queryset = self.filter_queryset(self.get_queryset()) \
            .filter(salesPerson_id=salesPersonId, is_verified=False)

        querysetCredit = self.filter_queryset(self.get_queryset()) \
            .filter(salesPerson_id=salesPersonId, transaction_type="credit", is_verified=False)
        amount = decimal.Decimal(0.000)
        # if queryset:
        #     for transaction in queryset:
        #         amount += transaction.transaction_amount
        serializer = self.get_serializer(queryset, many=True)
        serializerCredit = self.get_serializer(querysetCredit, many=True)
        return Response({"results": {"results": serializer.data, "creditresults": serializerCredit.data, "amount": 0}})


class HandleReturnAfterPayment(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data
        print(request.data)
        data_dict = dict(data).copy()
        txStatus = data.get('txStatus', '')
        orderId = data.get('orderId')
        cash_free_transaction = CashFreeTransaction.objects.filter(transaction_id=orderId).first()

        if txStatus == 'SUCCESS':

            url = "%s/api/v1/order/info/status" % (CASHFREE_BASE_URL)

            payload = {'appId': CASHFREE_APP_ID,
                       'secretKey': CASHFREE_SECRET_KEY,
                       'orderId': orderId}
            files = [

            ]
            headers = {}
            response = requests.request("POST", url, headers=headers, data=payload, files=files)
            print(response.text)
            payment_status_response = json.loads(response.text)

            if payment_status_response.get('txStatus') == 'SUCCESS' and payment_status_response.get(
                    'orderStatus') == 'PAID':
                ecomm_order = Order.objects.filter(id=cash_free_transaction.order.id).first()
                if ecomm_order.pay_by_wallet:
                    wallet = cash_free_transaction.wallet
                    customer_wallet = CustomerWallet.objects.get(id=wallet.id)
                    promoWallets = CustomerPromoWallet.objects.filter(wallet_id=wallet.id, is_active=True,
                                                                      expired_at__gte=datetime.now(
                                                                          tz=CURRENT_ZONE)).order_by(
                        'expired_at')
                    for promoWallet in promoWallets:
                        promoWallet.balance = 0.000
                        promoWallet.is_active = False
                        promoWallet.save()
                    amount = cash_free_transaction.transaction_amount
                    wallet_recharge = WalletRecharge.objects.create(
                        transaction=cash_free_transaction,
                        wallet_id=wallet.id,
                        amount=amount
                    )
                    customer_wallet.total_balance = 0.000
                    customer_wallet.recharge_balance = 0.000
                    customer_wallet.save()
                    redirect_url = PAYMENT_SUCCESS_REDIRECT_WALLET_URL
                    data_dict["status"] = "PaidByWallet"
                else:
                    amount = cash_free_transaction.transaction_amount
                    redirect_url = PAYMENT_SUCCESS_REDIRECT_CARD_URL
                    data_dict["status"] = "Paid"
                # Handle Order Event and order

                ecomm_order.status = "created"
                ecomm_order.order_payment_status = "Paid"
                ecomm_order.save()

                order_obj = ecomm_order

                order_lines = order_obj.lines.all()
                purchase_details = []
                total_amount = 0
                for order_line in order_lines:
                    product = order_line.product
                    print(product)

                    if product:
                        purchase_detail = {
                            "item_description": "%s (%s SKU)" % (product.name, product.SKU_Count),
                            "hsn_sac": product.productDivision.hsn,
                            "sku_type": product.SKU_Count,
                            "quantity": order_line.quantity,
                            "sku_rate": round(product.current_price,
                                              2)
                        }
                        purchase_detail['amount'] = round(
                            purchase_detail['sku_rate'] * purchase_detail['quantity'], 2)
                        purchase_details.append(purchase_detail)
                        total_amount = round(total_amount + purchase_detail['amount'], 2)
                address = {
                    "address_name": order_obj.shipping_address.address_name if order_obj.shipping_address.address_name else None,
                    "building_address": order_obj.shipping_address.building_address if order_obj.shipping_address.building_address else None,
                    "street_address": order_obj.shipping_address.street_address if order_obj.shipping_address.street_address else None,
                    "city_name": order_obj.shipping_address.city.city_name if order_obj.shipping_address.city else None,
                    "locality": order_obj.shipping_address.ecommerce_sector.sector_name if order_obj.shipping_address.ecommerce_sector else None,
                    "landmark": order_obj.shipping_address.landmark if order_obj.shipping_address.landmark else None,
                    "name": order_obj.shipping_address.name if order_obj.shipping_address.name else request.user.name,
                    "pinCode": order_obj.shipping_address.pinCode if order_obj.shipping_address.pinCode else None,
                    "phone_no": order_obj.shipping_address.phone_no if order_obj.shipping_address.phone_no else request.user.phone_no,
                }
                order_data = {"order_id": order_obj.orderId, "address": address,
                              "order_total_amount": order_obj.order_price_amount,
                              "order_total_in_words": num2words(order_obj.order_price_amount),
                              "purchase_details": purchase_details}
                html_message = loader.render_to_string(
                    'invoice/order_email.html',
                    order_data
                )
                send_mail(subject="Order " + str(order_obj.orderId) + " has  been placed succesfully",
                          message="Message", from_email=FROM_EMAIL,
                          recipient_list=['po@eggoz.in', 'rohit.kumar@eggoz.in'], html_message=html_message)
                OrderEvent.objects.create(order=order_obj, type="created", user=order_obj.customer.user)

                # Handle Invoice
                invoice = Invoice.objects.filter(order=ecomm_order).first()
                if not invoice:
                    invoices = Invoice.objects.all()
                    # might be possible model has no records so make sure to handle None
                    invoice_max_id = invoices.aggregate(Max('id'))['id__max'] + 1 if invoices else 1
                    invoice_id = "E" + str(invoice_max_id)
                    invoice = Invoice.objects.create(invoice_id=invoice_id, order=ecomm_order, invoice_status="Paid")

                OrderEvent.objects.create(order=ecomm_order, type="order_marked_as_paid",
                                          user=ecomm_order.customer.user)
                # Handle Sales Transactions
                transactions_first = SalesTransaction.objects.all()
                # might be possible model has no records so make sure to handle None
                transaction_max_id_first = transactions_first.aggregate(Max('id'))[
                                               'id__max'] + 1 if transactions_first else 1
                transaction_id_first = "TR" + str(transaction_max_id_first)
                st_credit = SalesTransaction.objects.create(customer=ecomm_order.customer,
                                                            transaction_id=transaction_id_first,
                                                            transaction_type="Credit",
                                                            transaction_date=ecomm_order.date,
                                                            transaction_amount=amount)
                st_credit.invoices.add(invoice)
                st_credit.save()
                # Handle Sales Transactions
                transactions_second = SalesTransaction.objects.all()
                # might be possible model has no records so make sure to handle None
                transaction_max_id_second = transactions_second.aggregate(Max('id'))[
                                                'id__max'] + 1 if transactions_second else 1
                transaction_id_second = "TR" + str(transaction_max_id_second)
                st_debit = SalesTransaction.objects.create(customer=ecomm_order.customer,
                                                           transaction_id=transaction_id_second,
                                                           transaction_type="Debit", transaction_date=ecomm_order.date,
                                                           transaction_amount=ecomm_order.order_price_amount)
                st_debit.invoices.add(invoice)
                st_debit.save()

                cash_free_transaction.transaction_status = "Success"

                # redirect_url = PAYMENT_SUCCESS_REDIRECT_URL
            else:
                redirect_url = PAYMENT_FAILED_REDIRECT_UNPAID_URL
                data_dict["status"] = "Unpaid"
                cash_free_transaction.transaction_status = "UnPaid"
        else:
            redirect_url = PAYMENT_FAILED_REDIRECT_FAIL_URL
            data_dict["status"] = "Fail"
            cash_free_transaction.transaction_status = "FAILURE"
        cash_free_transaction.transaction_type = data.get('paymentMode')
        cash_free_transaction.reference_id = data.get('referenceId', '')
        cash_free_transaction.signature_response = data.get('signature', '')
        cash_free_transaction.transaction_message = data.get('txMsg', '')
        cash_free_transaction.payment_return_response = data
        cash_free_transaction.save()
        final_url = redirect_url + "&type=ecomm_order&orderId=%s" % (data.get('orderId'))
        return redirect(final_url, transaction_response=data_dict)


class HandleReturnAfterWalletRecharge(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data
        print(request.data)
        data_dict = dict(data).copy()
        print(data_dict)
        txStatus = data.get('txStatus', '')
        orderId = data.get('orderId')
        cash_free_transaction = CashFreeTransaction.objects.filter(transaction_id=orderId).first()
        if txStatus == 'SUCCESS':
            url = "%s/api/v1/order/info/status" % (CASHFREE_BASE_URL)

            payload = {'appId': CASHFREE_APP_ID,
                       'secretKey': CASHFREE_SECRET_KEY,
                       'orderId': orderId}
            files = [

            ]
            headers = {}
            response = requests.request("POST", url, headers=headers, data=payload, files=files)
            print(response.text)
            payment_status_response = json.loads(response.text)
            if payment_status_response.get('txStatus') == 'SUCCESS' and payment_status_response.get(
                    'orderStatus') == 'PAID':

                # Handle  Customer Wallet

                wallet = cash_free_transaction.wallet
                customer_wallet = CustomerWallet.objects.get(id=wallet.id)
                if cash_free_transaction.voucher:
                    recharge_voucher = cash_free_transaction.voucher
                    amount = decimal.Decimal(recharge_voucher.amount)
                    promo_amount = decimal.Decimal(recharge_voucher.promo)
                    wallet_recharge = WalletRecharge.objects.create(
                        transaction=cash_free_transaction,
                        wallet_id=wallet.id,
                        voucher_id=recharge_voucher.id,
                        amount=amount,
                        promo_amount=promo_amount
                    )
                    customer_wallet.total_balance += amount + promo_amount
                    customer_wallet.recharge_balance += amount
                    customer_wallet.save()
                    time_difference = datetime.now(tz=CURRENT_ZONE) + timedelta(days=28)
                    customer_promo_wallet = CustomerPromoWallet.objects.create(wallet_id=wallet.id,
                                                                               balance=promo_amount,
                                                                               is_active=True,
                                                                               published_at=datetime.now(
                                                                                   tz=CURRENT_ZONE),
                                                                               expired_at=time_difference)
                    customer_promo_wallet.save()

                    customer_voucher_promo = CustomerVoucherPromo.objects.create(voucher_id=recharge_voucher.id,
                                                                                 customer_id=customer_wallet.customer.id,
                                                                                 published_at=datetime.now(
                                                                                     tz=CURRENT_ZONE),
                                                                                 expired_at=time_difference)
                    customer_voucher_promo.save()

                    transaction_date = datetime.now(tz=CURRENT_ZONE)
                    # Handle Sales Transactions
                    transactions_first = SalesTransaction.objects.all()
                    # might be possible model has no records so make sure to handle None
                    transaction_max_id_first = transactions_first.aggregate(Max('id'))[
                                                   'id__max'] + 1 if transactions_first else 1
                    transaction_id_first = "TR" + str(transaction_max_id_first)
                    SalesTransaction.objects.create(customer_id=customer_wallet.customer.id,
                                                    transaction_id=transaction_id_first,
                                                    transaction_type="Credit", transaction_date=transaction_date,
                                                    transaction_amount=amount)

                    transactions_second = SalesTransaction.objects.all()
                    # might be possible model has no records so make sure to handle None
                    transaction_max_id_second = transactions_second.aggregate(Max('id'))[
                                                    'id__max'] + 1 if transactions_second else 1
                    transaction_id_second = "TR" + str(transaction_max_id_second)
                    SalesTransaction.objects.create(customer_id=customer_wallet.customer.id,
                                                    transaction_id=transaction_id_second,
                                                    transaction_type="Promo", transaction_date=transaction_date,
                                                    transaction_amount=promo_amount)
                else:
                    amount = cash_free_transaction.transaction_amount
                    wallet_recharge = WalletRecharge.objects.create(
                        transaction=cash_free_transaction,
                        wallet_id=wallet.id,
                        amount=amount
                    )
                    customer_wallet.total_balance += amount
                    customer_wallet.recharge_balance += amount
                    customer_wallet.save()
                    transaction_date = datetime.now(tz=CURRENT_ZONE)
                    # Handle Sales Transactions
                    transactions = SalesTransaction.objects.all()
                    # might be possible model has no records so make sure to handle None
                    transaction_max_id = transactions.aggregate(Max('id'))['id__max'] + 1 if transactions else 1
                    transaction_id = "TR" + str(transaction_max_id)
                    SalesTransaction.objects.create(customer_id=customer_wallet.customer.id,
                                                    transaction_id=transaction_id,
                                                    transaction_type="Credit", transaction_date=transaction_date,
                                                    transaction_amount=amount)

                cash_free_transaction.transaction_status = "Success"
                redirect_url = PAYMENT_SUCCESS_REDIRECT_CARD_URL
                data_dict["status"] = "Success"
            else:
                redirect_url = PAYMENT_FAILED_REDIRECT_UNPAID_URL
                data_dict["status"] = "Unpaid"
                cash_free_transaction.transaction_status = "UnPaid"
        else:
            redirect_url = PAYMENT_FAILED_REDIRECT_FAIL_URL
            data_dict["status"] = "Fail"
            cash_free_transaction.transaction_status = "Failure"
        cash_free_transaction.transaction_type = data.get('paymentMode')
        cash_free_transaction.reference_id = data.get('referenceId', '')
        cash_free_transaction.signature_response = data.get('signature', '')
        cash_free_transaction.transaction_message = data.get('txMsg', '')
        cash_free_transaction.payment_return_response = data
        cash_free_transaction.save()

        final_url = redirect_url + "&type=wallet_recharge&orderId=%s" % (data.get('orderId'))
        return redirect(final_url, transaction_response=data_dict)


class HandleReturnAfterMemberShipRecharge(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data
        print(request.data)
        data_dict = dict(data).copy()
        txStatus = data.get('txStatus', '')
        orderId = data.get('orderId')
        cash_free_transaction = CashFreeTransaction.objects.filter(transaction_id=orderId).first()

        if txStatus == 'SUCCESS':

            url = "%s/api/v1/order/info/status" % (CASHFREE_BASE_URL)

            payload = {'appId': CASHFREE_APP_ID,
                       'secretKey': CASHFREE_SECRET_KEY,
                       'orderId': orderId}
            files = [

            ]
            headers = {}
            response = requests.request("POST", url, headers=headers, data=payload, files=files)
            print(response.text)
            payment_status_response = json.loads(response.text)

            if payment_status_response.get('txStatus') == 'SUCCESS' and payment_status_response.get(
                    'orderStatus') == 'PAID':
                wallet = cash_free_transaction.wallet
                customer_wallet = CustomerWallet.objects.get(id=wallet.id)
                customer = customer_wallet.customer
                amount = cash_free_transaction.transaction_amount
                CustomerMemberShip.objects.create(customer=customer,
                                                  memberShip=cash_free_transaction.memberShipRequest.memberShip,
                                                  start_date=cash_free_transaction.memberShipRequest.start_date,
                                                  expiry_date=cash_free_transaction.memberShipRequest.expiry_date)
                if cash_free_transaction.pay_by_wallet:

                    customer_wallet.total_balance -= amount
                    customer_wallet.recharge_balance -= amount
                    customer_wallet.save()
                    redirect_url = PAYMENT_SUCCESS_REDIRECT_WALLET_URL
                    data_dict["status"] = "PaidByWallet"
                else:

                    redirect_url = PAYMENT_SUCCESS_REDIRECT_CARD_URL
                    data_dict["status"] = "Paid"
                # Handle Order Event and order

                order_data = {}
                html_message = loader.render_to_string(
                    'invoice/order_email.html',
                    order_data
                )

                cash_free_transaction.transaction_status = "Success"

                # redirect_url = PAYMENT_SUCCESS_REDIRECT_URL
            else:
                redirect_url = PAYMENT_FAILED_REDIRECT_UNPAID_URL
                data_dict["status"] = "Unpaid"
                cash_free_transaction.transaction_status = "UnPaid"
        else:
            redirect_url = PAYMENT_FAILED_REDIRECT_FAIL_URL
            data_dict["status"] = "Fail"
            cash_free_transaction.transaction_status = "FAILURE"
        cash_free_transaction.transaction_type = data.get('paymentMode')
        cash_free_transaction.reference_id = data.get('referenceId', '')
        cash_free_transaction.signature_response = data.get('signature', '')
        cash_free_transaction.transaction_message = data.get('txMsg', '')
        cash_free_transaction.payment_return_response = data
        cash_free_transaction.save()
        final_url = redirect_url + "&type=ecomm_membership&orderId=%s" % (data.get('orderId'))
        return redirect(final_url, transaction_response=data_dict)


class HandleReturnAfterSubscriptionRecharge(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data
        print(request.data)
        data_dict = dict(data).copy()
        txStatus = data.get('txStatus', '')
        orderId = data.get('orderId')
        cash_free_transaction = CashFreeTransaction.objects.filter(transaction_id=orderId).first()

        if txStatus == 'SUCCESS':

            url = "%s/api/v1/order/info/status" % (CASHFREE_BASE_URL)

            payload = {'appId': CASHFREE_APP_ID,
                       'secretKey': CASHFREE_SECRET_KEY,
                       'orderId': orderId}
            files = [

            ]
            headers = {}
            response = requests.request("POST", url, headers=headers, data=payload, files=files)
            print(response.text)
            payment_status_response = json.loads(response.text)

            if payment_status_response.get('txStatus') == 'SUCCESS' and payment_status_response.get(
                    'orderStatus') == 'PAID':
                wallet = cash_free_transaction.wallet
                customer_wallet = CustomerWallet.objects.get(id=wallet.id)
                customer = customer_wallet.customer
                amount = cash_free_transaction.transaction_amount
                customersubscription = CustomerSubscription.objects.create(customer=customer,
                                                                           subscription=cash_free_transaction.subscriptionRequest.subscription,
                                                                           product=cash_free_transaction.subscriptionRequest.product,
                                                                           quantity=cash_free_transaction.subscriptionRequest.quantity,
                                                                           single_sku_rate=cash_free_transaction.subscriptionRequest.single_sku_rate,
                                                                           single_sku_mrp=cash_free_transaction.subscriptionRequest.single_sku_mrp,
                                                                           slot=cash_free_transaction.subscriptionRequest.slot,
                                                                           start_date=cash_free_transaction.subscriptionRequest.start_date,
                                                                           expiry_date=cash_free_transaction.subscriptionRequest.expiry_date)
                days_added = []
                for day in cash_free_transaction.subscriptionRequest.days.all():
                    days_added.append(day.id)
                    customersubscription.days.add(day)

                if cash_free_transaction.pay_by_wallet:

                    customer_wallet.total_balance -= amount
                    customer_wallet.recharge_balance -= amount
                    customer_wallet.save()
                    redirect_url = PAYMENT_SUCCESS_REDIRECT_WALLET_URL
                    data_dict["status"] = "PaidByWallet"
                else:
                    redirect_url = PAYMENT_SUCCESS_REDIRECT_CARD_URL
                    data_dict["status"] = "Paid"
                # Handle Order Event and order
                print(cash_free_transaction.id)
                print(customersubscription.id)
                print(customersubscription.customer.id)
                ecomm_create_order.delay(cash_free_transaction.id, customersubscription.id,
                                         customersubscription.customer.id)

                cash_free_transaction.transaction_status = "Success"

                # redirect_url = PAYMENT_SUCCESS_REDIRECT_URL
            else:
                redirect_url = PAYMENT_FAILED_REDIRECT_UNPAID_URL
                data_dict["status"] = "Unpaid"
                cash_free_transaction.transaction_status = "UnPaid"
        else:
            redirect_url = PAYMENT_FAILED_REDIRECT_FAIL_URL
            data_dict["status"] = "Fail"
            cash_free_transaction.transaction_status = "FAILURE"
        cash_free_transaction.transaction_type = data.get('paymentMode')
        cash_free_transaction.reference_id = data.get('referenceId', '')
        cash_free_transaction.signature_response = data.get('signature', '')
        cash_free_transaction.transaction_message = data.get('txMsg', '')
        cash_free_transaction.payment_return_response = data
        cash_free_transaction.save()
        final_url = redirect_url + "&type=ecomm_subscription&orderId=%s" % (data.get('orderId'))
        return redirect(final_url, transaction_response=data_dict)


class HandleNotifyAfterPayment(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data
        print(data)
        return Ok(data)


class SalesPaymentViewSet(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        data = request.data
        user = request.user
        print(data)
        paymentResponse = {"payment": []}
        sales_profile = UserProfile.objects.filter(user=request.user, department__name__in=['Sales']).first()
        finance_profile = UserProfile.objects.filter(user=request.user, department__name__in=['Finance']).first()
        distributor_profile = UserProfile.objects.filter(user=request.user,
                                                         department__name__in=['Distribution', 'Sales']).first()
        if sales_profile or distributor_profile or finance_profile:
            # print(sales_profile)
            # transaction_amount date retailer_id invoice_ids
            transaction_data = request.data.get('sales_transaction', None)

            if transaction_data:
                transaction_data = json.loads(transaction_data)
                serializer = SalesTransactionCreateSerializer(data=transaction_data)
                serializer.is_valid(raise_exception=True)

                # Validate Payment Modes
                # payment_modes = transaction_data.get('payment_modes', [])
                # if len(payment_modes) > 0:
                #     for payment_mode in payment_modes:
                #         payment_mode_serializer = PaymentValidationSerializer(data=payment_mode)
                #         payment_mode_serializer.is_valid(raise_exception=True)
                # else:
                #     return BadRequest({'error_type': "ValidationError",
                #                        'errors': [{'message': "Payment Modes can not be empty"}]})

                retailer_id = transaction_data.get('retailer_id')
                salesRetailer = Retailer.objects.get(id=int(retailer_id))

                is_trial = False
                if salesRetailer.code == "T1001* Trial" or salesRetailer.code == "D2670* Paul Trial":
                    is_trial = True
                # Create Credit Transaction
                transactions = SalesTransaction.objects.all()
                # might be possible model has no records so make sure to handle None
                transaction_max_id = transactions.aggregate(Max('id'))['id__max'] + 1 if transactions else 1
                transaction_id = "TR" + str(transaction_max_id)
                transaction_amount = transaction_data.get('transaction_amount')

                transaction_date = datetime.strptime(transaction_data.get('transaction_date'),
                                                     "%Y-%m-%d %H:%M")
                # transaction_date = CURRENT_ZONE.localize(transaction_date)
                if sales_profile:
                    salesPersonProfile = SalesPersonProfile.objects.filter(user=user).first()
                    sales_transaction = serializer.save(transaction_amount=transaction_amount,
                                                        salesPerson=salesPersonProfile,
                                                        transaction_type="Credit",
                                                        is_trial=is_trial,
                                                        transaction_date=transaction_date,
                                                        transaction_id=transaction_id, retailer_id=retailer_id)
                elif distributor_profile:
                    distributionPersonProfile = DistributionPersonProfile.objects.filter(user=user).first()
                    sales_transaction = serializer.save(transaction_amount=transaction_amount,
                                                        distributor=distributionPersonProfile,
                                                        transaction_type="Credit",
                                                        is_trial=is_trial,
                                                        transaction_date=transaction_date,
                                                        transaction_id=transaction_id, retailer_id=retailer_id)
                else:
                    financeProfile = FinanceProfile.objects.filter(user=user).first()
                    sales_transaction = serializer.save(transaction_amount=transaction_amount,
                                                        salesPerson=salesRetailer.salesPersonProfile,
                                                        financePerson=financeProfile,
                                                        transaction_type="Credit",
                                                        is_trial=is_trial,
                                                        transaction_date=transaction_date,
                                                        transaction_id=transaction_id, retailer_id=retailer_id)

                if request.data.get('prev_order_id'):
                    order_id = int(request.data.get('prev_order_id'))
                    order = Order.objects.filter(id=order_id).first()
                    order.pending_transaction = sales_transaction.id
                    if data.get('beat_assignment'):
                        OrderPendingTransaction.objects.create(order_id=order_id,
                                                               pending_transaction=sales_transaction.id,
                                                               beat_assignment_id=data.get('beat_assignment'),
                                                               pending_collection_date=sales_transaction.transaction_date)
                    else:
                        OrderPendingTransaction.objects.create(order_id=order_id,
                                                               pending_transaction=sales_transaction.id,
                                                               pending_collection_date=sales_transaction.transaction_date)
                    order.save()
                sales_transaction.retailer.amount_due = decimal.Decimal(
                    sales_transaction.retailer.amount_due) - decimal.Decimal(
                    sales_transaction.transaction_amount)
                sales_transaction.retailer.save()
                sales_transaction.current_balance = sales_transaction.retailer.amount_due
                sales_transaction.save()

                # for payment_mode in payment_modes:
                #     payment_mode['salesTransaction'] = sales_transaction
                #     payment = Payment(**payment_mode)
                #     payment.save()

                # Handle Retailer Pending Invoices
                invoice_details = data.get('invoice_details', [])
                invoicesData = json.loads(invoice_details)
                print(invoicesData)
                for invoiceData in invoicesData:
                    print(invoiceData)
                    invoice_id = invoiceData['id']
                    paid_amount = decimal.Decimal(invoiceData['paid_amount'])
                    invoice = Invoice.objects.get(pk=invoice_id)
                    due = invoice.invoice_due
                    invoice.invoice_due -= paid_amount

                    if int(due - paid_amount) < 1 and not int(due - paid_amount) <= -1:
                        invoice.invoice_status = "Paid"
                        print("paid")
                    invoice.save()
                    InvoiceLine.objects.create(invoice=invoice, amount_received=paid_amount,
                                               received_at=transaction_date,
                                               sales_transaction=sales_transaction)
                    invoice.sales_invoices.add(sales_transaction)

                    # TODO payment choice wrt date
                    if invoice.created_at:
                        print(invoice.created_at + timedelta(hours=5, minutes=30))
                        created_at = invoice.created_at + timedelta(hours=5, minutes=30)
                        print(invoice.order.delivery_date)

                        print(sales_transaction.transaction_date)
                        if created_at.date() == sales_transaction.transaction_date.date():
                            payment_choice = transaction_data.get('payment_choice', "InstantPay")
                        else:
                            payment_choice = transaction_data.get('payment_choice', "LaterPay")
                    else:
                        payment_choice = transaction_data.get('payment_choice', "LaterPay")
                    payment_type = transaction_data.get('payment_type', "Cash")
                    payment = Payment.objects.create(payment_type=payment_type,
                                                     pay_choice=payment_choice,
                                                     invoice=invoice,
                                                     pay_amount=paid_amount,
                                                     created_at=transaction_date,
                                                     salesTransaction=sales_transaction)
                    if payment_type == "Cash":
                        payment_mode = transaction_data.get('payment_mode', "PETTY CASH").upper()
                    elif payment_type == "Cheque":
                        payment_mode = transaction_data.get('payment_mode', "CHEQUE").upper()
                        cheque_number = transaction_data.get('cheque_number')
                        payment.cheque_number = cheque_number
                    else:
                        payment_mode = transaction_data.get('payment_mode', "UPI").upper()
                        upi_id = transaction_data.get('upi_id')
                        payment.upi_id = upi_id

                    payment.payment_mode = payment_mode
                    payment.save()

                    paymentResponse["payment"].append(PaymentSerializer(payment).data)
                paymentResponse["sales_transaction"] = SalesTransactionShortSerializer(sales_transaction).data
            return Response(paymentResponse, status=status.HTTP_201_CREATED)
