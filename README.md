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
