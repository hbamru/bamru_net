from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

# Register your models here.

class InlineDefaults(admin.TabularInline):
    extra = 0
    min_num = 0

class AddressInline(InlineDefaults):
    model = Address

class EmailInline(InlineDefaults):
    model = Email

class PhoneInline(InlineDefaults):
    model = Phone

class EmergencyContactInline(InlineDefaults):
    model = EmergencyContact

class RoleInline(InlineDefaults):
    model = Role

class OtherInfoInline(InlineDefaults):
    model = OtherInfo

class MemberUserAdmin(UserAdmin):
    """Override broken defaults from UserAdmin"""
    fieldsets = None
    search_fields = []

@admin.register(Member)
class MemberAdmin(MemberUserAdmin):
    list_display = ('last_name', 'first_name', 'status')
#xxx    list_filter = ('status', )
    search_fields = ['last_name', 'first_name', 'username',]
    inlines = [
        AddressInline,
        EmailInline,
        PhoneInline,
        EmergencyContactInline,
        RoleInline,
        OtherInfoInline,
        ]


class ParticipantInline(InlineDefaults):
    model = Participant

class PeriodInline(InlineDefaults):
    model = Period

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'start_on', 'finish_on',)
    inlines = [
        PeriodInline,
        ]

@admin.register(Period)
class PeriodAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'event', 'position', 'start_on', 'finish_on',)
    inlines = [
        ParticipantInline,
        ]

@admin.register(DoAvailable)
class DoAvailableAdmin(admin.ModelAdmin):
    search_fields = ['member__last_name', 'member__first_name', 'member__username']


class DistributionInline(InlineDefaults):
    model = Distribution


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('author', 'text', 'created_at',
                    'format', 'period_format', )
    inlines = [
        DistributionInline,
    ]
