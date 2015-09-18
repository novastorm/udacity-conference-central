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

#### Task 1 - Conference Sessions

Conferences present sessions and their associated speakers for attendees to experience.

Sessions are implemented using a Conference as the parent. This method creates a relationship with the parent object and takes advatange of datastores ancestor query capabilities.

The relationship between Session and Speaker is described using a structured property represented by a link object containing minimal information commonly requested with the referencing object. This method preserves the idea of a an object as a document containing pertinent information in addition to  minimizing reads from the datastore.

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


#### Relationships

Session/Speaker relationships are handled with structured properties in the Session and Speaker objects instead of an intermediate table to reduce datastore queries.

##### SessionLink

The SessionLink object contains the minimum information commonly referenced for the Session object.

Property   | Type
---------- | ----------------------------------
name       | string, required
websafeKey | string, required



##### SpeakerLink

The SpeakerLink object contains the minimum information commonly referenced for the Speaker object.

Property   | Type
---------- | ----------------------------------
name       | string, required
websafeKey | string, required
