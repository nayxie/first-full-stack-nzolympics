from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
import re
from datetime import datetime
import mysql.connector
from mysql.connector import FieldType
import connect

# import string for the capwords() method for eventname
import string

app = Flask(__name__)

dbconn = None
connection = None

def getCursor():
    global dbconn
    global connection
    connection = mysql.connector.connect(user=connect.dbuser, \
    password=connect.dbpass, host=connect.dbhost, \
    database=connect.dbname, autocommit=True)
    dbconn = connection.cursor()
    return dbconn

@app.route("/")
def home():
    return render_template("base.html")

# --- list members ---
# get hold of all members who are in a team
# return memberlist to the teamplate
@app.route("/listmembers")
def listmembers():
    connection = getCursor()
    # inner join members and teams to get hold of team names
    # and select all members who have got a team
    sql = "SELECT m.MemberID, t.TeamName, CONCAT(m.FirstName, ' ', m.LastName), m.City, m.Birthdate \
    FROM members m INNER JOIN teams t ON m.TeamID = t.TeamID;"
    connection.execute(sql)
    memberList = connection.fetchall()
    return render_template("memberlist.html", memberlist = memberList)    

# --- list future and past events ---
# memberId passed in from browser
# get hold of all future and past events, if any, for that memberId
# return the ID, name, and two event lists of the member to the template   
@app.route("/memberevent/<memberId>")
def memberevent(memberId):
    connection = getCursor()
    connection.execute("SELECT CONCAT(FirstName,' ', LastName) FROM members \
                       WHERE memberID = %s;", (memberId,))
    memberName = connection.fetchall()[0][0]

    # fetch a list of tuples with information of all future events 
    # for that memberId
    connection = getCursor()
    sql = "SELECT e.EventName, es.StageDate, es.StageName, es.Location \
    FROM members m \
    RIGHT JOIN events e ON m.TeamID = e.NZTeam \
    RIGHT JOIN event_stage es ON e.EventID = es.EventID \
    LEFT JOIN event_stage_results esr ON es.StageID = esr.StageID \
    WHERE es.StageID NOT IN (SELECT StageID FROM event_stage_results esr) \
    AND m.MemberID = %s;"
    connection.execute(sql, (memberId,))
    futureeventList = connection.fetchall()

    # fetch a list of tuples with information of all past events 
    # for that memberId
    connection = getCursor()
    sql = "SELECT e.EventName, es.StageDate, es.StageName, es.Location, \
        esr.PointsScored, es.PointsToQualify, esr.Position \
        FROM events e \
        RIGHT JOIN event_stage es ON e.EventID = es.EventID \
        RIGHT JOIN event_stage_results esr ON es.StageID = esr.StageID \
        WHERE esr.MemberID = %s;"
    connection.execute(sql, (memberId,))
    pasteventList = connection.fetchall()

    # convert all tuples to lists in pasteventList 
    # to prepare for interpretation of scores and positions 
    # depending on StageName, modify last values accordingly
    pasteventList = [list(item) for item in pasteventList]
    for item in pasteventList:
        if item[2] == "Final":
            if item[-1] == 1:
                item[-1] = "Gold"
            elif item[-1] == 2:
                item[-1] = "Silver"
            elif item[-1] == 3:
                item[-1] = "Bronze"
        else:
            if item[-2] >= item[-3]:
                item[-1] = "Not Qualified"
            else:
                item[-1] = "Qualified"
    
    for item in pasteventList:
        del item[-2]
        del item[-3]

    return render_template("memberevent.html", memberid = memberId, membername = memberName, 
                           futureeventlist = futureeventList, pasteventlist = pasteventList)

# --- list events ---
# get hold of all events 
# return eventlist
@app.route("/listevents")
def listevents():
    connection = getCursor()
    connection.execute("SELECT * FROM events;")
    eventList = connection.fetchall()
    return render_template("eventlist.html", eventlist = eventList)

# --- admin route ---
# home page for all the functions below
# including adding, editing, updating, and reporting 
@app.route("/admin")
def adminhome():
    return render_template("adminbase.html")

