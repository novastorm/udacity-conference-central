#!/usr/bin/env python

"""
conference.py -- Udacity conference server-side Python App Engine API;
    uses Google Cloud Endpoints

$Id: conference.py,v 1.25 2014/05/24 23:42:19 wesc Exp wesc $

created by wesc on 2014 apr 21

"""

__author__ = 'wesc+api@google.com (Wesley Chun)'


from datetime import datetime

import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote

from google.appengine.api import memcache
from google.appengine.api import taskqueue
from google.appengine.ext import ndb

from google.net.proto.ProtocolBuffer import ProtocolBufferDecodeError

from models import ConflictException
from models import Profile
from models import ProfileMiniForm
from models import ProfileForm
from models import StringMessage
from models import BooleanMessage
from models import Conference
from models import ConferenceForm
from models import ConferenceForms
from models import ConferenceQueryForm
from models import ConferenceQueryForms
from models import Session
from models import SessionLink
from models import SessionForm
from models import SessionForms
from models import SessionType
from models import SessionTypeResponse
from models import SessionTypeListResponse
from models import TeeShirtSize
from models import ConferenceSessionWishlistRequest
from models import Speaker
from models import SpeakerRequest
from models import SpeakerResponse
from models import SpeakerListResponse

from settings import WEB_CLIENT_ID
from settings import ANDROID_CLIENT_ID
from settings import IOS_CLIENT_ID
from settings import ANDROID_AUDIENCE

from utils import getUserId

EMAIL_SCOPE = endpoints.EMAIL_SCOPE
API_EXPLORER_CLIENT_ID = endpoints.API_EXPLORER_CLIENT_ID
MEMCACHE_ANNOUNCEMENTS_KEY = "RECENT_ANNOUNCEMENTS"
ANNOUNCEMENT_TPL = ('Last chance to attend! The following conferences '
                    'are nearly sold out: %s')
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

DEFAULTS = {
    "city": "Default City",
    "maxAttendees": 0,
    "seatsAvailable": 0,
    "topics": [ "Default", "Topic" ],
}

OPERATORS = {
            'EQ':   '=',
            'GT':   '>',
            'GTEQ': '>=',
            'LT':   '<',
            'LTEQ': '<=',
            'NE':   '!='
            }

FIELDS =    {
            'CITY': 'city',
            'TOPIC': 'topics',
            'MONTH': 'month',
            'MAX_ATTENDEES': 'maxAttendees',
            }

CONF_GET_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeConferenceKey=messages.StringField(1),
)

CONF_POST_REQUEST = endpoints.ResourceContainer(
    ConferenceForm,
    websafeConferenceKey=messages.StringField(1),
)


CONF_SESS_INDEX_REQUEST = CONF_GET_REQUEST

CONF_SESS_STORE_REQUEST = endpoints.ResourceContainer(
    SessionForm,
    websafeConferenceKey=messages.StringField(1))

CONF_SESS_SHOW_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeSessionKey=messages.StringField(1))

CONF_SESS_UPDATE_REQUEST = endpoints.ResourceContainer(
    SessionForm,
    websafeSessionKey=messages.StringField(1))

CONF_SESS_DELETE_REQUEST = CONF_SESS_SHOW_REQUEST


SESS_TYPE_GET_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeSessionTypeKey=messages.StringField(1))

SESS_TYPE_POST_REQUEST = SESS_TYPE_GET_REQUEST


CONF_SPEAK_INDEX_REQ = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeConferenceKey=messages.StringField(1)
    )

CONF_SPEAK_STORE_REQ = endpoints.ResourceContainer(
    SpeakerRequest,
    websafeConferenceKey=messages.StringField(1)
    )

CONF_SPEAK_SHOW_REQ = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeSpeakerKey=messages.StringField(1)
    )

CONF_SPEAK_UPDATE_REQ = endpoints.ResourceContainer(
    SpeakerResponse,
    websafeSpeakerKey=messages.StringField(1)
    )

CONF_SPEAK_DELETE_REQ = CONF_SPEAK_SHOW_REQ


SESS_SPEAK_STORE_REQ = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeSessionKey=messages.StringField(1),
    websafeSpeakerKey=messages.StringField(2)
    )

SESS_SPEAK_DELETE_REQ = SESS_SPEAK_STORE_REQ


SESS_BY_SPEAKER_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    speaker=messages.StringField(1)
    )
SESS_BY_TYPE_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeConferenceKey=messages.StringField(1),
    typeOfSession=messages.StringField(2)
    )

SESS_WISH_STORE_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeSessionKey=messages.StringField(1)
    )

SESS_WISH_DELETE_REQUEST = SESS_WISH_STORE_REQUEST


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


@endpoints.api(name='conference', version='v1', audiences=[ANDROID_AUDIENCE],
    allowed_client_ids=[WEB_CLIENT_ID, API_EXPLORER_CLIENT_ID, ANDROID_CLIENT_ID, IOS_CLIENT_ID],
    scopes=[EMAIL_SCOPE])
