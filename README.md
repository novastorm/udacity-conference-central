Conference Manangement
======================

Cloud application to managing conferences, available sessions and guest
speakers.

Features:

  - User profile management
  - Secure 3rd pary OAuth 2.0 user authentication (via Google)
  - Conference management
  - Session management
  - Speaker management
  - User session wish list

View the demo at: [omgidb-conference-central.appspot.com](http://omgidb-conference-central.appspot.com)

Explore the API endpoints with the [API Explorer] (http://omgidb-conference-central.appspot.com/_ah/api/explorer)


### Project Tasks

#### Task 1: Add Sessions to a Conference

Sessions<sup>[1](#SessionObject)</sup> are inherently tied to a conference and thus are created  with a conference as it's parent. This also has the added benefit of allowing session queries by conference.

A speaker may speak at multiple sessions. To forgo having to enter speaker details for every session, a separate Speaker<sup>[2](#SpeakerObject)</sup> object is created.

The relationship between Sessions and Speakers is accomplished with intermediate relationships<sup>[3](#Relationships)</sup>. SpeakerLink<sup>[4](#SpeakerLinkObject)</sup> provides a speaker reference and SessionLink<sup>[5](#SessionLinkObject)</sup> provides a session reference.

This architecture is choosen to facilitate a document-oriented paradigm, whereby the document contains related data in a single record. The links also contain a reference to the link object for quick reference.

#### Task 2: Add Sessions to User Wishlist

The Profile object is updated to include a structure property representing a SessionLink object containing minimal information commonly requested with the referencing object. This method preserves the idea of a an object as a document containing pertinent information in addition to  minimizing reads from the datastore. 


#### Task 3: Work on indexes and queries

Datastore only allows inequality queries on one property. Working around this required an approach combining features available with a Datastore query augmented with additional application code.

The approach used here is to parse the query filters and assemble as much as possible into a datastore query then programmatically loop through the remaining filters within the application code. This lead to the generic query feature design handling a variety of query input filters.

In addition to the challenge of querying multiple properties using datastore, further clarification is required for the question of handling "non-workshop sessions before 7pm". "Non-workshops" is trivial, analyzing "sessions before 7pm" brings requires clarification of these questions:

1. Sessions starting before 7:00 PM
2. Sessions ending before 7:00 PM

1 - can be implemented without additional object changes.

2 - requires adding a calculated end time to the Session object.

##### Additional Endpoints

- RSS feed

	Responds with the 10 most recently added or updated sessions
	for a given conference.

- queryConferenceSessions

	Query Conference sessions with the following options:
	
	- 'TYPE': 'typeOfSession',
	- 'DATE': 'date',
	- 'START': 'startTime',
	- 'DURATION': 'duration',
	- 'END': 'endTime',


#### Task 4: Add a Task

This task is accomplished by modifying the addSessionSpeaker feature. When adding a speaker to a session the session parent and speaker are passed to 


### Endpoints

URI | endpoints method | description
--- | ---------------- | -----------
GET conference/{websafeConferenceKey}/session | getConferenceSessions | Given a conference, return all sessions
GET conference/{websafeConferenceKey}/session/type/{typeOfSession} | getConferenceSessionsByType | Given a conference, return all sessions of a specified type (eg lecture, keynote, workshop)
GET session/speakers?name=</br> GET session/speakers?websafeSpeakerKey= | getSessionsBySpeaker | Given a speaker, return all sessions given by this particular speaker, across all conference 
POST conference/{websafeConferenceKey}/session | createSession | open only to the organizer of the conference
POST conference/session/{websafeSessionKey}/wishlist | addSessionToWishlist | adds the session to the user's list of sessions they are interested in attending
GET conference/session/wishlist | getSessionsInWishlist | query for all the sessions in a conference that the user is interested in


### Objects


<a name="SessionObject"></a>
##### Session Object
Implemented as a child of a conference.

Session.speakers is a list of SpeakerLink items containing  commonly queried data with the Session object in addition to a reference to the Speaker

Property      | Type
------------- | ----------------------------------
name          | string, required
highlights    | string
duration      | integer
typeOfSession | string (default='Not_SPECIFIED')
startTime     | time
endtime       | time
speakers      | structured (SpeakerLink, repeated)


<a name="SpeakerObject"></a>
##### Speaker Object

Speakers will have their own description and possibly additional information.

Speaker.sessions is a list of SessionLink items containing  commonly queried data with the Spekaer object in addition to a reference to the Session

Property    | Type
----------- | ----------------------------------
name        | string, required
description | string
sessions    | structured (SessionLink, repeated)


<a name="Relationships"></a>
##### Relationships

Session/Speaker relationships are handled with structured properties in the Session and Speaker objects instead of an intermediate table to reduce datastore queries.

<a name="SessionLinkObject"></a>
###### SessionLink

The SessionLink object contains the minimum information commonly referenced for the Session object.

Property   | Type
---------- | ----------------------------------
name       | string, required
websafeKey | string, required

<a name="SpeakerLinkObject"></a>
###### SpeakerLink

The SpeakerLink object contains the minimum information commonly referenced for the Speaker object.

Property   | Type
---------- | ----------------------------------
name       | string, required
websafeKey | string, required