# --- search members and events ---
@app.route("/admin/search")
def search():
    return render_template("search.html")

# request the search term from browser, by way of the POST method 
# use f-string and %, the wildcard symbol, for partial matches
# select from both members and events tables
# return results in two seperate lists
@app.route("/admin/search/result", methods=["POST"])
def searchresult():
    searchterm = request.form.get("searchentry")
    likesearchterm = f"%{searchterm}%"
    connection = getCursor()
    connection.execute("SELECT * FROM members WHERE CONCAT(FirstName, ' ', LastName) LIKE %s;", (likesearchterm,))
    memberList = connection.fetchall()
    
    connection = getCursor()
    connection.execute("SELECT * FROM events WHERE EventName LIKE %s;", (likesearchterm,))
    eventList = connection.fetchall()
    return render_template("searchresult.html", memberlist = memberList, eventlist = eventList)

# --- add new members ---
# display all teams for user to choose a specific team 
# to add a member to 
@app.route("/admin/displayteams")
def displayteams():
    connection = getCursor()
    connection.execute("SELECT * FROM teams;")
    teamList = connection.fetchall()
    return render_template("displayteams.html", teamlist = teamList)

# teamId passed in from browser 
# select all information for that teamId
# return teaminfo to the teamplate for diaplay 
# as a reference for the team the user is adding a member to
@app.route("/admin/addmember/<teamId>")
def addmember(teamId):
    connection = getCursor()
    connection.execute("SELECT * FROM teams WHERE TeamID = %s;", (teamId,))
    teamInfo = connection.fetchall()
    return render_template("addmember.html", teaminfo = teamInfo)

# teamId passed in from browser 
# request all form data, by way of the POST method
# insert data into members table
# except MemberID which will be assigned by MySQL, using auto-increment  
# redirect to "/listmembers" function to verify the new member  
@app.route("/admin/addtomembers/<teamId>", methods=["POST"])
def addtomembers(teamId):
    firstname = request.form.get("firstname").title()
    lastname = request.form.get("lastname").title()
    city = request.form.get("city")
    birthdate = request.form.get("birthdate")

    connection = getCursor()
    sql = ("INSERT INTO members (TeamID, FirstName, LastName, City, Birthdate) VALUES (%s, %s, %s, %s, %s)")
    connection.execute(sql, (teamId, firstname, lastname, city, birthdate))
    return redirect("/listmembers")

# --- edit existing members ---
# display all members for user to choose a specific member to edit
@app.route("/admin/displaymembers")
def displaymembers():
    connection = getCursor()
    connection.execute("SELECT * FROM members;")
    memberList = connection.fetchall()
    return render_template("displaymembers.html", memberlist = memberList)

# memberId passed in from browser 
# select all information for that memberId
# return memberinfo to the teamplate for diaplay and editing
@app.route("/admin/editmember/<memberId>")
def editmember(memberId):
    connection = getCursor()
    connection.execute("SELECT * FROM members WHERE MemberID = %s;", (memberId,))
    memberInfo = connection.fetchall()
    return render_template("editmember.html", memberinfo = memberInfo)

# request new information for the chosen member 
# update members table 
# redirect to "/listmembers" for verification
@app.route("/admin/updatemember/<memberId>", methods=["POST"])
def updatemember(memberId):
    firstname = request.form.get("firstname").title()
    lastname = request.form.get("lastname").title()
    city = request.form.get("city")
    birthdate = request.form.get("birthdate")

    connection = getCursor()
    connection.execute("UPDATE members SET FirstName = %s, LastName = %s, City = %s, Birthdate = %s WHERE MemberID = %s;",
                   (firstname, lastname, city, birthdate, memberId))
    return redirect("/listmembers")
    
# --- add events ---
# select all TeamID, put them in a list, 
# and pass it to the template for display and for user to choose from 
@app.route("/admin/addevent")
def addevent():
    connection = getCursor()
    connection.execute("SELECT TeamID FROM teams;")
    teamidList = connection.fetchall()
    return render_template("addevent.html", teamidlist = teamidList)