class ConferenceApi(remote.Service):
    """Conference API v0.1"""

# - - - Conference objects - - - - - - - - - - - - - - - - -

    def _getUser(self):
        """Get the current user"""
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        return user

    def _getConference(self, websafeKey=None):
        """Get conference object for the given websafeKey"""
        try:
            a_conference = ndb.Key(urlsafe=websafeKey).get()
        except (TypeError) as e:
            raise endpoints.NotFoundException(
                'Invalid input conference key string: [%s]' % websafeKey)
        except (ProtocolBufferDecodeError) as e:
            raise endpoints.NotFoundException(
                'No conference found with key: [%s]' % websafeKey)
        except Exception as e:
            raise endpoints.NotFoundException('%s: %s' % (e.__class__.__name__, e))

        # TODO: check object kind
        # print "a_conference kind: [%s]" % a_conference._get_kind()

        return a_conference

    def _getSession(self, websafeKey=None):
        """Get conference object for the given websafeKey"""
        try:
            a_session = ndb.Key(urlsafe=websafeKey).get()
        except (TypeError) as e:
            raise endpoints.NotFoundException(
                'Invalid input session key string: [%s]' % websafeKey)
        except (ProtocolBufferDecodeError) as e:
            raise endpoints.NotFoundException(
                'No session found with key: [%s]' % websafeKey)
        except Exception as e:
            raise endpoints.NotFoundException('%s: %s' % (e.__class__.__name__, e))

        # TODO: check object kind
        # print "a_session kind: [%s]" % a_session._get_kind()

        return a_session

    def _getSpeaker(self, websafeKey=None):
        """Get conference object for the given websafeKey"""
        try:
            a_speaker = ndb.Key(urlsafe=websafeKey).get()
        except (TypeError) as e:
            raise endpoints.NotFoundException(
                'Invalid input speaker key string: [%s]' % websafeKey)
        except (ProtocolBufferDecodeError) as e:
            raise endpoints.NotFoundException(
                'No speaker found with key: [%s]' % websafeKey)
        except Exception as e:
            raise endpoints.NotFoundException('%s: %s' % (e.__class__.__name__, e))

        # TODO: check object kind
        # print "a_speaker kind: [%s]" % a_speaker._get_kind()

        return a_speaker

    def _copyConferenceToForm(self, conf, displayName):
        """Copy relevant fields from Conference to ConferenceForm."""
        cf = ConferenceForm()
        for field in cf.all_fields():
            if hasattr(conf, field.name):
                # convert Date to date string; just copy others
                if field.name.endswith('Date'):
                    setattr(cf, field.name, str(getattr(conf, field.name)))
                else:
                    setattr(cf, field.name, getattr(conf, field.name))
            elif field.name == "websafeKey":
                setattr(cf, field.name, conf.key.urlsafe())
        if displayName:
            setattr(cf, 'organizerDisplayName', displayName)
        cf.check_initialized()
        return cf


    def _createConferenceObject(self, request):
        """Create or update Conference object, returning ConferenceForm/request."""
        # preload necessary data items
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        user_id = getUserId(user)

        if not request.name:
            raise endpoints.BadRequestException("Conference 'name' field required")

        # copy ConferenceForm/ProtoRPC Message into dict
        data = {field.name: getattr(request, field.name) for field in request.all_fields()}
        del data['websafeKey']
        del data['organizerDisplayName']

        # add default values for those missing (both data model & outbound Message)
        for df in DEFAULTS:
            if data[df] in (None, []):
                data[df] = DEFAULTS[df]
                setattr(request, df, DEFAULTS[df])

        # convert dates from strings to Date objects; set month based on start_date
        if data['startDate']:
            data['startDate'] = datetime.strptime(data['startDate'][:10], "%Y-%m-%d").date()
            data['month'] = data['startDate'].month
        else:
            data['month'] = 0
        if data['endDate']:
            data['endDate'] = datetime.strptime(data['endDate'][:10], "%Y-%m-%d").date()

        # set seatsAvailable to be same as maxAttendees on creation
        if data["maxAttendees"] > 0:
            data["seatsAvailable"] = data["maxAttendees"]
        # generate Profile Key based on user ID and Conference
        # ID based on Profile key get Conference key from ID
        p_key = ndb.Key(Profile, user_id)
        c_id = Conference.allocate_ids(size=1, parent=p_key)[0]
        c_key = ndb.Key(Conference, c_id, parent=p_key)
        data['key'] = c_key
        data['organizerUserId'] = request.organizerUserId = user_id

        # create Conference, send email to organizer confirming
        # creation of Conference & return (modified) ConferenceForm
        Conference(**data).put()
        taskqueue.add(params={'email': user.email(),
            'conferenceInfo': repr(request)},
            url='/tasks/send_confirmation_email'
        )
        return request


    @ndb.transactional()
    def _updateConferenceObject(self, request):
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        user_id = getUserId(user)

        # copy ConferenceForm/ProtoRPC Message into dict
        data = {field.name: getattr(request, field.name) for field in request.all_fields()}

        # update existing conference
        conf = ndb.Key(urlsafe=request.websafeConferenceKey).get()
        # check that conference exists
        if not conf:
            raise endpoints.NotFoundException(
                'No conference found with key: %s' % request.websafeConferenceKey)

        # check that user is owner
        if user_id != conf.organizerUserId:
            raise endpoints.ForbiddenException(
                'Only the owner can update the conference.')

        # Not getting all the fields, so don't create a new object; just
        # copy relevant fields from ConferenceForm to Conference object
        for field in request.all_fields():
            data = getattr(request, field.name)
            # only copy fields where we get data
            if data not in (None, []):
                # special handling for dates (convert string to Date)
                if field.name in ('startDate', 'endDate'):
                    data = datetime.strptime(data, "%Y-%m-%d").date()
                    if field.name == 'startDate':
                        conf.month = data.month
                # write to Conference object
                setattr(conf, field.name, data)
        conf.put()
        prof = ndb.Key(Profile, user_id).get()
        return self._copyConferenceToForm(conf, getattr(prof, 'displayName'))


    @endpoints.method(ConferenceForm, ConferenceForm, path='conference',
            http_method='POST', name='createConference')
    def createConference(self, request):
        """Create new conference."""
        return self._createConferenceObject(request)


    @endpoints.method(CONF_POST_REQUEST, ConferenceForm,
            path='conference/{websafeConferenceKey}',
            http_method='PUT', name='updateConference')
    def updateConference(self, request):
        """Update conference w/provided fields & return w/updated info."""
        return self._updateConferenceObject(request)


    @endpoints.method(CONF_GET_REQUEST, ConferenceForm,
            path='conference/{websafeConferenceKey}',
            http_method='GET', name='getConference')
    def getConference(self, request):
        """Return requested conference (by websafeConferenceKey)."""
        # get Conference object from request; bail if not found
        conf = ndb.Key(urlsafe=request.websafeConferenceKey).get()
        if not conf:
            raise endpoints.NotFoundException(
                'No conference found with key: %s' % request.websafeConferenceKey)
        prof = conf.key.parent().get()
        # return ConferenceForm
        return self._copyConferenceToForm(conf, getattr(prof, 'displayName'))


    @endpoints.method(message_types.VoidMessage, ConferenceForms,
            path='getConferencesCreated',
            http_method='POST', name='getConferencesCreated')
    def getConferencesCreated(self, request):
        """Return conferences created by user."""
        # make sure user is authed
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        user_id = getUserId(user)

        # create ancestor query for all key matches for this user
        confs = Conference.query(ancestor=ndb.Key(Profile, user_id))
        prof = ndb.Key(Profile, user_id).get()
        # return set of ConferenceForm objects per Conference
        return ConferenceForms(
            items=[self._copyConferenceToForm(conf, getattr(prof, 'displayName')) for conf in confs]
        )


    def _getQuery(self, request):
        """Return formatted query from the submitted filters."""
        q = Conference.query()
        inequality_filter, filters = self._formatFilters(request.filters)

        # If exists, sort on inequality filter first
        if not inequality_filter:
            q = q.order(Conference.name)
        else:
            q = q.order(ndb.GenericProperty(inequality_filter))
            q = q.order(Conference.name)

        for filtr in filters:
            if filtr["field"] in ["month", "maxAttendees"]:
                filtr["value"] = int(filtr["value"])
            formatted_query = ndb.query.FilterNode(filtr["field"], filtr["operator"], filtr["value"])
            q = q.filter(formatted_query)
        return q


    def _formatFilters(self, filters):
        """Parse, check validity and format user supplied filters."""
        formatted_filters = []
        inequality_field = None

        for f in filters:
            filtr = {field.name: getattr(f, field.name) for field in f.all_fields()}

            try:
                filtr["field"] = FIELDS[filtr["field"]]
                filtr["operator"] = OPERATORS[filtr["operator"]]
            except KeyError:
                raise endpoints.BadRequestException("Filter contains invalid field or operator.")

            # Every operation except "=" is an inequality
            if filtr["operator"] != "=":
                # check if inequality operation has been used in previous filters
                # disallow the filter if inequality was performed on a different field before
                # track the field on which the inequality operation is performed
                if inequality_field and inequality_field != filtr["field"]:
                    raise endpoints.BadRequestException("Inequality filter is allowed on only one field.")
                else:
                    inequality_field = filtr["field"]

            formatted_filters.append(filtr)
        return (inequality_field, formatted_filters)


    @endpoints.method(ConferenceQueryForms, ConferenceForms,
            path='queryConferences',
            http_method='POST',
            name='queryConferences')
    def queryConferences(self, request):
        """Query for conferences."""
        conferences = self._getQuery(request)

        # need to fetch organiser displayName from profiles
        # get all keys and use get_multi for speed
        organisers = [(ndb.Key(Profile, conf.organizerUserId)) for conf in conferences]
        profiles = ndb.get_multi(organisers)

        # put display names in a dict for easier fetching
        names = {}
        for profile in profiles:
            names[profile.key.id()] = profile.displayName

        # return individual ConferenceForm object per Conference
        return ConferenceForms(
                items=[self._copyConferenceToForm(conf, names[conf.organizerUserId]) for conf in \
                conferences]
        )


