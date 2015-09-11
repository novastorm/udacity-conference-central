#!/usr/bin/env python

"""models.py

Udacity conference server-side Python App Engine data & ProtoRPC models

$Id: models.py,v 1.1 2014/05/24 22:01:10 wesc Exp $

created/forked from conferences.py by wesc on 2014 may 24

"""

__author__ = 'wesc+api@google.com (Wesley Chun)'

import httplib
import endpoints
from protorpc import messages
from google.appengine.ext import ndb

class ConflictException(endpoints.ServiceException):
    """ConflictException -- exception mapped to HTTP 409 response"""
    http_status = httplib.CONFLICT

class ConferenceLink(ndb.Model):
    """ConferenceLink -- used to hold basic conference information for quick access
    to pertinent conference information
    """
    name          = ndb.StringProperty(required=True)
    websafeKey    = ndb.StringProperty(required=True)

class SessionLink(ndb.Model):
    """SessionLink -- used to hold basic session information for quick access
    to pertinent session information
    """
    name          = ndb.StringProperty(required=True)
    websafeKey    = ndb.StringProperty(required=True)

class SpeakerLink(ndb.Model):
    """SpeakerLink -- used to hold basic speaker information for quick access
    to pertinent speaker information
    """
    name       = ndb.StringProperty()
    numberOfSessions = ndb.IntegerProperty()
    websafeKey = ndb.StringProperty()

class Profile(ndb.Model):
    """Profile -- User profile object"""
    displayName     = ndb.StringProperty()
    mainEmail       = ndb.StringProperty()
    teeShirtSize    = ndb.StringProperty(default='NOT_SPECIFIED')
    conferenceKeysToAttend = ndb.StringProperty(repeated=True)
    sessionWishlist = ndb.StructuredProperty(SessionLink, repeated=True)

class ProfileMiniForm(messages.Message):
    """ProfileMiniForm -- update Profile form message"""
    displayName  = messages.StringField(1)
    teeShirtSize = messages.EnumField('TeeShirtSize', 2)

class ProfileForm(messages.Message):
    """ProfileForm -- Profile outbound form message"""
    displayName     = messages.StringField(1)
    mainEmail       = messages.StringField(2)
    teeShirtSize    = messages.EnumField('TeeShirtSize', 3)
    conferenceKeysToAttend = messages.StringField(4, repeated=True)
    sessionWishlist = messages.StringField(5, repeated=True)

class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    data = messages.StringField(1, required=True)

class BooleanMessage(messages.Message):
    """BooleanMessage-- outbound Boolean value message"""
    data = messages.BooleanField(1)

class Conference(ndb.Model):
    """Conference -- Conference object"""
    name            = ndb.StringProperty(required=True)
    description     = ndb.StringProperty()
    organizerUserId = ndb.StringProperty()
    topics          = ndb.StringProperty(repeated=True)
    city            = ndb.StringProperty()
    startDate       = ndb.DateProperty()
    month           = ndb.IntegerProperty() # TODO: do we need for indexing like Java?
    endDate         = ndb.DateProperty()
    maxAttendees    = ndb.IntegerProperty()
    seatsAvailable  = ndb.IntegerProperty()
    sessions        = ndb.StringProperty(repeated=True)
    speakers        = ndb.StructuredProperty(SpeakerLink, repeated=True)

class ConferenceForm(messages.Message):
    """ConferenceForm -- Conference outbound form message"""
    name            = messages.StringField(1)
    description     = messages.StringField(2)
    organizerUserId = messages.StringField(3)
    topics          = messages.StringField(4, repeated=True)
    city            = messages.StringField(5)
    startDate       = messages.StringField(6) #DateTimeField()
    month           = messages.IntegerField(7)
    maxAttendees    = messages.IntegerField(8)
    seatsAvailable  = messages.IntegerField(9)
    endDate         = messages.StringField(10) #DateTimeField()
    websafeKey      = messages.StringField(11)
    organizerDisplayName = messages.StringField(12)
    sessions        = messages.StringField(13, repeated=True)
    speakers        = messages.StringField(14, repeated=True)

