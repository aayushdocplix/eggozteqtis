from django.core.mail import send_mail, EmailMessage
from rest_framework import viewsets, permissions
from django_filters import rest_framework as filters

from Eggoz.settings import FROM_EMAIL
from base.response import Created, BadRequest
from farmer.models import Farmer
from feedback.api import FeedbackSerializer
from feedback.api.serializers import FarmerFeedbackCreateSerializer, FarmerFeedbackSerializer, \
    CustomerFeedbackSerializer
from feedback.models import Feedback, FarmerFeedback, CustomerFeedback


class FeedbackViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Feedback.objects.all().order_by('-feedback_date')
    serializer_class = FeedbackSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        data = serializer.data
        request_person_name = data.get('first_name') + " " + data.get('last_name')
        contact_eggoz_msg_body = {
            "subject": data.get('query_type'),
            "body": "Feedback \n%s \nFrom \nName: %s \nPhone- %s \nEmail- %s" % (
                data.get('message'), request_person_name, data.get('phone'), data.get('email', ''))
        }
        send_mail(contact_eggoz_msg_body.get('subject'), contact_eggoz_msg_body.get('body'), FROM_EMAIL,
                  ['contact@eggoz.in'])
        email = EmailMessage(
            "Eggoz - Your Feedback has been received succesfully", "Check our farmer app at https://play.google.com/store/apps/details?id=com.antino.eggoz", FROM_EMAIL,
            [data.get('email', 'contact@eggoz.in')])
        email.send()
    #    EmailMessage(body="test",reply_to=email).send()
        return Created(data, headers=headers)


class FarmerFeedbackViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = FarmerFeedback.objects.all().order_by('-created_at')
    serializer_class = FarmerFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('farmer', 'query_type')

    def create(self, request, *args, **kwargs):
        serializer = FarmerFeedbackCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        farmer = Farmer.objects.filter(farmer=user).first()
        if farmer:
            farmer_feedback = serializer.save(farmer=farmer)
            email_body = "Farmer Name:- " + user.name + "\nFarmer Id:-" + str(farmer.id) + "\nTitle:-" + str(
                farmer_feedback.title) + "\nMessage:-" + str(farmer_feedback.message)
            contact_eggoz_msg_body = {
                "subject": farmer_feedback.query_type,
                "body": email_body
            }
            email = EmailMessage(
                contact_eggoz_msg_body.get('subject'), contact_eggoz_msg_body.get('body'), FROM_EMAIL,
                ['info@eggoz.in'])
            if farmer_feedback.file:
                email.attach_file(farmer_feedback.file.path)
            email.send()
            return Created({"success": "%s Submitted successfully" % (farmer_feedback.query_type)})
        else:
            return BadRequest({'error_type': "ValidationError",
                               'errors': [{'message': "farmer profile not created"}]})


class CustomerFeedbackViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = CustomerFeedback.objects.all().order_by('-created_at')
    serializer_class = CustomerFeedbackSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('name', 'issue_type', 'batch_no')