# - - - Profile objects - - - - - - - - - - - - - - - - - - -

    def _copyProfileToForm(self, prof):
        """Copy relevant fields from Profile to ProfileForm."""
        # copy relevant fields from Profile to ProfileForm
        pf = ProfileForm()
        for field in pf.all_fields():
            if hasattr(prof, field.name):
                # convert t-shirt string to Enum; just copy others
                if field.name == 'teeShirtSize':
                    setattr(pf, field.name, getattr(TeeShirtSize, getattr(prof, field.name)))
                else:
                    setattr(pf, field.name, getattr(prof, field.name))
        pf.check_initialized()
        return pf


    def _getProfileFromUser(self):
        """Return user Profile from datastore, creating new one if non-existent."""
        # make sure user is authed
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')

        # get Profile from datastore
        user_id = getUserId(user)
        p_key = ndb.Key(Profile, user_id)
        profile = p_key.get()
        # create new Profile if not there
        if not profile:
            profile = Profile(
                key = p_key,
                displayName = user.nickname(),
                mainEmail= user.email(),
                teeShirtSize = str(TeeShirtSize.NOT_SPECIFIED),
            )
            profile.put()

        return profile      # return Profile


    def _doProfile(self, save_request=None):
        """Get user Profile and return to user, possibly updating it first."""
        # get user Profile
        prof = self._getProfileFromUser()

        # if saveProfile(), process user-modifyable fields
        if save_request:
            for field in ('displayName', 'teeShirtSize'):
                if hasattr(save_request, field):
                    val = getattr(save_request, field)
                    if val:
                        setattr(prof, field, str(val))
                        #if field == 'teeShirtSize':
                        #    setattr(prof, field, str(val).upper())
                        #else:
                        #    setattr(prof, field, val)
                        prof.put()

        # return ProfileForm
        return self._copyProfileToForm(prof)


    @endpoints.method(message_types.VoidMessage, ProfileForm,
            path='profile', http_method='GET', name='getProfile')
    def getProfile(self, request):
        """Return user profile."""
        return self._doProfile()


    @endpoints.method(ProfileMiniForm, ProfileForm,
            path='profile', http_method='POST', name='saveProfile')
    def saveProfile(self, request):
        """Update & return user profile."""
        return self._doProfile(request)


