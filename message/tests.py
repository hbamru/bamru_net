import json
import subprocess

from django.conf import settings
from django.core import mail
from django.test import Client, TestCase
from django.test.utils import override_settings
from model_mommy import mommy

from bnet.models import Email, Participant

from .models import *


@override_settings(EMAIL_BACKEND='anymail.backends.test.EmailBackend')
class OutgoingEmailTestCase(TestCase):
    def setUp(self):
        self.address = 'message_test@example.com'
        self.email = mommy.make(Email,
                                address=self.address,
                                make_m2m=True)
        self.distribution = mommy.make(Distribution,
                                       member=self.email.member,
                                       email=True,
                                       phone=False,
                                       make_m2m=True)

    def test_send(self):
        self.distribution.message.send()

        # Test that one message was sent:
        self.assertEqual(len(mail.outbox), 1)

        self.assertEqual(mail.outbox[0].to, [self.address])

        # TODO test click on link


@override_settings(MESSAGE_FILE_PATH='/tmp/message_log',
                   DJANGO_TWILIO_FORGERY_PROTECTION=False)
class OutgoingSmsTestCase(TestCase):
    def setUp(self):
        self.number = '+15551234567'
        self.phone = mommy.make(Phone,
                                number=self.number,
                                make_m2m=True)
        self.distribution = mommy.make(Distribution,
                                       member=self.phone.member,
                                       email=False,
                                       phone=True,
                                       make_m2m=True)
        self.c = Client()

    def test_send(self):
        # Send a generic page
        self.distribution.message.send()

        # Check that it is logged
        f = settings.SMS_FILE_PATH + '/sms.log'
        proc = subprocess.Popen(['tail', '-n', '1', f], stdout=subprocess.PIPE)
        lines = proc.stdout.readlines()
        data = json.loads(lines[0].decode('utf-8'))

        self.assertEqual(data['to'], self.number)
        self.assertEqual(data['body'], self.distribution.message.text)

        # Emulate a status callback
        sms = self.distribution.outboundsms_set.first()
        sms_id = sms.id
        self.assertEqual(sms.delivered, False)
        response = self.c.post(reverse('message:sms_callback'),
                               {'MessageSid': sms.sid,
                                'MessageStatus': 'delivered',
                                })
        self.assertEqual(response.status_code, 200)

        # Make sure it's now marked as delivered
        sms = OutboundSms.objects.get(id=sms_id)
        self.assertEqual(sms.delivered, True)


@override_settings(MESSAGE_FILE_PATH='/tmp/message_log',
                   DJANGO_TWILIO_FORGERY_PROTECTION=False)
class IncommingSmsTestCase(TestCase):
    def setUp(self):
        self.number = '+15552345678'
        self.phone = mommy.make(Phone,
                                number=self.number,
                                make_m2m=True)
        self.participant = mommy.make(Participant,
                                      member=self.phone.member,
                                      make_m2m=True)
        self.distribution = mommy.make(Distribution,
                                       member=self.phone.member,
                                       message__period=self.participant.period,
                                       message__format='page',
                                       message__period_format='leave',
                                       email=False,
                                       phone=True,
                                       make_m2m=True)
        self.c = Client()

    def test_send(self):
        # Send a transit page
        self.distribution.message.send()

        # Check no RSVP before
        self.assertIsNone(self.participant.en_route_at)

        # Respond Yes to page
        response = self.c.post(reverse('message:sms'),
                               {'To': '+5550123456',
                                'From': self.number,
                                'MessageSid': 'FAKE_SID_SMS',
                                'Body': 'Yes',
                                })
        self.assertEqual(response.status_code, 200)

        # Check that RSVP is now there
        p2 = Participant.objects.get(pk=self.participant.id)
        self.assertIsNotNone(p2.en_route_at)
