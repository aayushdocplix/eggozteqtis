import decimal
from datetime import datetime
from decimal import Decimal

import pytz
from django.db.models import Max, Q

from payment.models import Invoice, SalesTransaction, Payment

from retailer.models import Retailer

regex = '^[a-zA-Z0-9]+[\._]?[a-zA-Z0-9]+[@]\w+[.]\w{2,3}$'


def sales_transactions_balance(cities):
    file_response = {}
    data = {"success": [], "No diff": []}
    retailers = Retailer.objects.filter(city__in=cities)
    for retailer in retailers:
        # retailer = Retailer.objects.get(id=60)
        orderbyList = ['-transaction_date', 'id']  # default order
        salesTransactions = SalesTransaction.objects.filter(retailer=retailer,is_trial=False).order_by('-transaction_date')
        salesTransactions = salesTransactions.filter(~Q(transaction_type="Cancelled"))
        # print(salesTransactions)

        if salesTransactions:
            balance = decimal.Decimal(0.000)
            for sales_transaction in salesTransactions:
                if sales_transaction.transaction_type == "Debit":
                    balance += sales_transaction.transaction_amount
                else:
                    balance -= sales_transaction.transaction_amount
                sales_transaction.current_balance = balance
                sales_transaction.save()

                sales_transaction.retailer.amount_due = balance
                sales_transaction.retailer.save()
            data["success"].append({"index": retailer.id + 2, "shop_name": retailer.code, "success": "success"})
            print("Success" + str(retailer.id))
            continue
        else:
            data["success"].append({"index": retailer.id + 2, "shop_name": retailer.code, "success": "no transactions"})
            print("Success" + str(retailer.id))
            continue
    file_response['status'] = "success"
    file_response["data"] = data
    return file_response


def sales_pending_invoices(cities):
    file_response = {}
    data = {"success": [], "No diff": []}
    retailers = Retailer.objects.filter(city__in=cities)
    for retailer in retailers:
        invoices = Invoice.objects.filter(order__is_trial=False,order__retailer=retailer)
        invoices = invoices.filter(~Q(order__status="cancelled"))

        if invoices:
            balance = decimal.Decimal(0.000)
            net_balance = decimal.Decimal(0.000)
            for invoice in invoices:
                net_balance += invoice.invoice_due
                if invoice.invoice_status == "Pending":
                    balance += invoice.invoice_due

            retailer.calc_amount_due = balance
            retailer.net_amount_due = net_balance
            retailer.save()
            data["success"].append({"index": retailer.id + 2, "shop_name": retailer.code, "success": "success"})
            print("Success" + str(retailer.id))
            continue
        else:
            data["success"].append({"index": retailer.id + 2, "shop_name": retailer.code, "success": "no transactions"})
            print("Success" + str(retailer.id))
            continue
    file_response['status'] = "success"
    file_response["data"] = data
    return file_response