# - - - Announcements - - - - - - - - - - - - - - - - - - - -

    @staticmethod
    def _cacheAnnouncement():
        """Create Announcement & assign to memcache; used by
        memcache cron job & putAnnouncement().
        """
        confs = Conference.query(ndb.AND(
            Conference.seatsAvailable <= 5,
            Conference.seatsAvailable > 0)
        ).fetch(projection=[Conference.name])

        if confs:
            # If there are almost sold out conferences,
            # format announcement and set it in memcache
            announcement = ANNOUNCEMENT_TPL % (
                ', '.join(conf.name for conf in confs))
            memcache.set(MEMCACHE_ANNOUNCEMENTS_KEY, announcement)
        else:
            # If there are no sold out conferences,
            # delete the memcache announcements entry
            announcement = ""
            memcache.delete(MEMCACHE_ANNOUNCEMENTS_KEY)

        return announcement


    @endpoints.method(message_types.VoidMessage, StringMessage,
            path='conference/announcement/get',
            http_method='GET', name='getAnnouncement')
    def getAnnouncement(self, request):
        """Return Announcement from memcache."""
        return StringMessage(data=memcache.get(MEMCACHE_ANNOUNCEMENTS_KEY) or "")


# - - - Registration - - - - - - - - - - - - - - - - - - - -

    @ndb.transactional(xg=True)
    def _conferenceRegistration(self, request, reg=True):
        """Register or unregister user for selected conference."""
        retval = None
        prof = self._getProfileFromUser() # get user Profile

        # check if conf exists given websafeConfKey
        # get conference; check that it exists
        wsck = request.websafeConferenceKey
        conf = ndb.Key(urlsafe=wsck).get()
        if not conf:
            raise endpoints.NotFoundException(
                'No conference found with key: %s' % wsck)

        # register
        if reg:
            # check if user already registered otherwise add
            if wsck in prof.conferenceKeysToAttend:
                raise ConflictException(
                    "You have already registered for this conference")

            # check if seats avail
            if conf.seatsAvailable <= 0:
                raise ConflictException(
                    "There are no seats available.")

            # register user, take away one seat
            prof.conferenceKeysToAttend.append(wsck)
            conf.seatsAvailable -= 1
            retval = True

        # unregister
        else:
            # check if user already registered
            if wsck in prof.conferenceKeysToAttend:

                # unregister user, add back one seat
                prof.conferenceKeysToAttend.remove(wsck)
                conf.seatsAvailable += 1
                retval = True
            else:
                retval = False

        # write things back to the datastore & return
        prof.put()
        conf.put()
        return BooleanMessage(data=retval)


    @endpoints.method(message_types.VoidMessage, ConferenceForms,
            path='conferences/attending',
            http_method='GET', name='getConferencesToAttend')
    def getConferencesToAttend(self, request):
        """Get list of conferences that user has registered for."""
        prof = self._getProfileFromUser() # get user Profile
        conf_keys = [ndb.Key(urlsafe=wsck) for wsck in prof.conferenceKeysToAttend]
        conferences = ndb.get_multi(conf_keys)

        # get organizers
        organisers = [ndb.Key(Profile, conf.organizerUserId) for conf in conferences]
        profiles = ndb.get_multi(organisers)

        # put display names in a dict for easier fetching
        names = {}
        for profile in profiles:
            names[profile.key.id()] = profile.displayName

        # return set of ConferenceForm objects per Conference
        return ConferenceForms(items=[self._copyConferenceToForm(conf, names[conf.organizerUserId])\
         for conf in conferences]
        )


    @endpoints.method(CONF_GET_REQUEST, BooleanMessage,
            path='conference/{websafeConferenceKey}',
            http_method='POST', name='registerForConference')
    def registerForConference(self, request):
        """Register user for selected conference."""
        return self._conferenceRegistration(request)


    @endpoints.method(CONF_GET_REQUEST, BooleanMessage,
            path='conference/{websafeConferenceKey}',
            http_method='DELETE', name='unregisterFromConference')
    def unregisterFromConference(self, request):
        """Unregister user for selected conference."""
        return self._conferenceRegistration(request, reg=False)


    @endpoints.method(message_types.VoidMessage, ConferenceForms,
            path='filterPlayground',
            http_method='GET', name='filterPlayground')
    def filterPlayground(self, request):
        """Filter Playground"""
        q = Conference.query()
        # field = "city"
        # operator = "="
        # value = "London"
        # f = ndb.query.FilterNode(field, operator, value)
        # q = q.filter(f)
        q = q.filter(Conference.city=="London")
        q = q.filter(Conference.topics=="Medical Innovations")
        q = q.filter(Conference.month==6)

        return ConferenceForms(
            items=[self._copyConferenceToForm(conf, "") for conf in q]
        )


