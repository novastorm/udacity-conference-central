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

Demo avaiable at: [omgidb-conference-central.appspot.com](http://omgidb-conference-central.appspot.com)

[API Explorer] (http://omgidb-conference-central.appspot.com/_ah/api/explorer)


### Project Tasks

#### Task 1: Add Sessions to a Conference

Conferences present sessions and their associated speakers for attendees to experience.

Sessions are implemented using a Conference as the parent. This method creates a relationship with the parent object and takes advatange of datastores ancestor query capabilities.

The relationship between Session and Speaker is described using a structured property represented by a link object containing minimal information commonly requested with the referencing object. This method preserves the idea of a an object as a document containing pertinent information in addition to  minimizing reads from the datastore.


##### API endpoints

URI | endpoints method | description
--- | ---------------- | -----------
GET conference/{websafeConferenceKey}/session | getConferenceSessions | Given a conference, return all sessions
GET conference/{websafeConferenceKey}/session/type/{typeOfSession} | getConferenceSessionsByType | Given a conference, return all sessions of a specified type (eg lecture, keynote, workshop)
GET session/speakers?name=</br> GET session/speakers?websafeSpeakerKey= | getSessionsBySpeaker | Given a speaker, return all sessions given by this particular speaker, across all conference 
POST conference/{websafeConferenceKey}/session | createSession | open only to the organizer of the conference


##### Session Object

Sessions and ideally be implemented as a child of a conference. A Session also contains a list of 

Property      | Type
------------- | ----------------------------------
name          | string, required
highlights    | string
duration      | integer
typeOfSession | string (default='Not_SPECIFIED')
startTime     | time
endtime       | time
speakers      | structured (SpeakerLink, repeated)


##### Speaker Object

Speakers will have their own description and possibly additional information.

Property    | Type
----------- | ----------------------------------
name        | string, required
description | string
sessions    | structured (SessionLink, repeated)


##### Relationships

Session/Speaker relationships are handled with structured properties in the Session and Speaker objects instead of an intermediate table to reduce datastore queries.

###### SessionLink

The SessionLink object contains the minimum information commonly referenced for the Session object.

Property   | Type
---------- | ----------------------------------
name       | string, required
websafeKey | string, required

###### SpeakerLink

The SpeakerLink object contains the minimum information commonly referenced for the Speaker object.

Property   | Type
---------- | ----------------------------------
name       | string, required
websafeKey | string, required


#### Task 2: Add Sessions to User Wishlist

Users should be able to mark some sessions that they are interested in and retrieve their own current wishlist.

Updated Profile object to include a structure property representing a link object containing minimal information commonly requested with the referencing object. This method preserves the idea of a an object as a document containing pertinent information in addition to  minimizing reads from the datastore. 

##### API endpoints

URI | endpoints method | description
--- | ---------------- | -----------
POST conference/session/{websafeSessionKey}/wishlist | addSessionToWishlist | adds the session to the user's list of sessions they are interested in attending
GET conference/session/wishlist | getSessionsInWishlist | query for all the sessions in a conference that the user is interested in

##### Profile (updates)

sessionWishList property added to store the session wishlist references.

Property   | Type
---------- | ----------------------------------
sessionWishList | structured (SessionLink, repeated)


#### Task 3: Work on indexes and queries

##### Additional Queries
##### Challenge Question

*Let’s say that you don't like workshops and you don't like sessions after 7 pm. How would you handle a query for all non-workshop sessions before 7 pm? What is the problem for implementing this query? What ways to solve it did you think of?*

#### Task 4: Add a Task