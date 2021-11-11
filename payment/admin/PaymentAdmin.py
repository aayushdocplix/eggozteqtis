from django.contrib import admin

from payment.models import SalesTransaction, Invoice, Payment


class SalesTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'retailer','get_invoices', 'transaction_type', 'transaction_date', 'transaction_amount', 'current_balance','get_payments')
    search_fields = ('id', 'transaction_type', 'transaction_date', 'transaction_amount', 'retailer__code')
    filter_horizontal = ('invoices',)
    readonly_fields = ['id']

    def get_payments(self,obj):
        return "\n, ".join(str(payment.id) for payment in obj.paymentTransactions.all())

    def get_invoices(self, obj):
        return "\n, ".join([i.order.name for i in obj.invoices.all()])

    def get_queryset(self, request):
        queryset = super(SalesTransactionAdmin, self).get_queryset(request)
        orderbyList = ['transaction_date','id']
        queryset = queryset.order_by(*orderbyList)
        return queryset


class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'invoice_id','invoice_due','invoice_status', 'transactions', 'order_name', 'retailer_name')
    search_fields = ('id', "invoice_id", "order__name", "order__retailer__code")

    def transactions(self, obj):
        return "\n, ".join([str(t.id) for t in obj.sales_invoices.all()])

    def order_name(self,obj):
        if obj.order:
            return obj.order.name
        else:
            return ""

    def retailer_name(self,obj):
        if obj.order.retailer:
            return obj.order.retailer.code
        else:
            return ""

    def get_queryset(self, request):
        queryset = super(InvoiceAdmin, self).get_queryset(request)
        queryset = queryset.order_by('-id')
        return queryset

admin.site.register(SalesTransaction, SalesTransactionAdmin)
admin.site.register(Invoice, InvoiceAdmin)

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'payment_type', 'pay_choice', 'pay_amount', 'salesTransaction')
    search_fields = ('id', 'salesTransaction__retailer__code', 'invoice__order__name')

    def get_queryset(self, request):
        queryset = super(PaymentAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset

admin.site.register(Payment,PaymentAdmin)