class ConferenceForms(messages.Message):
    """ConferenceForms -- multiple Conference outbound form message"""
    items = messages.MessageField(ConferenceForm, 1, repeated=True)

class TeeShirtSize(messages.Enum):
    """TeeShirtSize -- t-shirt size enumeration value"""
    NOT_SPECIFIED = 1
    XS_M = 2
    XS_W = 3
    S_M = 4
    S_W = 5
    M_M = 6
    M_W = 7
    L_M = 8
    L_W = 9
    XL_M = 10
    XL_W = 11
    XXL_M = 12
    XXL_W = 13
    XXXL_M = 14
    XXXL_W = 15

class ConferenceQueryForm(messages.Message):
    """ConferenceQueryForm -- Conference query inbound form message"""
    field = messages.StringField(1)
    operator = messages.StringField(2)
    value = messages.StringField(3)

class ConferenceQueryForms(messages.Message):
    """ConferenceQueryForms -- multiple ConferenceQueryForm inbound form message"""
    filters = messages.MessageField(ConferenceQueryForm, 1, repeated=True)


###############################################################################
#
# Session object
#

class Session(ndb.Model):
    """Session -- Conference Session object"""
    name          = ndb.StringProperty(required=True)
    highlights    = ndb.StringProperty()
    duration      = ndb.IntegerProperty()
    typeOfSession = ndb.StringProperty(default='NOT_SPECIFIED')
    date          = ndb.DateProperty()
    startTime     = ndb.TimeProperty()
    # speakers      = ndb.StringProperty(repeated=True) # Speaker name
    speakers      = ndb.StructuredProperty(SpeakerLink, repeated=True) # Speaker name

class SessionForm(messages.Message):
    """SessionForm -- Session outbound form message"""
    name          = messages.StringField(1)
    highlights    = messages.StringField(2)
    duration      = messages.IntegerField(3)
    typeOfSession = messages.StringField(4)
    date          = messages.StringField(5) # DateField YYYY-MM-DD
    startTime     = messages.StringField(6) # TimeField HH:MM
    websafeKey    = messages.StringField(7)
    speakers      = messages.StringField(8, repeated=True)

class SessionForms(messages.Message):
    """SessionForms -- multiple Session outbound form message"""
    items = messages.MessageField(SessionForm, 1, repeated=True)


###############################################################################
#
# SessionType object
#

class SessionType(ndb.Model):
    """SessionType -- Session type list"""
    label = ndb.StringProperty()

class SessionTypeResponse(messages.Message):
    """SessionTypeResponse -- Session type response form"""
    label      = messages.StringField(1)
    websafeKey = messages.StringField(2)

class SessionTypeListResponse(messages.Message):
    """SessionTypeListResponse -- Session type list response form"""
    items = messages.MessageField(SessionTypeResponse, 1, repeated=True)


###############################################################################
#
# Wishlist object
#

class ConferenceSessionWishlistRequest(messages.Message):
    """ConferenceSessionWishlistRequest -- Conference session wishlist request
    form
    """
    websafeConferenceKey = messages.StringField(1)


###############################################################################
#
# Speaker object
#

class Speaker(ndb.Model):
    """Speaker -- Conference Speaker object"""
    name        = ndb.StringProperty()
    description = ndb.StringProperty()
    sessions    = ndb.StructuredProperty(SessionLink, repeated=True) # Session name

    # def sessions(self):
    #     return Session.query(self.key.urlsafe().IN(Session.speakers))

    # on update speaker
    # update conferences containing this speaker
    # update sessions containining this speaker

class SpeakerRequest(messages.Message):
    """SpeakerRequest -- Speaker outbound form message"""
    websafeConferenceKey = messages.StringField(1)
    name        = messages.StringField(2)
    description = messages.StringField(3)

class SpeakerResponse(messages.Message):
    """SpeakerForm -- Speaker outbound form message"""
    name        = messages.StringField(1)
    description = messages.StringField(2)
    websafeKey = messages.StringField(3)

class SpeakerListResponse(messages.Message):
    """SpeakerForms -- multiple Speaker outbound form message"""
    items = messages.MessageField(SpeakerResponse, 1, repeated=True)

