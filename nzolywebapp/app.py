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
    # use inner join to get hold of team names
    sql = "SELECT m.MemberID, t.TeamName, m.FirstName, m.LastName, m.City, m.Birthdate \
    FROM members m INNER JOIN teams t ON m.TeamID = t.TeamID;"
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

@app.route("/admin/addMandE")
def addMandE():
    return render_template("addMandE.html")

@app.route("/admin/addtoMandE", methods=["POST"])
def addtoMandE():
    firstname = request.form.get("firstname").title()
    lastname = request.form.get("lastname").title()
    city = request.form.get("city")
    birthdate = request.form.get("birthdate")
    eventname = string.capwords(request.form.get("eventname"))
    sport = request.form.get("sport").title()


    # - use re to validate user input
    
    # create new entry in the teams table 
    # name of sport is passed to TeamName
    # get hold of the auto-incremented TeamID
    connection = getCursor()
    connection.execute("INSERT INTO teams (TeamName) VALUES (%s)", (sport,))
    connection.execute("SELECT TeamID FROM teams")
    teamid = connection.fetchall()[-1][0]
    
    # create new entry in the events table
    connection = getCursor()
    connection.execute("INSERT INTO events (EventName, Sport, NZTeam) VALUES (%s, %s, %s)", (eventname, sport, teamid))

    # create new entry in the members table
    connection = getCursor()
    sql = ("INSERT INTO members (TeamID, FirstName, LastName, City, Birthdate) VALUES (%s, %s, %s, %s, %s)")
    connection.execute(sql, (teamid, firstname, lastname, city, birthdate))

    # redict to listmembers, where users can see the updated member information
    # and because the page is based on base.html, there's link to list events as well 
    # where users can click and see the updated event information 

    return redirect("/listmembers")


# and edit the details of existing members.
# return page where all member data is shown, with memberID linked 
# to another page where user can edit all information of the chosen 
# member, similar template to memberlist  

@app.route("/admin/displayMandE")
def displayMandE():
    connection = getCursor()
    connection.execute("SELECT m.MemberID, m.FirstName, m.LastName, m.City, m.Birthdate, \
                       e.EventName, e.Sport FROM members m \
                       LEFT JOIN events e ON m.TeamID = e.NZTeam;")
    memberList = connection.fetchall()
    return render_template("displayMandE.html", memberlist = memberList)

@app.route("/admin/editMandE/<memberId>")    
def editMandE(memberId):
    connection = getCursor()
    connection.execute("SELECT m.MemberID, m.FirstName, m.LastName, m.City, m.Birthdate, \
                       e.EventName, e.Sport FROM members m \
                       LEFT JOIN events e ON m.TeamID = e.NZTeam \
                       WHERE memberID = %s;", (memberId,))
    memberInfo = connection.fetchall()
    return render_template("editMandE.html", memberinfo = memberInfo) 




@app.route("/admin/updateMandE", methods=["POST"])
def updateMandE():
    memberid = request.form.get("memberid")
    firstname = request.form.get("firstname").title()
    lastname = request.form.get("lastname").title()
    city = request.form.get("city")
    birthdate = request.form.get("birthdate")
    eventname = string.capwords(request.form.get("eventname"))
    sport = request.form.get("sport").title()

    connection = getCursor()
    connection.execute("UPDATE members SET FirstName = %s, LastName = %s, City = %s, Birthdate = %s WHERE MemberID = %s;",
                   (firstname, lastname, city, birthdate, memberid))
    
    connection = getCursor()
    connection.execute("SELECT TeamID FROM members WHERE MemberID = %s;", (memberid,))
    teamid = connection.fetchall()[0][0]

    connection = getCursor()
    connection.execute("UPDATE teams SET TeamName = %s WHERE TeamID = %s;",(sport, teamid))

    connection = getCursor()
    connection.execute("UPDATE events SET EventName = %s, Sport = %s WHERE NZTeam = %s;", (eventname, sport, teamid))

    # - use re to validate user input
    


    # redict to listmembers, where users can see the updated member information
    # and because the page is based on base.html, there's link to list events as well 
    # where users can click and see the updated event information 

    return redirect("/listmembers")


# Add new event_stages.

@app.route("/admin/displayEandS")
def displayEandS():
    connection = getCursor()
    connection.execute("SELECT * FROM events;")
    eventList = connection.fetchall()

    connection = getCursor()
    connection.execute("SELECT * FROM event_stage;")
    stageList = connection.fetchall()

    return render_template("displayEandS.html", eventlist = eventList, stagelist = stageList)

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

    # print(f"EventID is {eventId}")
    # print(f"{stagename}, {location}, {stagedate}, {pointstoqualify}")

    if stagename == "Heat 1" or stagename == "Qualification":
        qualifying = 1 
    elif stagename == "Final":
        qualifying = 0
    
    connection = getCursor()
    sql = "INSERT INTO event_stage (StageName, EventID, Location, \
        StageDate, Qualifying, PointsToQualify) VALUES (%s, %s, %s, %s, %s, %s);"
    connection.execute(sql, (stagename, eventId, location, stagedate, qualifying, pointstoqualify))

    return redirect("/admin/displayEandS")


# Add scores for an event stage and position for a non-qualifying event stage

@app.route("/admin/displaySandR")
def displaySandR():
    connection = getCursor()
    connection.execute("SELECT * FROM event_stage;")
    stageList = connection.fetchall()

    connection = getCursor()
    sql = "SELECT es.StageID, es.StageName, es.Location, es.StageDate, \
        es.PointsToQualify, esr.PointsScored, esr.Position \
        FROM event_stage es \
        LEFT JOIN event_stage_results esr ON es.StageID = esr.StageID;"
    connection.execute(sql)
    stageList = connection.fetchall()
    return render_template("displaySandR.html", stagelist = stageList)


@app.route("/admin/addresult/<stageId>")
def displaySandR(stageId):
    connection = getCursor()
    connection.execute("SELECT * FROM event_stage WHERE StageID = %s;", (stageId,))
    stageInfo = connection.fetchall()
    return render_template("addresult.html", stageinfo = stageInfo)

@app.route("/admin/addtoresults/<stageId>", methods=["POST"])
def addtoresults(stageId):
    pointsscored = request.form.get("pointsscored")
    position = request.form.get("position")
    if position == "1":
        position = 1
    elif position == "2":
        position = 2 
    elif position == "3":
        position = 3
    elif position == "None":
        position = None


    # how do you get hold of MemberID



    # connection = getCursor()
    # sql = "INSERT INTO event_stage_results (StageID, EventID, Location, \
    #     StageDate, Qualifying, PointsToQualify) VALUES (%s, %s, %s, %s, %s, %s);"
    # connection.execute(sql, (stagename, eventId, location, stagedate, qualifying, pointstoqualify))

    # return redirect("/admin/displayEandS")
    

