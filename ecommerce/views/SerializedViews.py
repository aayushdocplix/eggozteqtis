import asyncio
import decimal
import json
from ast import literal_eval
from datetime import datetime, timedelta

from asgiref.sync import async_to_sync
from django.core.mail import send_mail
from django.template import loader
from django_filters import rest_framework as filters

import requests
from django.db.models import Max, Q
from num2words import num2words
from rest_framework import viewsets, permissions, mixins, pagination, decorators, status

from Eggoz.settings import CASHFREE_BASE_URL, CASHFREE_APP_ID, CASHFREE_SECRET_KEY, CURRENT_ZONE, FROM_EMAIL
from base.response import Ok, Response, BadRequest
from base.views import PaginationWithNoLimit
from custom_auth.models import UserProfile, Address
from custom_auth.views import PaginationWithLimit
from ecommerce.api import RechargeVoucherSerializer, CustomerWalletSerializer, MemberShipSerializer, \
    CustomerMemberShipSerializer, CustomerSubscriptionSerializer, CustomerSubscriptionCreateSerializer, \
    SubscriptionSerializer, CustomerSubscriptionRequestCreateSerializer, NotifyCustomerSerializer
from ecommerce.models import RechargeVoucher, CustomerWallet, CashFreeTransaction, WalletRecharge, Customer, \
    CustomerVoucherPromo, MemberShipRequest, SubscriptionRequest, SubscriptionDate, NotifyCustomer, CustomerPromoWallet
from ecommerce.models.Subscriptions import MemberShip, CustomerMemberShip, CustomerSubscription, FrequencyDay, \
    Subscription
from order.api.serializers import EcommerceOrderCreateSerializer, OrderLineSerializer
from order.models import Order, OrderEvent
from order.models.Order import OrderReturnLine

from order.tasks import ecomm_create_order
from order.views.SerializedViews import ecommerce_order_create
from payment.api.serializers import WalletRechargeSerializer, WalletRechargeValidationSerializer, \
    MemberShipRechargeValidationSerializer, SubscriptionRechargeValidationSerializer
from payment.models import Invoice, SalesTransaction


class RechargeVoucherViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = RechargeVoucherSerializer
    pagination_class = PaginationWithLimit
    queryset = RechargeVoucher.objects.all()

    def list(self, request, *args, **kwargs):
        user = request.user
        customer_profile = UserProfile.objects.filter(user=user, department__name__in=['Customer']).first()
        if customer_profile:
            customer = Customer.objects.filter(user=user).first()
            if customer:
                if CustomerVoucherPromo.objects.filter(customer=customer):
                    used_promos_ids = CustomerVoucherPromo.objects.filter(customer=customer).values_list('voucher_id',
                                                                                                         flat=True)
                    queryset = RechargeVoucher.objects.filter(~Q(id__in=used_promos_ids))
                else:
                    queryset = RechargeVoucher.objects.all()
                page = self.paginate_queryset(queryset)
                if page is not None:
                    serializer = self.get_serializer(page, many=True)
                    return self.get_paginated_response(serializer.data)

                serializer = self.get_serializer(queryset, many=True)
                return Response(serializer.data)
            else:
                return Response({"message": "No customer account"})
        else:
            return Response({"message": "No customer profile account"})


class CustomerWalletViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    permission_classes = (permissions.AllowAny,)
    serializer_class = CustomerWalletSerializer
    queryset = CustomerWallet.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('customer',)


class WalletRechargeViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    serializer_class = WalletRechargeSerializer
    pagination_class = PaginationWithLimit
    permission_classes = [permissions.IsAuthenticated]
    queryset = WalletRecharge.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('wallet',)

    def list(self, request, *args, **kwargs):
        if request.GET.get("wallet"):
            wallet = request.GET.get("wallet")
            queryset = self.get_queryset().filter(wallet_id=wallet)
        else:
            queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @decorators.action(detail=False, methods=['post'], url_path="recharge")
    def recharge(self, request, *args, **kwargs):
        data = request.data
        user = request.user
        customer = Customer.objects.filter(user=user).first()
        print(request.data)
        serializer = WalletRechargeValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        name = data.get('name', user.name)
        email = data.get('email', user.email)
        phone_no = data.get('phone_no', user.phone_no)
        voucher_id = data.get('voucher', 0)
        wallet_id = data.get('wallet')
        cash_free_all_obj = CashFreeTransaction.objects.all()
        cft_maxcount = cash_free_all_obj.aggregate(Max('id'))['id__max'] + 1 if cash_free_all_obj else 1
        cash_free_transaction = CashFreeTransaction.objects.create(
            transaction_id="CustomerWallet-" + str(customer.id) + "-" + str(cft_maxcount),
            wallet_id=int(wallet_id))
        if int(voucher_id) > 0:
            cash_free_transaction.voucher_id = int(voucher_id)
            cash_free_transaction.save()
        orderAmount = decimal.Decimal(data.get('amount'))
        cash_free_transaction.transaction_amount = orderAmount
        cash_free_transaction.save()
        orderId = cash_free_transaction.transaction_id
        # Handle Payment
        domain = request.build_absolute_uri('/')[:-1]
        if "https" in domain:
            pass
        else:
            domain = domain.replace('http', 'https')

        url = "%s/api/v1/order/create" % (CASHFREE_BASE_URL)
        print(url)
        payload = {'appId': CASHFREE_APP_ID,
                   'secretKey': CASHFREE_SECRET_KEY,
                   'orderId': orderId,
                   'orderAmount': float("{:.2f}".format(orderAmount)),
                   'orderCurrency': 'INR',
                   'orderNote': "Wallet Recharge",
                   'customerEmail': str(email),
                   'customerName': str(name),
                   'customerPhone': str(phone_no),
                   'returnUrl': '%s/payment/return_wallet_recharge/' % (domain),
                   'notifyUrl': '%s/payment/notify_payment/' % (domain)
                   }
        print(payload)
        files = [
        ]
        headers = {}
        response = requests.request("POST", url, headers=headers, data=payload, files=files)
        print(domain)
        print(response.text)
        gateway_response = json.loads(response.text)
        cash_free_transaction.payment_link = gateway_response.get('paymentLink')
        cash_free_transaction.save()
        return Ok(gateway_response)


class MemberShipViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = PaginationWithNoLimit
    serializer_class = MemberShipSerializer
    queryset = MemberShip.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('name', 'margin', 'is_visible')

    @decorators.action(detail=False, methods=['post'], url_path="recharge")
    def recharge(self, request, *args, **kwargs):
        data = request.data
        user = request.user
        customer = Customer.objects.filter(user=user).first()
        print(request.data)
        serializer = MemberShipRechargeValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        name = data.get('name', user.name)
        email = data.get('email', user.email)
        phone_no = data.get('phone_no', user.phone_no)
        start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%d %H:%M:%S')
        expiry_date = datetime.strptime(data.get('expiry_date'), '%Y-%m-%d %H:%M:%S')
        memberShip_id = data.get('memberShip')
        # recharge_type = data.get('recharge_type', 'Membership')
        wallet_id = data.get('wallet')
        if data.get('pay_by_wallet') == "true":
            pay_by_wallet = True
        else:
            pay_by_wallet = False
        cash_free_all_obj = CashFreeTransaction.objects.all()
        cft_maxcount = cash_free_all_obj.aggregate(Max('id'))['id__max'] + 1 if cash_free_all_obj else 1
        memberShipRequest = MemberShipRequest.objects.create(memberShip_id=memberShip_id, start_date=start_date,
                                                             expiry_date=expiry_date)
        cash_free_transaction = CashFreeTransaction.objects.create(
            transaction_id="CustomerMemberShip-" + str(customer.id) + "-" + str(cft_maxcount),
            memberShipRequest=memberShipRequest,
            recharge_type="MemberShip",
            pay_by_wallet=pay_by_wallet,
            wallet_id=int(wallet_id))

        orderAmount = decimal.Decimal(data.get('amount'))
        cash_free_transaction.transaction_amount = orderAmount
        cash_free_transaction.save()

        if data.get('pay_by_wallet') == "true":
            wallet = cash_free_transaction.wallet
            customer_wallet = CustomerWallet.objects.get(id=wallet.id)
            customer = customer_wallet.customer
            amount = cash_free_transaction.transaction_amount
            if int(customer_wallet.recharge_balance) > int(amount):

                CustomerMemberShip.objects.create(customer=customer,
                                                  memberShip=cash_free_transaction.memberShipRequest.memberShip,
                                                  start_date=cash_free_transaction.memberShipRequest.start_date,
                                                  expiry_date=cash_free_transaction.memberShipRequest.expiry_date)

                customer_wallet.total_balance -= amount
                customer_wallet.recharge_balance -= amount
                customer_wallet.save()

                return Ok("order created successfully")
            else:
                return BadRequest({'error_type': "Validation Error",
                                   'errors': [
                                       {'message': "Your current recharged balance is less than amount to be paid"}]})
        else:
            orderId = cash_free_transaction.transaction_id
            # Handle Payment
            domain = request.build_absolute_uri('/')[:-1]
            if "https" in domain:
                pass
            else:
                domain = domain.replace('http', 'https')

            url = "%s/api/v1/order/create" % (CASHFREE_BASE_URL)
            print(url)
            payload = {'appId': CASHFREE_APP_ID,
                       'secretKey': CASHFREE_SECRET_KEY,
                       'orderId': orderId,
                       'orderAmount': float("{:.2f}".format(orderAmount)),
                       'orderCurrency': 'INR',
                       'orderNote': "MemberShip Recharge",
                       'customerEmail': str(email),
                       'customerName': str(name),
                       'customerPhone': str(phone_no),
                       'returnUrl': '%s/payment/return_membership_recharge/' % (domain),
                       'notifyUrl': '%s/payment/notify_payment/' % (domain)
                       }
            print(payload)
            files = [
            ]
            headers = {}
            response = requests.request("POST", url, headers=headers, data=payload, files=files)
            print(domain)
            print(response.text)
            gateway_response = json.loads(response.text)
            cash_free_transaction.payment_link = gateway_response.get('paymentLink')
            cash_free_transaction.save()
            return Ok(gateway_response)


class SubscriptionViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    permission_classes = [permissions.AllowAny]
    pagination_class = PaginationWithNoLimit
    serializer_class = SubscriptionSerializer
    queryset = Subscription.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('name', 'margin', 'is_visible')

    @decorators.action(detail=False, methods=['post'], url_path="recharge")
    def recharge(self, request, *args, **kwargs):
        data = request.data
        user = request.user
        customer = Customer.objects.filter(user=user).first()
        if customer:
            print(request.data)
            serializer = SubscriptionRechargeValidationSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            name = data.get('name', user.name)
            email = data.get('email', user.email)
            phone_no = data.get('phone_no', user.phone_no)
            start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%d %H:%M:%S')
            expiry_date = datetime.strptime(data.get('expiry_date'), '%Y-%m-%d %H:%M:%S')
            subscription_id = data.get('subscription')

            days = data.get('days', [])
            slot = data.get('slot', 1)
            dates = data.get('dates', [])
            cart_product = data.get('cart_product', {})
            shipping_address = int(data.get('shipping_address'))

            wallet_id = data.get('wallet')
            if data.get('pay_by_wallet') == "true":
                pay_by_wallet = True
            else:
                pay_by_wallet = False
            cash_free_all_obj = CashFreeTransaction.objects.all()
            cft_maxcount = cash_free_all_obj.aggregate(Max('id'))['id__max'] + 1 if cash_free_all_obj else 1

            if days:
                days = json.loads(days)
                if len(days) > 0:
                    cart_product = json.loads(cart_product)
                    subscription_serializer = CustomerSubscriptionRequestCreateSerializer(data=data)
                    subscription_serializer.is_valid(raise_exception=True)
                    subscriptionRequest = subscription_serializer.save(subscription_id=subscription_id,
                                                                       single_sku_rate=cart_product['single_sku_rate'],
                                                                       single_sku_mrp=cart_product['single_sku_mrp'],
                                                                       start_date=start_date, expiry_date=expiry_date)

                    for day in days:
                        frequency = FrequencyDay.objects.get(day_id=int(day))
                        subscriptionRequest.days.add(frequency)

                    # print(dates)
                    dates = json.loads(dates)
                    for date in dates:
                        SubscriptionDate.objects.create(date_string=date, subscriptionRequest=subscriptionRequest,
                                                        shipping_address=shipping_address)

                    cash_free_transaction = CashFreeTransaction.objects.create(
                        transaction_id="Customer-" + str(customer.id) + "-" + str(cft_maxcount),
                        subscriptionRequest=subscriptionRequest,
                        recharge_type="Subscription",
                        pay_by_wallet=pay_by_wallet,
                        wallet_id=int(wallet_id))

                    orderAmount = decimal.Decimal(data.get('amount'))
                    cash_free_transaction.transaction_amount = orderAmount
                    cash_free_transaction.save()

                    if data.get('pay_by_wallet') == "true":
                        wallet = cash_free_transaction.wallet
                        customer_wallet = CustomerWallet.objects.get(id=wallet.id)
                        customer = customer_wallet.customer
                        amount = cash_free_transaction.transaction_amount
                        if int(customer_wallet.recharge_balance) >= int(amount):
                            customersubscription = CustomerSubscription.objects.create(customer=customer,
                                                                                       subscription=cash_free_transaction.subscriptionRequest.subscription,
                                                                                       product=cash_free_transaction.subscriptionRequest.product,
                                                                                       quantity=cash_free_transaction.subscriptionRequest.quantity,
                                                                                       single_sku_rate=cash_free_transaction.subscriptionRequest.single_sku_rate,
                                                                                       single_sku_mrp=cash_free_transaction.subscriptionRequest.single_sku_mrp,
                                                                                       slot=cash_free_transaction.subscriptionRequest.slot,
                                                                                       start_date=cash_free_transaction.subscriptionRequest.start_date,
                                                                                       expiry_date=cash_free_transaction.subscriptionRequest.expiry_date)

                            print(cash_free_transaction.id)
                            print(customersubscription.id)
                            print(customersubscription.customer.id)
                            ecomm_create_order.delay(cash_free_transaction.id, customersubscription.id,
                                                     customersubscription.customer.id)

                            customer_wallet.total_balance -= amount
                            customer_wallet.recharge_balance -= amount
                            customer_wallet.save()
                            return Response({"result": "Subscription added successfully"},
                                            status=status.HTTP_201_CREATED)
                        else:
                            return Response(
                                {"result": "Your current recharged balance is less than amount to be paid, "},
                                status=status.HTTP_400_BAD_REQUEST)
                            # return BadRequest({'error_type': "Validation Error", 'errors': [{'message': "Your
                            # current recharged balance is less than amount to be paid"}]})
                    else:
                        orderId = cash_free_transaction.transaction_id
                        # Handle Payment
                        domain = request.build_absolute_uri('/')[:-1]
                        if "https" in domain:
                            pass
                        else:
                            domain = domain.replace('http', 'https')

                        url = "%s/api/v1/order/create" % (CASHFREE_BASE_URL)
                        print(url)
                        payload = {'appId': CASHFREE_APP_ID,
                                   'secretKey': CASHFREE_SECRET_KEY,
                                   'orderId': orderId,
                                   'orderAmount': float("{:.2f}".format(orderAmount)),
                                   'orderCurrency': 'INR',
                                   'orderNote': "Subscription Recharge",
                                   'customerEmail': str(email),
                                   'customerName': str(name),
                                   'customerPhone': str(phone_no),
                                   'returnUrl': '%s/payment/return_subscription_recharge/' % (domain),
                                   'notifyUrl': '%s/payment/notify_payment/' % (domain)
                                   }
                        print(payload)
                        files = [
                        ]
                        headers = {}
                        response = requests.request("POST", url, headers=headers, data=payload, files=files)
                        print(domain)
                        print(response.text)
                        gateway_response = json.loads(response.text)
                        cash_free_transaction.payment_link = gateway_response.get('paymentLink')
                        cash_free_transaction.save()
                        return Ok(gateway_response)

                else:
                    return BadRequest({'error_type': "Validation Error",
                                       'errors': [
                                           {'message': "Days Less than one"}]})
            else:
                return BadRequest({'error_type': "Validation Error",
                                   'errors': [
                                       {'message': "Days Less than one"}]})
        else:
            return BadRequest({'error_type': "Authorization Error",
                               'errors': [
                                   {'message': "Not Authorized"}]})


