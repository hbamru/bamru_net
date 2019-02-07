import logging
from datetime import datetime, timedelta

from anymail.signals import tracking
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.dispatch import receiver
from django.forms.widgets import HiddenInput, Select, SelectDateWidget, Widget
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape
from django.views import generic
from django_twilio.decorators import twilio_view
from django_twilio.request import decompose
from twilio.twiml.messaging_response import MessagingResponse

from main.models import Member, Participant, Period

from main.models import (Distribution, InboundSms, Message, OutboundEmail,
                         OutboundSms, RsvpTemplate)
from main.tasks import message_send

logger = logging.getLogger(__name__)


class MessageCreateView(LoginRequiredMixin, generic.ListView):
    model = Message
    template_name = 'message_add.html'
    context_object_name = 'member_list'
    page_format = None  # to override in urls

    #def get_success_url(self): FIXME
    #    return self.object.get_absolute_url()

    def get_queryset(self):
        """Return context for standard paging."""
        format_convert = {'headsUp': ['invite', 'Heads Up'],
                          'available': ['invite', 'Available?'],
                          'leave': ['leave', 'Left?'],
                          'return': ['return', 'Returned?'],
                          'info': ['info', None],
                          'broadcast': ['broadcast', None],
                          'test': ['test', 'Test']
                          }
        initial = {}
        initial['author'] = self.request.user.pk
        initial['type'] = "std_page"
        initial['format'] = 'page'
        members = None
        period_id = self.request.GET.get('period')
        page_format = self.request.GET.get('page_format', self.page_format)
        period_format = format_convert[page_format][0]
        rsvp_name = format_convert[page_format][1]
        rsvp_template = None
        if rsvp_name is not None:
            try:
                rsvp_template = RsvpTemplate.objects.get(name=rsvp_name)
                initial['rsvp_template'] = rsvp_template
            except RsvpTemplate.DoesNotExist:
                logger.error('RsvpTemplate {} not found for format: {}'.format(
                    rsvp_name, page_format))
        if page_format == 'test':
            initial['type'] = "test"
            initial['input'] = datetime.now().strftime("Test page: %A, %d. %B %Y %I:%M%p")
            members = Member.members.filter(id=self.request.user.pk)
        if period_id:
            try:
                period = Period.objects.get(pk=period_id)
            except Period.DoesNotExist:
                logger.error('Period not found for: ' + period_id)
                raise Http404(
                    'Period {} specified, but does not exist'.format(period_id))
            initial['period_id'] = period_id
            initial['period_format'] = period_format
            initial['period'] = str(period)

            if period_format == 'invite':
                members = (Member.members.filter(status__in=Member.AVAILABLE_MEMBERS)
                .exclude(participant__period=period_id))
            elif period_format == 'leave':
                members = period.members_for_left_page()
            elif period_format == 'return':
                members = period.members_for_returned_page()
            elif period_format == 'info':
                members = Member.members.filter(participant__period=period_id)
            elif period_format == 'broadcast':
                members = Member.members.filter(status__in=Member.AVAILABLE_MEMBERS)
            elif period_format == 'test':
                members = Member.members.filter(participant__period=period_id)
            else:
                logger.error('Period format {} not found for: {}'.format(
                period_format, self.request.body))
            if (rsvp_template != None):
                initial['input'] = "{}: {}".format(str(period), rsvp_template.text)
            else:
                initial['input'] = "{}: ".format(str(period))

        self.initial = initial
        return members

    def get_context_data(self, **kwargs):
        '''Add additional useful information.'''
        context = super().get_context_data(**kwargs)
        return {**context, **self.initial}


