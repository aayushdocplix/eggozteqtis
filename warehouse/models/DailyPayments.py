from datetime import datetime
from decimal import Decimal

from django.db import models
from django.db.models import F

from Eggoz import settings
from Eggoz.settings import CURRENT_ZONE
from distributionchain.models import DistributionPersonProfile
from finance.models import FinanceProfile
from saleschain.models import SalesPersonProfile
from warehouse.models import Warehouse


class DailyPayments(models.Model):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    date = models.DateField(null=False, blank=False)
    salesPerson = models.ForeignKey(SalesPersonProfile, on_delete=models.DO_NOTHING,
                                    related_name="paymentSalesPerson", null=True, blank=True)
    distributor = models.ForeignKey(DistributionPersonProfile, on_delete=models.DO_NOTHING,
                                    related_name="paymentDistributionPerson", null=True, blank=True)
    entered_by = models.ForeignKey(FinanceProfile, on_delete=models.DO_NOTHING,
                                    related_name="paymentFinancePerson", null=True, blank=True)
    remark = models.CharField(null=True, max_length=200)
    total_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
    )
    is_verified = models.BooleanField(default=False)

    class Meta:
        ordering = ("-date",)

    def __str__(self):
        if self.salesPerson:
            return '{} {}'.format(str(self.date), self.salesPerson.user.name)
        else:
            return '{} {}'.format(str(self.date), self.distributor.user.name)

    def increase_amount(self, total_amount: float, commit: bool = True):
        """Return given quantity of product to a stock."""
        self.quantity = F("total_amount") + Decimal(total_amount)
        if commit:
            self.save(update_fields=["total_amount"])

    def decrease_amount(self, total_amount: float, commit: bool = True):
        self.quantity = F("total_amount") - Decimal(total_amount)
        if commit:
            self.save(update_fields=["total_amount"])


class DailyPaymentLine(models.Model):
    dailyPayment = models.ForeignKey(DailyPayments, null=False, blank=False, on_delete=models.DO_NOTHING,
                                     related_name="daily_payment_lines")
    date_time = models.DateTimeField(null=False, blank=False)
    remark = models.CharField(null=True, max_length=200)
    amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
    )

    def __str__(self):
        if self.dailyPayment.salesPerson:
            return '{} {} {}'.format(str(self.date_time), self.dailyPayment.salesPerson.user.name, self.amount)
        else:
            return '{} {} {}'.format(str(self.date_time), self.dailyPayment.distributor.user.name,  self.amount)

    class Meta:
        ordering = ("-date_time",)


class ExpenseCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class ExpenseRequest(models.Model):
    date_time = models.DateTimeField(null=True, blank=True)
    expense_category = models.ForeignKey(ExpenseCategory, on_delete=models.CASCADE, null=True, blank=True)
    expense_type = models.CharField(max_length=200, default="OTHER")
    city = models.CharField(max_length=200, default="Gurgaon")
    description = models.CharField(max_length=254, default="Paid to")
    user = models.ForeignKey('custom_auth.User', on_delete=models.DO_NOTHING,
                             related_name="expenseRequestUser", null=True, blank=True)
    amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
    )
    STATUS_TYPES = (('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected'), ('Paid', 'Paid'))
    status = models.CharField(max_length=200, choices=STATUS_TYPES)
    def __str__(self):
        return '{} {}'.format(str(self.date_time), self.user.name)


class Expense(models.Model):
    date_time = models.DateTimeField(null=True, blank=True)
    entered_date = models.DateTimeField(null=True, blank=True)
    expense_category = models.ForeignKey(ExpenseCategory, on_delete=models.CASCADE, null=True, blank=True)
    expense_type = models.CharField(max_length=200, default="OTHER")
    description = models.CharField(max_length=254, default="Paid to")
    city = models.CharField(max_length=200, default="Gurgaon")
    user = models.ForeignKey('custom_auth.User', on_delete=models.DO_NOTHING,
                             related_name="expenseUser", null=True, blank=True)
    entered_by = models.ForeignKey(FinanceProfile, on_delete=models.DO_NOTHING,
                                   related_name="expenseFinancePerson", null=True, blank=True)
    remark = models.CharField(null=True, max_length=200)
    amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
    )
    payment_mode = models.CharField(max_length=200, default='PETTY CASH')
    bill_no = models.CharField(max_length=200, default='bill')
    vendor = models.CharField(max_length=200, default='Vendor Name')

    class Meta:
        ordering = ("-date_time",)

    def __str__(self):
        if self.user:
            return '{} {}'.format(str(self.date_time), self.user.name)
        else:
            return '{} {}'.format(str(self.date_time), self.remark)

    def increase_amount(self, amount: float, commit: bool = True):
        """Return given quantity of product to a stock."""
        self.quantity = F("amount") + Decimal(amount)
        if commit:
            self.save(update_fields=["amount"])

    def decrease_amount(self, amount: float, commit: bool = True):
        self.quantity = F("amount") - Decimal(amount)
        if commit:
            self.save(update_fields=["amount"])




class BankDetails(models.Model):
    name = models.CharField(max_length=200, default="Bank Name")
    account = models.CharField(max_length=200, default="Account")

    class Meta:
        ordering = ("-name",)

    def __str__(self):
        return '{}-{}'.format(str(self.name), self.account)


class BankTransaction(models.Model):
    date_time = models.DateTimeField(null=True, blank=True)
    entered_date = models.DateTimeField(null=True, blank=True)
    TRA_TYPES = (('Deposit', 'Deposit'), ('Withdrawal', 'Withdrawal'))
    transaction_type =models.CharField(choices=TRA_TYPES, default="Deposit", max_length=100)
    bank = models.ForeignKey(BankDetails, null=True, blank=True, on_delete=models.DO_NOTHING)
    description = models.CharField(max_length=254, default="Paid to")
    entered_by = models.ForeignKey(FinanceProfile, on_delete=models.DO_NOTHING,
                                   related_name="depositFinancePerson", null=True, blank=True)
    remark = models.CharField(null=True, max_length=200)
    amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
    )
    deposit_mode = models.CharField(max_length=200, default='PETTY CASH')
    deposit_id = models.CharField(max_length=200, default='ID')
    class Meta:
        ordering = ("-date_time",)

    def __str__(self):
        return '{} {}'.format(str(self.date_time), self.entered_by.user.name)


    def increase_amount(self, amount: float, commit: bool = True):
        """Return given quantity of product to a stock."""
        self.quantity = F("amount") + Decimal(amount)
        if commit:
            self.save(update_fields=["amount"])

    def decrease_amount(self, amount: float, commit: bool = True):
        self.quantity = F("amount") - Decimal(amount)
        if commit:
            self.save(update_fields=["amount"])
