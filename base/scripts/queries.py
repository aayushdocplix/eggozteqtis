from custom_auth.models import User
from retailer.models import CommissionSlab, Retailer


def update_commission_slab():
    commission_slab, created = CommissionSlab.objects.get_or_create(number=25, type="%")
    retailers = Retailer.objects.all()
    for retailer in retailers:
        retailer.commission_slab = commission_slab
        retailer.save()


def get_unique_phone_number():
    phone_number = 8000000001
    users = User.objects.all()
    for user in users:
        phone_number_zzz = "+91" + str(phone_number)
        user.phone_no = phone_number_zzz
        user.save()
        phone_number = phone_number + 1
    return "updated"
