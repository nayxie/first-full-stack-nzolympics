# 636final-nzoly

# NZ Winter Olympics Project Report
## Assumptions 
## Routes and functions
## Changes
### database changes 
### app changes 


eventlist.html is used to display a list of events,
and is sharing the same template as memberlist.html 
for the display

based on the data model, each stage can have multiple results but needs to have at least one result, and reslt (pointsScored) cannot be null, so the programme can only record and display past events. to be able to work with upcoming events, result field (pointsScored) can be set as null so that all events, past or future, can be recorded and displayed

the add members and add events are combined, bnecause in order to create a new entry for members, we need to know the teamID first, which is auto-incremented in the teams table, and the teamname field in the teams table is equal to sport, which is a field in the evnts table, as a result, the form is contructed in a way for users to provide not only the member info, but the event they would participate in as well, so that all the data would be collected as a package to fit in with the schema/ data model. 

there is no future events in the db based on the premise, which we could assume all the dates in the db are in the past, so we coult set a current date any date after that (??)
the current date should be a condition mechenism to determine if an event is added and its date is before the date, there should be stages and results recorded; and if event happened after the date, no result should be recorded 