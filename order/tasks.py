import decimal
from datetime import datetime, date

from celery import shared_task
from django.core.files.base import ContentFile
from django.core.mail import send_mail, EmailMessage
from django.db.models import Max
from django.template import loader
from num2words import num2words

from Eggoz import settings
from Eggoz.settings import FROM_EMAIL
from base.util.convert_pdf import create_pdf, create_pdf_async
from custom_auth.models import Address
from ecommerce.models import Customer, CashFreeTransaction, CustomerSubscription
from order.api.serializers import OrderLineSerializer
from order.models.Order import EcommerceOrder, OrderEvent, OrderReturnLine, Order
from payment.models import Invoice, SalesTransaction


@shared_task(bind=True, max_retries=3)
def ecomm_create_order(self, cash_free_transaction_id, customer_subscription_id, customer_id):
    print("task", str(cash_free_transaction_id))
    print("task", str(customer_subscription_id))
    print("task", str(customer_id))
    cash_free_transaction = CashFreeTransaction.objects.get(id=cash_free_transaction_id)
    customer_subscription = CustomerSubscription.objects.get(id=customer_subscription_id)

    customer = Customer.objects.get(id=customer_id)
    print("task2", cash_free_transaction)
    print("task2", customer_subscription)
    print("task2", customer)
    # customer_wallet = customer.wallet
    order_type = "Customer"
    dates = cash_free_transaction.subscriptionRequest.dates_subscrption_request.all()

    subscriptionRequest = cash_free_transaction.subscriptionRequest
    if dates:
        for date in dates:
            date_string = date.date_string
            shipping_address_id = date.shipping_address
            cart_product = {}
            cart_product['product'] = subscriptionRequest.product.id
            cart_product['quantity'] = subscriptionRequest.quantity
            cart_product['single_sku_rate'] = subscriptionRequest.single_sku_rate
            cart_product['single_sku_mrp'] = subscriptionRequest.single_sku_mrp
            order_line_serializer = OrderLineSerializer(data=cart_product)
            order_line_serializer.is_valid(raise_exception=True)
            order_date = datetime.strptime(date_string, '%Y-%m-%d')
            orders = Order.objects.all()
            # might be possible model has no records so make sure to handle None
            order_max_id = orders.aggregate(Max('id'))['id__max'] + 1 if orders else 1
            order_id = "Ecomm-GGN-" + str(order_max_id)
            is_promo = False
            if is_promo:
                if is_promo == "true":
                    is_promo = True
                else:
                    is_promo = False
            promo_amount = decimal.Decimal(0.000)
            del_address = Address.objects.get(id=shipping_address_id)
            order_obj = EcommerceOrder.objects.create(customer=customer, orderId=order_id, name=order_id,
                                                      order_type=order_type, date=order_date,
                                                      delivery_date=order_date,
                                                      warehouse_id=1,
                                                      is_promo=is_promo,
                                                      promo_amount=promo_amount,
                                                      ecommerce_slot=cash_free_transaction.subscriptionRequest.slot,
                                                      distributor=del_address.ecommerce_sector.distributor if (
                                                                  del_address.ecommerce_sector and del_address.ecommerce_sector.distributor) else None,
                                                      shipping_address_id=shipping_address_id,
                                                      order_price_amount=cart_product['quantity'] * cart_product[
                                                          'single_sku_rate'],
                                                      discount_amount=cart_product['quantity'] * (
                                                                  cart_product['single_sku_mrp'] - cart_product[
                                                              'single_sku_rate']),
                                                      status="created", desc="description",
                                                      order_payment_status="Paid")
            # Handle Order Event
            # OrderEvent.objects.create(order=order_obj, type="placed", user=order_obj.customer.user)
            OrderEvent.objects.create(order=order_obj, type="order_marked_as_paid", user=order_obj.customer.user)

            order_line_serializer = OrderLineSerializer(data=cart_product)
            order_line_serializer.is_valid(raise_exception=True)
            order_line = order_line_serializer.save(order=order_obj)
            if order_line.promo_quantity > 0:
                OrderReturnLine.objects.create(orderLine=order_line, date=date, line_type="Promo",
                                               quantity=order_line.promo_quantity,
                                               amount=order_line.single_sku_mrp)

            order_lines = order_obj.lines.all()
            purchase_details = []
            total_amount = 0
            for order_line in order_lines:
                product = order_line.product
                print(product)
                # print(dates)

                if product:
                    purchase_detail = {
                        "item_description": "%s (%s SKU)" % (product.name, product.SKU_Count),
                        "hsn_sac": product.productDivision.hsn,
                        "sku_type": product.SKU_Count,
                        "quantity": order_line.quantity,
                        "sku_rate": round(order_line.single_sku_rate,
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
                "name": order_obj.shipping_address.name if order_obj.shipping_address.name else customer.name,
                "pinCode": order_obj.shipping_address.pinCode if order_obj.shipping_address.pinCode else order_obj.shipping_address.ecommerce_sector.pinCode,
                "phone_no": order_obj.shipping_address.phone_no if order_obj.shipping_address.phone_no else customer.phone_no,
                "slot": cash_free_transaction.subscriptionRequest.slot if cash_free_transaction.subscriptionRequest.slot else "",
                # "delivery_person": order_obj.shipping_address.ecommerce_sector.distributor.user.name if order_obj.shipping_address.ecommerce_sector.distributor else " ",
            }
            order_data = {"order_id": order_obj.orderId, "address": address,
                          "order_total_amount": order_obj.order_price_amount,
                          "order_total_in_words": num2words(order_obj.order_price_amount),
                          "purchase_details": purchase_details}
            print(order_data)
            html_message = loader.render_to_string(
                'invoice/order_email.html',
                order_data
            )
            send_mail(subject="Order " + str(order_obj.orderId) + " has  been placed succesfully",
                      message="Message", from_email=FROM_EMAIL,
                      recipient_list=['po@eggoz.in', 'rohit.kumar@eggoz.in'], html_message=html_message)
            OrderEvent.objects.create(order=order_obj, type="created", user=order_obj.customer.user)
            # Handle Invoice
            invoice = Invoice.objects.filter(order=order_obj).first()
            if not invoice:
                invoices = Invoice.objects.all()
                # might be possible model has no records so make sure to handle None
                invoice_max_id = invoices.aggregate(Max('id'))['id__max'] + 1 if invoices else 1
                invoice_id = "E" + str(invoice_max_id)
                invoice = Invoice.objects.create(invoice_id=invoice_id, order=order_obj, invoice_status="Paid")
            # Handle Sales Transactions
            transactions = SalesTransaction.objects.all()
            # might be possible model has no records so make sure to handle None
            transaction_max_id = transactions.aggregate(Max('id'))['id__max'] + 1 if transactions else 1
            transaction_id = "TR" + str(transaction_max_id)
            st = SalesTransaction.objects.create(customer=order_obj.customer, transaction_id=transaction_id,
                                                 transaction_type="Debit", transaction_date=order_obj.date,
                                                 transaction_amount=order_obj.order_price_amount)
            st.invoices.add(invoice)
            st.save()

            # Handle Sales Transactions
            transactionsTwo = SalesTransaction.objects.all()
            # might be possible model has no records so make sure to handle None
            transaction_max_id_two = transactionsTwo.aggregate(Max('id'))['id__max'] + 1 if transactions else 1
            transaction_id_two = "TR" + str(transaction_max_id_two)

            st_two = SalesTransaction.objects.create(customer=order_obj.customer, transaction_id=transaction_id_two,
                                                     transaction_type="Credit", transaction_date=order_obj.date,
                                                     transaction_amount=order_obj.order_price_amount)
            st_two.invoices.add(invoice)
            st_two.save()

            date.customer_subscription = customer_subscription
            date.save()
            print("Order Created")


@shared_task(bind=True, max_retries=3)
def create_invoice(self, order_id, request_uri):
    invoice_type = "TAX INVOICE"
    order = Order.objects.get(id=order_id)
    invoice = Invoice.objects.get(id=order.invoice.id)

    if order.retailer:
        retailer = order.retailer
        billing_address_obj = retailer.billing_address
        billing_address = {
            "firm_name": retailer.name_of_shop,
            "line1": billing_address_obj.address_name if billing_address_obj and billing_address_obj.address_name else None,
            "line2": billing_address_obj.building_address if billing_address_obj and billing_address_obj.building_address else None,
            "line3": billing_address_obj.street_address if billing_address_obj and billing_address_obj.building_address else None,
            "city": billing_address_obj.city.city_name if billing_address_obj else None,
            "state": billing_address_obj.city.state if billing_address_obj and billing_address_obj.city.state else None,
            "pincode": billing_address_obj.pinCode if billing_address_obj and billing_address_obj.pinCode else None,
            "country": billing_address_obj.city.country if billing_address_obj and billing_address_obj.city.country else None,
            "gst_no": retailer.GSTIN
        }
        if retailer.billing_shipping_address_same:
            shipping_address = billing_address
        else:
            shipping_address_obj = retailer.shipping_address
            shipping_address = {
                "firm_name": retailer.name_of_shop,
                "line1": shipping_address_obj.address_name if shipping_address_obj and shipping_address_obj.address_name else None,
                "line2": shipping_address_obj.building_address if shipping_address_obj and shipping_address_obj.building_address else None,
                "line3": shipping_address_obj.street_address if shipping_address_obj and shipping_address_obj.building_address else None,
                "city": shipping_address_obj.city.city_name if shipping_address_obj else None,
                "state": shipping_address_obj.city.state if shipping_address_obj and shipping_address_obj.city.state else None,
                "pincode": shipping_address_obj.pinCode if shipping_address_obj and shipping_address_obj.pinCode else None,
                "country": shipping_address_obj.city.country if shipping_address_obj and shipping_address_obj.city.country else None,
                "gst_no": retailer.GSTIN
            }
    else:
        # TODO sales person billing and shipping address
        salesPerson = order.salesPerson
        billing_address_obj = salesPerson.user.default_address
        billing_address = {
            "firm_name": salesPerson.user.name,
            "line1": billing_address_obj.address_name if billing_address_obj and billing_address_obj.address_name else None,
            "line2": billing_address_obj.building_address if billing_address_obj and billing_address_obj.building_address else None,
            "line3": billing_address_obj.street_address if billing_address_obj and billing_address_obj.building_address else None,
            "city": billing_address_obj.city.city_name if billing_address_obj else None,
            "state": billing_address_obj.city.state if billing_address_obj and billing_address_obj.city.state else None,
            "pincode": billing_address_obj.pinCode if billing_address_obj and billing_address_obj.pinCode else None,
            "country": billing_address_obj.city.country if billing_address_obj and billing_address_obj.city.country else None,
            "gst_no": ""
        }
        shipping_address = billing_address

    order_lines = order.lines.all()
    purchase_details = []
    total_amount = 0
    for order_line in order_lines:
        product = order_line.product
        print(product)
        if order.retailer:
            retailer = order.retailer
            if retailer.commission_slab:
                retailer_slab_number = retailer.commission_slab.number
            else:
                retailer_slab_number = 25
        else:
            retailer_slab_number = 25
        if product:
            purchase_detail = {"item_description": "%s (%s SKU)" % (product.name, product.SKU_Count),
                               "hsn_sac": product.productDivision.hsn,
                               "sku_type": product.SKU_Count,
                               "quantity": order_line.quantity,
                               "sku_rate": round(product.current_price * (100 - retailer_slab_number) / 100,
                                                 2)
                               }
            purchase_detail['amount'] = round(purchase_detail['sku_rate'] * purchase_detail['quantity'], 2)
            purchase_details.append(purchase_detail)
            total_amount = round(total_amount + purchase_detail['amount'], 2)
    if order.retailer:
        retailer = order.retailer
        invoice_data = {
            "gst_no": "20BBGHU8547D1RT",
            "invoice_title": "tax_invoice.pdf",
            "invoice_type": invoice_type,
            "invoice_number": "NUPABH/" + order.name,
            "invoice_date": date.today,
            "terms": "Due on Receipt",
            "due_date": date.today,
            "place_of_supply": retailer.cluster.cluster_name,
            "billing_address": billing_address,
            "shipping_address": shipping_address,
            "purchase_details": purchase_details,
            "total_amount": total_amount,
            "total_in_words": num2words(total_amount)
        }
    else:
        salesPerson = order.salesPerson
        invoice_data = {
            "gst_no": "20BBGHU8547D1RT",
            "invoice_title": "tax_invoice.pdf",
            "invoice_type": invoice_type,
            "invoice_number": "NUPABH/" + order.name,
            "invoice_date": date.today,
            "terms": "Due on Receipt",
            "due_date": date.today,
            "place_of_supply": salesPerson.user.default_address.city,
            "billing_address": billing_address,
            "shipping_address": shipping_address,
            "purchase_details": purchase_details,
            "total_amount": total_amount,
            "total_in_words": num2words(total_amount)
        }
    pdf = create_pdf_async('invoice/tax-invoice.html', {"request_uri": request_uri, 'invoice_data': invoice_data},
                     ["/base/static/assets/tax_invoice.css"])
    pdf_name = "tax-invoice-%s" % order.name + ".pdf"

    msg = EmailMessage("Purchase Invoice", "Please Find Invoice", settings.FROM_EMAIL,
                       ['po@eggoz.in', 'contact@eggoz.in'])
    msg.attach(pdf_name, pdf, 'application/pdf')

    # msg = EmailMultiAlternatives("Purchase Invoice", "Please Find Invoice", settings.FROM_EMAIL,
    #                              [order.retailer.retailer.email])
    # msg.attach(pdf_name, pdf)
    try:
        # print(msg)
        msg.send()
    except Exception as e:
        print(e)
        pass

    if pdf and invoice:
        invoice.file.save(pdf_name, ContentFile(pdf))
        invoice.save()
    else:
        pass

    return "Invoice Created Successfully"