class MessageDetailView(LoginRequiredMixin, generic.DetailView):
    model = Message
    template_name = 'message_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        message = self.object
        sent = 0
        delivered = 0
        rsvp = 0
        rsvp_yes = 0
        rsvp_no = 0
        for d in message.distribution_set.all():
            sent += 1
            if d.rsvp:
                rsvp += 1
                if d.rsvp_answer:
                    rsvp_yes += 1
                else:
                    rsvp_no += 1
            this_delivered = False
            for m in d.outboundsms_set.all():
                this_delivered |= m.delivered
            for m in d.outboundemail_set.all():
                this_delivered |= m.delivered
            if this_delivered:
                delivered += 1
        context['stats'] = "{} sent, {} delivered, {} RSVPed".format(
            sent, delivered, rsvp)
        context['rsvp'] = "{} yes, {} no, {} unresponded".format(
            rsvp_yes, rsvp_no, sent - rsvp_yes - rsvp_no)
        return context


class MessageListView(LoginRequiredMixin, generic.ListView):
    template_name = 'message_list.html'
    context_object_name = 'message_list'

    def get_queryset(self):
        """Return event list within the last year """
        qs = Message.objects.all()
        qs = qs.filter(created_at__gte=timezone.now() - timedelta(days=365))
        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add column sort for datatable (zero origin)
        context['sortOrder'] = '2, "dsc"'
        return context


class MessageInboxView(LoginRequiredMixin, generic.ListView):
    template_name = 'message_list.html'
    context_object_name = 'message_list'

    def get_queryset(self):
        """Return event list within the last year """
        qs = Message.objects.all()
        qs = qs.filter(created_at__gte=timezone.now() - timedelta(days=365))
        member_id = self.kwargs.get('member_id', None)
        if member_id:
            qs = qs.filter(distribution__member__id=member_id)
        return qs.order_by('-created_at')


def handle_distribution_rsvp(request, distribution, rsvp=False):
    """Helper function to process a RSVP response.
    distribution -- A Distribution object
    rsvp -- boolean RSVP response
    """
    distribution.rsvp = True
    distribution.rsvp_answer = rsvp
    distribution.save()

    participant_filter = {'period': distribution.message.period,
                          'member': distribution.member}
    if distribution.message.period_format == 'invite':
        if distribution.rsvp_answer:
            Participant.objects.get_or_create(**participant_filter)
            return 'RSVP yes to {} successful.'.format(distribution.message.period)
        p = Participant.objects.filter(**participant_filter).first()
        if p:
            p.delete()
            return 'Canceled RSVP to {}.'.format(distribution.message.period)
        return 'RSVP no to {} recorded.'.format(distribution.message.period)

    p = Participant.objects.filter(**participant_filter).first()
    if p:
        response = None
        if distribution.message.period_format == 'leave':
            if distribution.rsvp_answer:
                p.en_route_at = timezone.now()
                p.save()
                response = 'Departure time recorded for {}.'
            else:
                p.en_route_at = None
                p.save()
                response = 'Departure time cleared for {}.'
        elif distribution.message.period_format == 'return':
            if distribution.rsvp_answer:
                p.return_home_at = timezone.now()
                p.save()
                response = 'Return time recorded for {}.'
            else:
                p.return_home_at = None
                p.save()
                response = 'Return time cleared for {}.'
        else:
            if distribution.rsvp_answer:
                response = 'Response yes to {} received.'
            else:
                response = 'Response no to {} received.'
        return response.format(distribution.message.period)

    logger.error('Participant not found for: ' + str(request.body))
    return ('Error: You were not found as a participant for {}.'
            .format(distribution.message.period))


def unauth_rsvp(request, token):
    d = get_object_or_404(Distribution, unauth_rsvp_token=token)
    if d.unauth_rsvp_expires_at < timezone.now():
        response_text = 'Error: token expired'
    else:
        rsvp = request.GET.get('rsvp')[0].lower() == 'y'
        response_text = handle_distribution_rsvp(request, d, rsvp)
    return HttpResponse(response_text)  # TODO template