# - - - Session - - - - - - - - - - - - - - - - - - - -

    def _copySessionToForm(self, a_session):
        """Copy relevant field from Session to SessionForm."""
        a_form = SessionForm()
        for field in a_form.all_fields():
            if hasattr(a_session, field.name):
                if field.name == 'date' or field.name == 'startTime':
                    setattr(a_form, field.name, str(getattr(a_session, field.name)))
                else:
                    setattr(a_form, field.name, getattr(a_session, field.name))
            elif field.name == "websafeKey":
                setattr(a_form, field.name, a_session.key.urlsafe())
        a_form.check_initialized()
        return a_form


    def _storeSessionObject(self, request):
        """Create conference session object, return SessionForm/request."""

        user = self._getUser()
        a_conference = self._getConference(request.websafeConferenceKey)

        # check for session name
        if not request.name:
            raise endpoints.BadRequestException(
                "Conference session 'name' field required")

        # check for duplicate
        if Session.query(Session.name == request.name).get():
            raise endpoints.BadRequestException(
                "Duplicate conference session 'name'")

        # copy request input to  dict
        data = {field.name: getattr(request, field.name) for field in request.all_fields()}
        # remove extraneous input field data
        del data['websafeConferenceKey']
        del data['websafeKey']
        # add default values for missing data
        # convert dates from strings to Data objects
        if data['date']:
            data['date'] = datetime.strptime(data['date'], "%Y-%m-%d").date()
        if data['startTime']:
            data['startTime'] = datetime.strptime(data['startTime'], "%H:%M").time()

        # allocate conference session id
        session_id = Session.allocate_ids(size=1, parent=a_conference.key)[0]
        session_key = ndb.Key(Session, session_id, parent=a_conference.key)
        data['key'] = session_key
        # create session
        a_session = Session(**data)
        a_session.put()
        # append session to conference
        # a_conference.sessions.append(session_key.urlsafe())
        # a_conference.put()

        return self._copySessionToForm(a_session)


    def _updateSessionObject(self, request):
        """Update conference session object, return SessionFrom"""

        user = self._getUser()
        a_session = self._getSession(request.websafeSessionKey)

        # Not getting all the fields, so don't create a new object; just
        # copy relevant fields from SessionForm to a ConferenceSession object
        for field in request.all_fields():
            data = getattr(request, field.name)
            # remove attribute if data is an empty
            if data == "":
                delattr(a_course, field.name)
            # only copy fields where we get data
            elif data not in (None, []):
                # special handling for date (convert string to Date)
                if field.name == 'date':
                    data['date'] = datetime.strptime(data['date'], "%Y-%m-%d").date()
                # special handling for time (convert string to Time)
                if field.name == 'startTime':
                    data['startTime'] = datetime.strptime(data['startTime'], "%H:%M").time()
                # write to Conference object
                setattr(a_session, field.name, data)
        a_session.put()
        return self._copySessionToForm(a_session)

    @ndb.transactional()
    def _destroySessionObject(self, request):
        """destroy conference session object, return SessionForm"""

        user = self._getUser()
        a_session= self._getSession(request.websafeSessionKey)

        a_conference = a_session.key.parent().get()
        a_conference.sessions.remove(a_session.key.urlsafe())
        a_conference.put()
        a_session.key.delete()

        return self._copySessionToForm(a_session)


    @endpoints.method(CONF_SESS_STORE_REQUEST, SessionForm,
        path='conference/{websafeConferenceKey}/session',
        http_method='POST',
        name='createSession')
    def createSession(self, request):
        """Create conference session"""
        return self._storeSessionObject(request)


    @endpoints.method(CONF_SESS_UPDATE_REQUEST, SessionForm,
        path='conference/session/{websafeSessionKey}',
        http_method='PUT',
        name='updateSession')
    def updateSession(self, request):
        """Update conference session"""
        return self._updateSessionObject(request)


    @endpoints.method(CONF_SESS_DELETE_REQUEST, SessionForm,
        path='conference/session/{websafeSessionKey}',
        http_method='DELETE',
        name='destroySession')
    def destroySession(self, request):
        """Destroy conference session"""
        return self._destroySessionObject(request)


    def _listConferenceSessions(self, request):
        """List session objects, return SessionForms"""
        a_conference_key = ndb.Key(urlsafe=request.websafeConferenceKey)
        session_list = Session.query(ancestor=a_conference_key)

        return SessionForms(
            items=[self._copySessionToForm(session) for session in session_list]
        )


    @endpoints.method(CONF_SESS_INDEX_REQUEST, SessionForms,
        path='conference/{websafeConferenceKey}/session',
        http_method='GET',
        name='getConferenceSessions')
    def getConferenceSessions(self, request):
        """Get list of conference Sessions"""
        return self._listConferenceSessions(request)