class CustomerCartCheckout(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    permission_classes = [permissions.AllowAny]
    pagination_class = PaginationWithNoLimit
    serializer_class = SubscriptionSerializer
    queryset = Subscription.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('name', 'margin', 'is_visible')

    @decorators.action(detail=False, methods=['post'], url_path="checkout")
    def checkout(self, request, *args, **kwargs):
        data = request.data
        user = request.user
        customer = Customer.objects.filter(user=user).first()
        if customer:
            if int(data.get('order_price_amount')) > 0 and int(data.get('amount')) > 0:
                subscription_serializer = SubscriptionRechargeValidationSerializer(data=request.data)
                subscription_serializer.is_valid(raise_exception=True)
                ecomm_order_create_serializer = EcommerceOrderCreateSerializer(data=data)
                ecomm_order_create_serializer.is_valid(raise_exception=True)

                order_type = "Customer"
                cart_products = data.get('cart_products', [])
                name = data.get('name', user.name)
                email = data.get('email', user.email)
                phone_no = data.get('phone_no', user.phone_no)
                start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%d %H:%M:%S')
                expiry_date = datetime.strptime(data.get('expiry_date'), '%Y-%m-%d %H:%M:%S')
                subscription_id = data.get('subscription')

                days = data.get('days', [])
                slot = data.get('slot', 1)
                dates = data.get('dates', [])
                cart_product = data.get('cart_product', {})
                shipping_address = int(data.get('shipping_address'))

                wallet_id = data.get('wallet')

                if data.get('pay_by_wallet') == "true":
                    pay_by_wallet = True
                else:
                    pay_by_wallet = False
                cash_free_all_obj = CashFreeTransaction.objects.all()
                cft_maxcount = cash_free_all_obj.aggregate(Max('id'))['id__max'] + 1 if cash_free_all_obj else 1

                return BadRequest({'error_type': "Implementation Error",
                                   'errors': [
                                       {'message': "To be Implemented soon"}]})
                # if days and cart_products and cart_product:
                #     days = json.loads(days)
                #     cart_products = json.loads(cart_products)
                #     cart_product = json.loads(cart_product)
                #     if len(days) > 0 and len(cart_product) > 0 and len(cart_products) > 0:
                #         subscription_serializer = CustomerSubscriptionRequestCreateSerializer(data=data)
                #         subscription_serializer.is_valid(raise_exception=True)
                #         subscriptionRequest = subscription_serializer.save(subscription_id=subscription_id,
                #                                                            single_sku_rate=cart_product[
                #                                                                'single_sku_rate'],
                #                                                            single_sku_mrp=cart_product[
                #                                                                'single_sku_mrp'],
                #                                                            start_date=start_date,
                #                                                            expiry_date=expiry_date)
                #
                #         for day in days:
                #             frequency = FrequencyDay.objects.get(day_id=int(day))
                #             subscriptionRequest.days.add(frequency)
                #
                #         # print(dates)
                #         dates = json.loads(dates)
                #         for date in dates:
                #             SubscriptionDate.objects.create(date_string=date, subscriptionRequest=subscriptionRequest,
                #                                             shipping_address=shipping_address)
                #
                #         cash_free_transaction = CashFreeTransaction.objects.create(
                #             transaction_id="Customer-" + str(customer.id) + "-" + str(cft_maxcount),
                #             subscriptionRequest=subscriptionRequest,
                #             recharge_type="Subscription",
                #             pay_by_wallet=pay_by_wallet,
                #             wallet_id=int(wallet_id))
                #
                #         orderAmount = decimal.Decimal(data.get('amount')) + \
                #                       decimal.Decimal(data.get('order_price_amount'))
                #         cash_free_transaction.transaction_amount = orderAmount
                #         cash_free_transaction.save()
                #
                #         if data.get('pay_by_wallet') == "true":
                #             wallet = cash_free_transaction.wallet
                #             customer_wallet = CustomerWallet.objects.get(id=wallet.id)
                #             customer = customer_wallet.customer
                #             amount = cash_free_transaction.transaction_amount
                #             if int(customer_wallet.recharge_balance) >= int(amount):
                #                 customersubscription = CustomerSubscription.objects.create(customer=customer,
                #                                                                            subscription=cash_free_transaction.subscriptionRequest.subscription,
                #                                                                            product=cash_free_transaction.subscriptionRequest.product,
                #                                                                            quantity=cash_free_transaction.subscriptionRequest.quantity,
                #                                                                            single_sku_rate=cash_free_transaction.subscriptionRequest.single_sku_rate,
                #                                                                            single_sku_mrp=cash_free_transaction.subscriptionRequest.single_sku_mrp,
                #                                                                            slot=cash_free_transaction.subscriptionRequest.slot,
                #                                                                            start_date=cash_free_transaction.subscriptionRequest.start_date,
                #                                                                            expiry_date=cash_free_transaction.subscriptionRequest.expiry_date)
                #
                #                 print(cash_free_transaction.id)
                #                 print(customersubscription.id)
                #                 print(customersubscription.customer.id)
                #                 ecomm_create_order.delay(cash_free_transaction.id, customersubscription.id,
                #                                          customersubscription.customer.id)
                #
                #                 customer_wallet.total_balance -= amount
                #                 customer_wallet.recharge_balance -= amount
                #                 customer_wallet.save()
                #                 return Response({"result": "Subscription added successfully"},
                #                                 status=status.HTTP_201_CREATED)
                #             else:
                #                 return Response(
                #                     {"result": "Your current recharged balance is less than amount to be paid, "},
                #                     status=status.HTTP_400_BAD_REQUEST)
                #         else:
                #             orderId = cash_free_transaction.transaction_id
                #             # Handle Payment
                #             domain = request.build_absolute_uri('/')[:-1]
                #             if "https" in domain:
                #                 pass
                #             else:
                #                 domain = domain.replace('http', 'https')
                #
                #             url = "%s/api/v1/order/create" % (CASHFREE_BASE_URL)
                #             print(url)
                #             payload = {'appId': CASHFREE_APP_ID,
                #                        'secretKey': CASHFREE_SECRET_KEY,
                #                        'orderId': orderId,
                #                        'orderAmount': float("{:.2f}".format(orderAmount)),
                #                        'orderCurrency': 'INR',
                #                        'orderNote': "Subscription Recharge",
                #                        'customerEmail': str(email),
                #                        'customerName': str(name),
                #                        'customerPhone': str(phone_no),
                #                        'returnUrl': '%s/payment/return_subscription_recharge/' % (domain),
                #                        'notifyUrl': '%s/payment/notify_payment/' % (domain)
                #                        }
                #             print(payload)
                #             files = [
                #             ]
                #             headers = {}
                #             response = requests.request("POST", url, headers=headers, data=payload, files=files)
                #             print(domain)
                #             print(response.text)
                #             gateway_response = json.loads(response.text)
                #             cash_free_transaction.payment_link = gateway_response.get('paymentLink')
                #             cash_free_transaction.save()
                #             return Ok(gateway_response)
                #
                #     else:
                #         return BadRequest({'error_type': "Validation Error",
                #                            'errors': [
                #                                {
                #                                    'message': "Days or Cart Products or Subscription Products are Empty"}]})
                # else:
                #     return BadRequest({'error_type': "Validation Error",
                #                        'errors': [
                #                            {'message': "Days or Cart Products or Subscription Products are Empty"}]})

            else:
                if int(data.get('order_price_amount')) > 0:
                    result = ecommerce_order_create(request)
                    return Ok(result)
                elif int(data.get('amount')) > 0:
                    result = subscription_ecommerce_create(request)
                    return Ok(result)
                else:
                    return BadRequest({'error_type': "Authorization Error",
                                       'errors': [
                                           {'message': "Not a Valid Amount"}]})
        else:
            return BadRequest({'error_type': "Authorization Error",
                               'errors': [
                                   {'message': "Not a Customer Profile"}]})


class CustomerMemberShipViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PaginationWithNoLimit
    serializer_class = CustomerMemberShipSerializer
    queryset = CustomerMemberShip.objects.all()


class CustomerSubscriptionViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PaginationWithNoLimit
    serializer_class = CustomerSubscriptionSerializer
    queryset = CustomerSubscription.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('customer', 'product', 'start_date', 'expiry_date')

    def create(self, request, *args, **kwargs):
        import json
        data = request.data
        days = data.get('days', [])
        if days:
            days = json.loads(days)
            if len(days) > 0:
                subscription_serializer = CustomerSubscriptionCreateSerializer(data=data)
                subscription_serializer.is_valid(raise_exception=True)
                subscription = subscription_serializer.save()
                for day in days:
                    frequency = FrequencyDay.objects.get(id=int(day))
                    subscription.days.add(frequency)
                return Response({""})
        else:
            return BadRequest({'error_type': "Validation Error",
                               'errors': [{'message': "Days can not be empty"}]})


class NotifyCustomerViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.AllowAny,)
    pagination_class = PaginationWithNoLimit
    serializer_class = NotifyCustomerSerializer
    queryset = NotifyCustomer.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('customer', 'is_notified', 'email', 'phone_no', 'product')