@twilio_view
def sms_callback(request):
    twilio_request = decompose(request)
    sms = OutboundSms.objects.get(sid=twilio_request.messagesid)
    sms.status = twilio_request.messagestatus
    if sms.status == 'delivered':
        sms.delivered = True
    if hasattr(twilio_request, 'errorcode'):
        sms.error_code = twilio_request.errorcode
    sms.save()
    logger.info('sms_callback for {}: {}'.format(sms.sid, sms.status))
    return HttpResponse('')


@twilio_view
def sms(request):
    """Handle an incomming SMS message."""
    response = MessagingResponse()
    twilio_request = decompose(request)
    try:
        sms = InboundSms.objects.create(sid=twilio_request.messagesid,
                                        from_number=twilio_request.from_,
                                        to_number=twilio_request.to,
                                        body=twilio_request.body)
        logger.info('Received SMS from {}: {}'.format(twilio_request.from_,
                                                      twilio_request.body))
    except:
        logger.error('Unable to save message: ' + str(request.body))
        response.message('BAMRU.net Error: unable to parse your message.')
        return response

    date_from = timezone.now() - timedelta(hours=12)
    outbound = (OutboundSms.objects
                .filter(destination=twilio_request.from_,
                        source=twilio_request.to,
                        distribution__message__rsvp_template__isnull=False,
                        created_at__gte=date_from)
                .order_by('-pk').first())
    if (not outbound) or (not outbound.distribution):
        logger.error('No matching OutboundSms from: {} to: {} body: {}'.format(
            twilio_request.from_, twilio_request.to, twilio_request.body))
        response.message(
            'BAMRU.net Warning: response ignored. No RSVP question in the past 24 hours.')
        return response

    yn = twilio_request.body[0].lower()
    if yn != 'y' and yn != 'n':
        logger.error('Unable to parse y/n message: ' + str(request.body))
        response.message('Could not parse yes/no in your message. Start your message with y or n.')
        return response

    response.message(handle_distribution_rsvp(
        request, outbound.distribution, (yn == 'y')))
    return response


@receiver(tracking)
def handle_outbound_email_tracking(sender, event, esp_name, **kwargs):
    logger.info('{}: {} ({})'.format(event.message_id,
                                     event.event_type, event.description))
    email = OutboundEmail.objects.get(sid=event.message_id)
    email.status = event.event_type
    email.error_message = event.description
    if email.error_message is None:
        email.error_message = ''
    if event.event_type == 'delivered':
        email.delivered = True
    if event.event_type == 'opened':
        email.opened = True
    email.save()


class ActionBecomeDo(LoginRequiredMixin, generic.ListView):
    model = Message
    template_name = 'message_add.html'
    context_object_name = 'member_list'

    #def get_success_url(self): FIXME
    #    return self.object.get_absolute_url()

    def get_queryset(self):
        """Return context with members to page."""
        initial = {}
        initial['author'] = self.request.user.pk
        members = None
        period_id = self.request.GET.get('period')
        period_format = self.request.GET.get('period_format')
        page = self.request.GET.get('page')

    def get_queryset(self):
        """Return the member list."""
        return Member.objects.filter(status__in=Member.DO_SHIFT_MEMBERS).order_by('id')

    def get_context_data(self, **kwargs):
        """Return context for become DO"""
        context = super().get_context_data(**kwargs)

        context['type'] = "become_do"

        # DO PII
        do = self.request.user
        context['title'] = "Page DO transition"

        context['format'] = 'page'
        context['period_format'] = 'broadcast'
        # text box canned message
        start = datetime.now()
        # set end to next Tuesday
        end = start + timedelta(7 - (start.weekday() - 1)  % 7)
        do_shift = "{} to {}".format(start.strftime("0800 %B %-d"),
                                     end.strftime("0800 %B %-d"))
        input = "BAMRU DO from {} is {} ({}, {})"
        context['input'] = input.format( do_shift, do.full_name,
                                         do.display_phone, do.display_email)
        context['confirm_prologue']  = "Correct data and time for your shift?\\n"
        context['type'] = "do_page"

        return context
