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

@app.route("/listmembers")
def listmembers():
    connection = getCursor()
    # use join to get hold of team names
    sql = "SELECT m.MemberID, t.TeamName, m.FirstName, m.LastName, m.City, m.Birthdate \
    FROM members m LEFT JOIN teams t ON m.TeamID = t.TeamID;"
    connection.execute(sql)
    memberList = connection.fetchall()
    return render_template("memberlist.html", memberlist = memberList)    

@app.route("/memberevent/<memberId>")
def memberevent(memberId):
    connection = getCursor()
    connection.execute("SELECT CONCAT(FirstName,' ', LastName) FROM members \
                       WHERE memberID = %s;", (memberId,))
    memberName = connection.fetchall()[0][0]

    # fetch a list of tuples with information of all future events 
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
    connection = getCursor()
    sql = "SELECT e.EventName, es.StageDate, es.StageName, es.Location, \
        esr.PointsScored, es.PointsToQualify, esr.Position \
        FROM events e \
        RIGHT JOIN event_stage es ON e.EventID = es.EventID \
        RIGHT JOIN event_stage_results esr ON es.StageID = esr.StageID \
        WHERE esr.MemberID = %s;"
    connection.execute(sql, (memberId,))
    pasteventList = connection.fetchall()

    # convert all tuples to lists in pasteventList to prepare for interpretation of scores and positions 
    # Depending on StageName, modify last values accordingly
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
    
# line 84, in memberevent
#     if item[-2] >= item[-3]:
#        ^^^^^^^^^^^^^^^^^^^^
# TypeError: '>=' not supported between instances of 'NoneType' and 'float'

    for item in pasteventList:
        del item[-2]
        del item[-3]

    return render_template("memberevent.html", memberid = memberId, membername = memberName, 
                           futureeventlist = futureeventList, pasteventlist = pasteventList)


@app.route("/listevents")
def listevents():
    connection = getCursor()
    connection.execute("SELECT * FROM events;")
    eventList = connection.fetchall()
    return render_template("eventlist.html", eventlist = eventList)

# add "/admin" route, share the same template as "base.html"
@app.route("/admin")
def adminhome():
    return render_template("adminbase.html")

@app.route("/admin/search")
def search():
    return render_template("search.html")

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




# Add new members 

@app.route("/admin/displayteams")
def displayteams():
    connection = getCursor()
    connection.execute("SELECT * FROM teams;")
    teamList = connection.fetchall()
    return render_template("displayteams.html", teamlist = teamList)

@app.route("/admin/addmember/<teamId>")
def addmember(teamId):
    connection = getCursor()
    connection.execute("SELECT * FROM teams WHERE TeamID = %s;", (teamId,))
    teamInfo = connection.fetchall()
    return render_template("addmember.html", teaminfo = teamInfo)

@app.route("/admin/addtomembers/<teamId>", methods=["POST"])
def addtomembers(teamId):
    firstname = request.form.get("firstname").title()
    lastname = request.form.get("lastname").title()
    city = request.form.get("city")
    birthdate = request.form.get("birthdate")

    # - use re to validate user input

    connection = getCursor()
    sql = ("INSERT INTO members (TeamID, FirstName, LastName, City, Birthdate) VALUES (%s, %s, %s, %s, %s)")
    connection.execute(sql, (teamId, firstname, lastname, city, birthdate))
    return redirect("/listmembers")

# and edit the details of existing members

@app.route("/admin/displaymembers")
def displaymembers():
    connection = getCursor()
    connection.execute("SELECT * FROM members;")
    memberList = connection.fetchall()
    return render_template("displaymembers.html", memberlist = memberList)

@app.route("/admin/editmember/<memberId>")
def editmember(memberId):
    connection = getCursor()
    connection.execute("SELECT * FROM members WHERE MemberID = %s;", (memberId,))
    memberInfo = connection.fetchall()
    return render_template("editmember.html", memberinfo = memberInfo)

@app.route("/admin/updatemember/<memberId>", methods=["POST"])
def updatemember(memberId):
    firstname = request.form.get("firstname").title()
    lastname = request.form.get("lastname").title()
    city = request.form.get("city")
    birthdate = request.form.get("birthdate")

    # - use re to validate user input

    connection = getCursor()
    connection.execute("UPDATE members SET FirstName = %s, LastName = %s, City = %s, Birthdate = %s WHERE MemberID = %s;",
                   (firstname, lastname, city, birthdate, memberId))
    return redirect("/listmembers")
    
# add events 

@app.route("/admin/addevent")
def addevent():
    connection = getCursor()
    connection.execute("SELECT TeamID FROM teams;")
    teamidList = connection.fetchall()
    return render_template("addevent.html", teamidlist = teamidList)


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



# add new stages 

@app.route("/admin/displayevents")
def displayevents():
    connection = getCursor()
    connection.execute("SELECT * FROM events;")
    eventList = connection.fetchall()
    return render_template("displayevents.html", eventlist = eventList)

@app.route("/admin/addstage/<eventId>")
def addstage(eventId):
    connection = getCursor()
    connection.execute("SELECT * FROM events WHERE EventID = %s;", (eventId,))
    eventInfo = connection.fetchall()
    return render_template("addstage.html", eventinfo = eventInfo)

@app.route("/admin/addtostages/<eventId>", methods=["POST"])
def addtostages(eventId):

    stagename = request.form.get("stagename")
    location = request.form.get("location")
    stagedate = request.form.get("stagedate")
    pointstoqualify = request.form.get("pointstoqualify")
    if pointstoqualify == "":
        pointstoqualify = None

    if stagename == "Heat 1" or stagename == "Qualification":
        qualifying = 1 
    elif stagename == "Final":
        qualifying = 0
    
    connection = getCursor()
    sql = "INSERT INTO event_stage (StageName, EventID, Location, \
        StageDate, Qualifying, PointsToQualify) VALUES (%s, %s, %s, %s, %s, %s);"
    connection.execute(sql, (stagename, eventId, location, stagedate, \
                             qualifying, pointstoqualify))
    
    connection = getCursor()
    connection.execute("SELECT * FROM event_stage;")
    stageList = connection.fetchall()

    return render_template("displaystages.html", stagelist = stageList)



# Add scores for an event stage and position for a non-qualifying event stage



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


@app.route("/admin/addresult/<stageId>/<memberId>")
def addresult(stageId, memberId):
    connection = getCursor()
    connection.execute("SELECT * FROM members WHERE MemberID = %s;", (memberId,))
    memberInfo = connection.fetchall()

    connection = getCursor()
    connection.execute("SELECT * FROM event_stage WHERE StageID = %s;", (stageId,))
    stageInfo = connection.fetchall()

    return render_template("addresult.html", stageinfo = stageInfo, memberinfo = memberInfo)

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
    