# - - - SessionType- - - - - - - - - - - - - - - - - - - -

    def _copySessionTypeToForm(self, a_session_type):
        """Copy relevant field from SessionType to SessionTypeResponse."""
        a_form = SessionTypeResponse()
        for field in a_form.all_fields():
            if hasattr(a_session_type, field.name):
                setattr(a_form, field.name, getattr(a_session_type, field.name))
            elif field.name == "websafeKey":
                setattr(a_form, field.name, a_session_type.key.urlsafe())
        a_form.check_initialized()
        return a_form


    def _listSessionTypeObjects(self, request):
        """List session type objects, return SessionTypeListResponse"""
        session_type_list = SessionType.query().fetch()
        return SessionTypeListResponse(
            items=[self._copySessionTypeToForm(a_type) for a_type in session_type_list]
        )


    def _storeSessionTypeObject(self, request):
        """Create conference session type object, return SessionTypeResponse/request."""

        user = self._getUser()
        user_id = getUserId(user)

        # check for type label
        if not request.label:
            raise endpoints.BadRequestException(
                "Conference session type 'label' field required")

        # check for duplicate
        if SessionType.query(SessionType.label == request.label).get():
            raise endpoints.BadRequestException(
                "Duplicate conference session type 'label'")

        # copy request input to  dict
        data = {field.name: getattr(request, field.name) for field in request.all_fields()}

        # create session
        a_session_type = SessionType(**data)
        a_session_type.put()
        return self._copySessionTypeToForm(a_session_type)


    def _destroySessionTypeObject(self, request):
        """destroy conference session type object, return SessionTypeResponse"""

        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        user_id = getUserId(user)

        try:
            a_session_type= ndb.Key(urlsafe=request.websafeSessionTypeKey).get()
        except (TypeError) as e:
            raise endpoints.NotFoundException(
                'Invalid input conference session key string: [%s]' % request.websafeSessionTypeKey)
        except (ProtocolBufferDecodeError) as e:
            raise endpoints.NotFoundException(
                'No conference session found with key: [%s]' % request.websafeSessionTypeKey)
        except Exception as e:
            raise endpoints.NotFoundException('%s: %s' % (e.__class__.__name__, e))

        a_session_type.key.delete()

        return self._copySessionTypeToForm(a_session_type)


    @endpoints.method(message_types.VoidMessage, SessionTypeListResponse,
        path='conference/session/type',
        http_method='GET',
        name='getConferenceSessionTypes')
    def getConferenceSessionTypes(self, request):
        """Get list of conference session types"""
        return self._listSessionTypeObjects(request)


    @endpoints.method(SessionTypeResponse, SessionTypeResponse,
        path='conference/session/type',
        http_method='POST',
        name='createSessionType')
    def createSessionType(self, request):
        """Create conference session"""
        return self._storeSessionTypeObject(request)


    @endpoints.method(SESS_TYPE_POST_REQUEST, SessionTypeResponse,
        path='conference/session/type/{websafeSessionTypeKey}',
        http_method='DELETE',
        name='destroySessionType')
    def destroySessionType(self, request):
        """Destroy conference session type"""
        return self._destroySessionTypeObject(request)


    def _getConferenceSessionsByType(self, request):
        """Get list of sessions by type for the given conference"""
        a_conference = self._getConference(request.websafeConferenceKey)
        a_type = request.typeOfSession
        a_query = Session.query(ancestor=a_conference.key)
        session_list = a_query.filter(Session.typeOfSession == a_type)
        return SessionForms(
            items=[self._copySessionToForm(session) for session in session_list])


    @endpoints.method(SESS_BY_TYPE_REQUEST, SessionForms,
        path='conference/{websafeConferenceKey}/session/type/{typeOfSession}',
        http_method='GET',
        name='getConferenceSessionsByType')
    def getConferenceSessionsByType(self, request):
        """Get list of conference sessions by speaker"""
        return self._getConferenceSessionsByType(request)