def subscription_ecommerce_create(request):
    data = request.data
    user = request.user
    customer = Customer.objects.filter(user=user).first()
    if customer:
        print(request.data)
        serializer = SubscriptionRechargeValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        name = data.get('name', user.name)
        email = data.get('email', user.email)
        phone_no = data.get('phone_no', user.phone_no)
        start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%d %H:%M:%S')
        expiry_date = datetime.strptime(data.get('expiry_date'), '%Y-%m-%d %H:%M:%S')
        subscription_id = data.get('subscription')

        days = data.get('days', [])
        slot = data.get('slot', 1)
        dates = data.get('dates', [])
        cart_product = data.get('cart_product', {})
        shipping_address = int(data.get('shipping_address'))

        wallet_id = data.get('wallet')
        if data.get('pay_by_wallet') == "true":
            pay_by_wallet = True
        else:
            pay_by_wallet = False
        cash_free_all_obj = CashFreeTransaction.objects.all()
        cft_maxcount = cash_free_all_obj.aggregate(Max('id'))['id__max'] + 1 if cash_free_all_obj else 1

        if days:
            days = json.loads(days)
            if len(days) > 0:
                cart_product = json.loads(cart_product)
                subscription_serializer = CustomerSubscriptionRequestCreateSerializer(data=data)
                subscription_serializer.is_valid(raise_exception=True)
                subscriptionRequest = subscription_serializer.save(subscription_id=subscription_id,
                                                                   single_sku_rate=cart_product['single_sku_rate'],
                                                                   single_sku_mrp=cart_product['single_sku_mrp'],
                                                                   start_date=start_date, expiry_date=expiry_date)

                for day in days:
                    frequency = FrequencyDay.objects.get(day_id=int(day))
                    subscriptionRequest.days.add(frequency)

                # print(dates)
                dates = json.loads(dates)
                for date in dates:
                    SubscriptionDate.objects.create(date_string=date, subscriptionRequest=subscriptionRequest,
                                                    shipping_address=shipping_address)

                cash_free_transaction = CashFreeTransaction.objects.create(
                    transaction_id="Customer-" + str(customer.id) + "-" + str(cft_maxcount),
                    subscriptionRequest=subscriptionRequest,
                    recharge_type="Subscription",
                    pay_by_wallet=pay_by_wallet,
                    wallet_id=int(wallet_id))

                orderAmount = decimal.Decimal(data.get('amount'))
                cash_free_transaction.transaction_amount = orderAmount
                cash_free_transaction.save()

                if data.get('pay_by_wallet') == "true":
                    wallet = cash_free_transaction.wallet
                    customer_wallet = CustomerWallet.objects.get(id=wallet.id)
                    customer = customer_wallet.customer
                    amount = cash_free_transaction.transaction_amount
                    if int(customer_wallet.recharge_balance) >= int(amount):
                        customersubscription = CustomerSubscription.objects.create(customer=customer,
                                                                                   subscription=cash_free_transaction.subscriptionRequest.subscription,
                                                                                   product=cash_free_transaction.subscriptionRequest.product,
                                                                                   quantity=cash_free_transaction.subscriptionRequest.quantity,
                                                                                   single_sku_rate=cash_free_transaction.subscriptionRequest.single_sku_rate,
                                                                                   single_sku_mrp=cash_free_transaction.subscriptionRequest.single_sku_mrp,
                                                                                   slot=cash_free_transaction.subscriptionRequest.slot,
                                                                                   start_date=cash_free_transaction.subscriptionRequest.start_date,
                                                                                   expiry_date=cash_free_transaction.subscriptionRequest.expiry_date)

                        print(cash_free_transaction.id)
                        print(customersubscription.id)
                        print(customersubscription.customer.id)
                        ecomm_create_order.delay(cash_free_transaction.id, customersubscription.id,
                                                 customersubscription.customer.id)

                        customer_wallet.total_balance -= amount
                        customer_wallet.recharge_balance -= amount
                        customer_wallet.save()
                        return {"result": "Subscription added successfully"}
                    else:
                        # return Response({"result": "Your current recharged balance is less than amount to be paid, "},
                        #                 status=status.HTTP_400_BAD_REQUEST)
                        orderAmount = decimal.Decimal(data.get('amount')) - decimal.Decimal(customer_wallet.recharge_balance)
                        orderId = cash_free_transaction.transaction_id
                        cash_free_transaction.wallet_amount = decimal.Decimal(customer_wallet.recharge_balance)
                        cash_free_transaction.save()
                        # Handle Payment
                        domain = request.build_absolute_uri('/')[:-1]
                        if "https" in domain:
                            pass
                        else:
                            domain = domain.replace('http', 'https')

                        url = "%s/api/v1/order/create" % (CASHFREE_BASE_URL)
                        print(url)
                        payload = {'appId': CASHFREE_APP_ID,
                                   'secretKey': CASHFREE_SECRET_KEY,
                                   'orderId': orderId,
                                   'orderAmount': float("{:.2f}".format(orderAmount)),
                                   'orderCurrency': 'INR',
                                   'orderNote': "Subscription Recharge",
                                   'customerEmail': str(email),
                                   'customerName': str(name),
                                   'customerPhone': str(phone_no),
                                   'returnUrl': '%s/payment/return_subscription_recharge/' % (domain),
                                   'notifyUrl': '%s/payment/notify_payment/' % (domain)
                                   }
                        print(payload)
                        files = [
                        ]
                        headers = {}
                        response = requests.request("POST", url, headers=headers, data=payload, files=files)
                        print(domain)
                        print(response.text)
                        gateway_response = json.loads(response.text)
                        cash_free_transaction.payment_link = gateway_response.get('paymentLink')
                        cash_free_transaction.save()
                        return gateway_response
                else:
                    orderId = cash_free_transaction.transaction_id
                    # Handle Payment
                    domain = request.build_absolute_uri('/')[:-1]
                    if "https" in domain:
                        pass
                    else:
                        domain = domain.replace('http', 'https')

                    url = "%s/api/v1/order/create" % (CASHFREE_BASE_URL)
                    print(url)
                    payload = {'appId': CASHFREE_APP_ID,
                               'secretKey': CASHFREE_SECRET_KEY,
                               'orderId': orderId,
                               'orderAmount': float("{:.2f}".format(orderAmount)),
                               'orderCurrency': 'INR',
                               'orderNote': "Subscription Recharge",
                               'customerEmail': str(email),
                               'customerName': str(name),
                               'customerPhone': str(phone_no),
                               'returnUrl': '%s/payment/return_subscription_recharge/' % (domain),
                               'notifyUrl': '%s/payment/notify_payment/' % (domain)
                               }
                    print(payload)
                    files = [
                    ]
                    headers = {}
                    response = requests.request("POST", url, headers=headers, data=payload, files=files)
                    print(domain)
                    print(response.text)
                    gateway_response = json.loads(response.text)
                    cash_free_transaction.payment_link = gateway_response.get('paymentLink')
                    cash_free_transaction.save()
                    return gateway_response

            else:
                return BadRequest({'error_type': "Validation Error",
                                   'errors': [
                                       {'message': "Days Less than one"}]})
        else:
            return BadRequest({'error_type': "Validation Error",
                               'errors': [
                                   {'message': "Days Less than one"}]})
    else:
        return BadRequest({'error_type': "Authorization Error",
                           'errors': [
                               {'message': "Not Authorized"}]})
