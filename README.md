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