# - - - Session wishlist - - - - - - - - - - - - - - - - - - - -

    def _getSessionsInWishlist(self, request):
        """List user wishlist session objects, return SessionForms"""
        profile = self._getProfileFromUser()
        session_key_list = [ndb.Key(urlsafe=session.websafeKey) for session in profile.sessionWishlist]
        wsck = getattr(request, 'websafeConferenceKey')

        if wsck:
            a_conference = self._getConference(wsck)

            session_list = Session.query(
                Session.key.IN(session_key_list),
                ancestor=a_conference.key)
                # ancestor=wsck) # also works
        else:
            session_list = ndb.get_multi(session_key_list)

        return SessionForms(items=[self._copySessionToForm(session) for session in session_list])


    def _addSessionToWishlist(self, request):
        """Add session to user wishlist"""
        # get user profile
        profile = self._getProfileFromUser()
        a_session = self._getSession(request.websafeSessionKey)

        a_session_link = SessionLink(
            name=a_session.name,
            websafeKey=a_session.key.urlsafe()
            )

        if a_session_link in profile.sessionWishlist:
            raise ConflictException(
                "Session already in wishlist")

        profile.sessionWishlist.append(a_session_link)
        profile.put()
        return BooleanMessage(data=True)


    def _removeSessionFromWishlist(self, request):
        """remove session from user wishlist"""
        # get user profile
        profile = self._getProfileFromUser()
        # validate Key
        a_session = self._getSession(request.websafeSessionKey)

        a_session_link = SessionLink(
            name=a_session.name,
            websafeKey=a_session.key.urlsafe()
            )

        if a_session_link not in profile.sessionWishlist:
            raise ConflictException(
                "Session not in wishlist")

        profile.sessionWishlist.remove(a_session_link)
        profile.put()
        return BooleanMessage(data=True)


    @endpoints.method(ConferenceSessionWishlistRequest, SessionForms,
        path='conference/session/wishlist',
        http_method='POST',
        name='getSessionsInWishlist')
    def getSessionsInWishlist(self, request):
        """Get list of sessions in user wishlist"""
        return self._getSessionsInWishlist(request)


    @endpoints.method(SESS_WISH_STORE_REQUEST, BooleanMessage,
        path='conference/session/{websafeSessionKey}/wishlist',
        http_method='POST',
        name='addSessionToWishlist')
    def addSessionToWishlist(self, request):
        """Add given session to user wishlist"""
        return self._addSessionToWishlist(request)

    @endpoints.method(SESS_WISH_DELETE_REQUEST, BooleanMessage,
        path='conference/session/{websafeSessionKey}/wishlist',
        http_method='DELETE',
        name='removeSessionFromWishlist')
    def removeSessionFromWishlist(self, request):
        """Add given session to user wishlist"""
        return self._removeSessionFromWishlist(request)