# request form data, through POST
# insert new event data into events table 
@app.route("/admin/addtoevents", methods=["POST"])
def addtoevents():
    eventname = string.capwords(request.form.get("eventname"))
    sport = request.form.get("sport").title()
    nzteam = request.form.get("nzteam")
    if nzteam == "none":
        nzteam = None

    connection = getCursor()
    sql = ("INSERT INTO events (EventName, Sport, NZTeam) VALUES (%s, %s, %s);")
    connection.execute(sql, (eventname, sport, nzteam))
    return redirect("/listevents")

# --- add new stages ---
# select all events for user to choose from and to add a stage to
@app.route("/admin/displayevents")
def displayevents():
    connection = getCursor()
    connection.execute("SELECT * FROM events;")
    eventList = connection.fetchall()
    return render_template("displayevents.html", eventlist = eventList)

# get hold of all information for the chosen event 
# as a reference for user to add a stage
@app.route("/admin/addstage/<eventId>")
def addstage(eventId):
    connection = getCursor()
    connection.execute("SELECT * FROM events WHERE EventID = %s;", (eventId,))
    eventInfo = connection.fetchall()
    return render_template("addstage.html", eventinfo = eventInfo)

# request form data 
# insert new data to event_stage table
# select all information of event_stage table for display and verification
@app.route("/admin/addtostages/<eventId>", methods=["POST"])
def addtostages(eventId):
    stagename = request.form.get("stagename")
    location = request.form.get("location")
    stagedate = request.form.get("stagedate")
    pointstoqualify = request.form.get("pointstoqualify")

    # depending on the stagename, as selected by user and passed in from browser
    # value for the qualifying variable will be determined 
    # and value for pointstoqualify will either be kept as is, or set to None 
    if stagename == "Heat 1" or stagename == "Qualification":
        qualifying = 1
    elif stagename == "Final":
        qualifying = 0
        pointstoqualify = None
    
    connection = getCursor()
    sql = "INSERT INTO event_stage (StageName, EventID, Location, \
        StageDate, Qualifying, PointsToQualify) VALUES (%s, %s, %s, %s, %s, %s);"
    connection.execute(sql, (stagename, eventId, location, stagedate, \
                             qualifying, pointstoqualify))
    
    connection = getCursor()
    connection.execute("SELECT * FROM event_stage;")
    stageList = connection.fetchall()

    return render_template("displaystages.html", stagelist = stageList)

# --- add scores and positions ---
# the following two routes get hold of all information for members and stages respectively
# return them as lists for display and for user to choose 
@app.route("/admin/displaymembers2")
def displaymembers2():
    connection = getCursor()
    connection.execute("SELECT * FROM members;")
    memberList = connection.fetchall()
    return render_template("displaymembers2.html", memberlist = memberList)

@app.route("/admin/displaystages2/<memberId>")
def displaystages2(memberId):
    connection = getCursor()
    connection.execute("SELECT * FROM event_stage;")
    stageList = connection.fetchall()
    return render_template("displaystages2.html", stagelist = stageList, memberid = memberId)

# stageId and memberId passed in from browser 
# select all id-related information for display
@app.route("/admin/addresult/<stageId>/<memberId>")
def addresult(stageId, memberId):
    connection = getCursor()
    connection.execute("SELECT * FROM members WHERE MemberID = %s;", (memberId,))
    memberInfo = connection.fetchall()

    connection = getCursor()
    connection.execute("SELECT * FROM event_stage WHERE StageID = %s;", (stageId,))
    stageInfo = connection.fetchall()

    return render_template("addresult.html", stageinfo = stageInfo, memberinfo = memberInfo)

# request form data through POST
# insert new data into results table 
# select all result information for display and verification
@app.route("/admin/addtoresults/<stageId>/<memberId>", methods=["POST"])
def addtoresults(stageId, memberId):
    pointsscored = request.form.get("pointsscored")
    position = request.form.get("position")
    if position == "none":
        position = None

    connection = getCursor()
    sql = "INSERT INTO event_stage_results (StageID, MemberID, PointsScored, Position) \
        VALUES (%s, %s, %s, %s);"
    connection.execute(sql, (stageId, memberId, pointsscored, position))

    connection = getCursor()
    connection.execute("SELECT * FROM event_stage_results;")
    resultList = connection.fetchall()

    return render_template("displayresults.html", resultlist = resultList)
    
