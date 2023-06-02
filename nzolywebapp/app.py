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
  # memberid, membername, futureevents, pastevents
    # memberId = request.args.get('memberID')
    connection = getCursor()
    connection.execute("SELECT CONCAT(FirstName,' ', LastName) FROM members \
                       WHERE memberID = %s;", (memberId,))
    memberName = connection.fetchall()[0][0]

    # fetch a list of tuples with information of all future events 
    connection = getCursor()
    sql = "SELECT e.EventName, es.StageDate, es.StageName, es.Location \
    FROM events e \
    RIGHT JOIN event_stage es ON e.EventID = es.EventID \
    LEFT JOIN event_stage_results esr ON es.StageID = esr.StageID \
    WHERE es.StageID NOT IN (SELECT StageID FROM event_stage_results esr) \
    AND esr.MemberID = %s;"
    connection.execute(sql, (memberId,))
    futureeventList = connection.fetchall()
    # print(memberId)
    # print(memberName)
    # print(futureeventList)

    # fetch a list of tuples with information of all past events 
    # esr.PointsScored yet to be interpreted
    connection = getCursor()
    sql = "SELECT e.EventName, es.StageDate, es.StageName, es.Location, esr.PointsScored \
    FROM events e \
    RIGHT JOIN event_stage es ON e.EventID = es.EventID \
    RIGHT JOIN event_stage_results esr ON es.StageID = esr.StageID \
    WHERE esr.MemberID = %s;"
    connection.execute(sql, (memberId,))
    pasteventList = connection.fetchall()
    # print(memberId)
    # print(memberName)
    # print(pasteventList)

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

@app.route("/admin/addmembersandevents")
def addmembersandevents():
    return render_template("addmembersandevents.html")

@app.route("/admin/updatemembersandevents", methods=["POST"])
def updatemembersandevents():
    firstname = request.form.get("firstname")
    lastname = request.form.get("lastname")
    city = request.form.get("city")
    birthdate = request.form.get("birthdate")
    eventname = request.form.get("eventname")
    sport = request.form.get("sport")

    # - assign MemberID, TeamID to new member
    # - insert new member data into members table
    # - return memberlist.html
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
@app.route("/admin/edit")
def edit():

    # return page where all member data is shown, with memberID linked 
    # to another page where user can edit all information of the chosen 
    # member, similar template to memberlist  


#   page where user can edit all information of the chosen member, appended
#   with memberID from edit page 
#   similar template to addmembersandevents
#   return redirect("/listmembers")
@app.route("/admin/editmembers")
def editmembers():






# Add new event_stages.
# Add scores for an event stage and position for a non-qualifying event stage.