# - - - Speaker - - - - - - - - - - - - - - - - - - - -

    def _copySpeakerToForm(self, a_speaker):
        """Copy relevant fields from Speaker to SpeakerResponse"""
        a_form = SpeakerResponse()
        for field in a_form.all_fields():
            if hasattr(a_speaker, field.name):
                setattr(a_form, field.name, getattr(a_speaker, field.name))
            elif field.name == "websafeKey":
                setattr(a_form, field.name, a_speaker.key.urlsafe())
        a_form.check_initialized()
        return a_form


    def _getSpeakers(self, request):
        """get list of speakers"""
        speaker_list = Speaker.query().fetch()
        return SpeakerListResponse(
            items=[self._copySpeakerToForm(speaker) for speaker in speaker_list])


    @endpoints.method(message_types.VoidMessage, SpeakerListResponse,
        path='conference/speaker',
        http_method='GET',
        name='getSpeakers')
    def getSpeakers(self, request):
        """Get list of speakers"""
        return self._getSpeakers(request)


    def _getConferenceSpeakers(self, request):
        """List conference speaker objects, return SpeakerListResponse"""
        a_conference = self._getConference(request.websafeConferenceKey)

        # TODO: find a way to reduce 3 gets
        session_key_list = [ndb.Key(urlsafe=websafeKey) for websafeKey in a_conference.sessions]
        session_list = ndb.get_multi(session_key_list)
        speaker_set = set()
        for session in session_list:
            speaker_set.update(session.speakers)
        print "speaker set %s" % speaker_set
        speaker_list = []
        if len(speaker_set):
            speaker_list = Speaker.query(Speaker.name.IN(list(speaker_set))).fetch()
        print "speaker list %s" % speaker_list
        return SpeakerListResponse(
            items=[self._copySpeakerToForm(speaker) for speaker in speaker_list])

    def _storeConferenceSpeaker(self, request):
        """Create a conference speaker profile, return SpeakerResponse"""
        a_conference = self._getConference(request.websafeConferenceKey)
        a_user = self._getUser()

        if not request.name:
            raise endpoints.BadRequestException(
                "Speaker 'name' field' required")

        data = {
            field.name: getattr(request, field.name)
            for field
            in request.all_fields()
            }

        del data['websafeConferenceKey']

        a_speaker = Speaker(**data)
        a_speaker.put()
        return self._copySpeakerToForm(a_speaker)

    def _showConferenceSpeaker(self, request):
        """Show speaker object, return SpeakerResponse"""
        a_speaker = self._getSpeaker(request.websafeSpeakerKey)
        return self._copySpeakerToForm(a_speaker)


    def _updateConferenceSpeaker(self, request):
        """Update speaker object, return SpeakerResponse"""
        pass


    def _destroyConferenceSpeaker(self, request):
        """Destroy speaker object, return SpeakerResponse"""
        pass


    @endpoints.method(CONF_SPEAK_INDEX_REQ, SpeakerListResponse,
        path='conference/{websafeConferenceKey}/speaker',
        http_method='GET',
        name='getConferenceSpeakers')
    def getConferenceSpeakers(self, request):
        """Get list of speakers for the given conference"""
        return self._getConferenceSpeakers(request)


    @endpoints.method(CONF_SPEAK_STORE_REQ, SpeakerResponse,
        path='conference/{websafeConferenceKey}/speaker',
        http_method='POST',
        name='createConferenceSpeaker')
    def createConferenceSpeaker(self, request):
        """Create a speaker profile"""
        return self._storeConferenceSpeaker(request)


    @endpoints.method(CONF_SPEAK_SHOW_REQ, SpeakerResponse,
        path='conference/speaker/{websafeSpeakerKey}',
        http_method='GET',
        name='showConferenceSpeaker')
    def showConferenceSpeaker(self, request):
        """Retrieve a speaker profile"""
        return self._showConferenceSpeaker(request)


    @endpoints.method(CONF_SPEAK_UPDATE_REQ, SpeakerResponse,
        path='conference/speaker/{websafeSpeakerKey}',
        http_method='PUT',
        name='updateConferenceSpeaker')
    def updateConferenceSpeaker(self, request):
        """Update a speaker profile"""
        return self._updateConferenceSpeaker(request)


    @endpoints.method(CONF_SPEAK_DELETE_REQ, SpeakerResponse,
        path='conference/speaker/{websafeSpeakerKey}',
        http_method='DELETE',
        name='destroyConferenceSpeaker')
    def destroyConferenceSpeaker(self, request):
        """Remove a speaker profile"""
        return self._destroyConferenceSpeaker(request)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _addSessionSpeaker(self, request):
        """Add a session and speaker object relationship"""
        speaker_key = ndb.Key(urlsafe=request.websafeSpeakerKey)
        session_key = ndb.Key(urlsafe=request.websafeSessionKey)

        objects = ndb.get_multi([speaker_key, session_key])
        print objects
        return BooleanMessage(data=True)

    @endpoints.method(SESS_SPEAK_STORE_REQ, BooleanMessage,
        path='session/speaker',
        http_method='POST',
        name='addSessionSpeaker')
    def addSessionSpeaker(self, request):
        """Add session speaker relationship"""
        return self._addSessionSpeaker(request)

    @endpoints.method(SESS_SPEAK_DELETE_REQ, BooleanMessage,
        path='session/speaker',
        http_method='DELETE',
        name='removeSessionSpeaker')
    def removeSessionSpeaker(self, request):
        pass


    def _getSessionsBySpeaker(self, request):
        a_speaker = request.speaker
        session_list = Session.query(Session.speakers==a_speaker)
        return SessionForms(
            items=[self._copySessionToForm(session) for session in session_list])


    @endpoints.method(SESS_BY_SPEAKER_REQUEST, SessionForms,
        path='conference/session/speaker/{speaker}',
        http_method='GET',
        name='getSessionsBySpeaker')
    def getSessionsBySpeaker(self, request):
        """Get list of sessions by speaker across all conferences"""
        return self._getSessionsBySpeaker(request)


api = endpoints.api_server([ConferenceApi]) # register API