# --- medal report ---
# get hold of total numbers of gold, silver and bronze
# and the winner lists 
@app.route("/admin/reportmedals")
def reportmedals():

    connection = getCursor()
    connection.execute("SELECT COUNT(Position) FROM event_stage_results WHERE Position = 1;")
    goldNum = connection.fetchall()[0][0]

    connection = getCursor()
    connection.execute("SELECT COUNT(Position) FROM event_stage_results WHERE Position = 2;")
    silverNum = connection.fetchall()[0][0]

    connection = getCursor()
    connection.execute("SELECT COUNT(Position) FROM event_stage_results WHERE Position = 3;")
    bronzeNum = connection.fetchall()[0][0]

    connection = getCursor()
    connection.execute("SELECT CONCAT(m.FirstName, ' ', m.LastName), COUNT(esr.Position) \
        FROM members m INNER JOIN event_stage_results esr \
        ON m.MemberID = esr.MemberID \
        WHERE Position = 1 \
        GROUP BY CONCAT(m.FirstName, ' ', m.LastName);")
    goldwinnerList = connection.fetchall()

    connection = getCursor()
    connection.execute("SELECT CONCAT(m.FirstName, ' ', m.LastName), COUNT(esr.Position) \
        FROM members m INNER JOIN event_stage_results esr \
        ON m.MemberID = esr.MemberID \
        WHERE Position = 2 \
        GROUP BY CONCAT(m.FirstName, ' ', m.LastName);")
    silverwinnerList = connection.fetchall()

    connection = getCursor()
    connection.execute("SELECT CONCAT(m.FirstName, ' ', m.LastName), COUNT(esr.Position) \
        FROM members m INNER JOIN event_stage_results esr \
        ON m.MemberID = esr.MemberID \
        WHERE Position = 3 \
        GROUP BY CONCAT(m.FirstName, ' ', m.LastName);")
    bronzewinnerList = connection.fetchall()

    return render_template("reportmedals.html", goldnum = goldNum, \
        silvernum = silverNum, bronzenum = bronzeNum, goldwinnerlist = goldwinnerList, \
        silverwinnerlist = silverwinnerList, bronzewinnerlist = bronzewinnerList)

# --- team report --- 
@app.route("/admin/reportteams")
def reportteams():
   
    # get hold of total number of teams:
    connection = getCursor()
    connection.execute("SELECT COUNT(TeamID) FROM teams;")
    teamNum = connection.fetchall()[0][0]

    # get hold of teamlist, containing number of members in each team 
    connection = getCursor()
    sql = "SELECT t.TeamID, t.TeamName, COUNT(m.TeamID)\
            FROM teams t LEFT JOIN members m \
            ON t.TeamID = m.TeamID \
            GROUP BY t.TeamID, t.TeamName;"
    connection.execute(sql)
    teamList = connection.fetchall()

    # get hold of team id list
    # loop through it to get hold of each team id  
    # use each team id to get hold of members of each team
    connection = getCursor()
    connection.execute("SELECT TeamID FROM teams;")
    teamidList = connection.fetchall()

    teamMembers= []
    for idlist in teamidList:
        for id in idlist:
            connection = getCursor()
            connection.execute("SELECT FirstName, LastName FROM members WHERE TeamID = %s;", (id,))
            teamMembers.append(connection.fetchall())
    
    # re-order members in each team, by last names then first names 
    for team in teamMembers:
        team.sort(key=lambda name: name[-1][0])

    # concatenate first and last names into one string 
    # put all members of the same team into one list
    # reassign to teamMembers to become a list of lists of all teams   
    teamMembers = [[f"{name[0]} {name[1]}" for name in team] for team in teamMembers]

    return render_template("reportteams.html", teamnum = teamNum, teamlist = teamList, teammembers = teamMembers)
