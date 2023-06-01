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

@app.route("/memberevent")
def memberevent():
  # memberid, membername, futureevents, pastevents
    memberid = request.args.get('memberID')
    connection = getCursor()
    connection.execute("SELECT CONCAT(FirstName,' ', LastName) FROM members \
                       WHERE memberID = %s;", (memberid,))
    membername = connection.fetchall()[0][0]

    # fetch a list of tuples with event name(s) of all future events 
    connection = getCursor()
    sql = "SELECT EventName FROM events e \
    RIGHT JOIN event_stage es ON e.EventID = es.EventID \
    LEFT JOIN event_stage_results esr ON es.StageID = esr.StageID \
    WHERE es.StageID NOT IN (SELECT StageID FROM event_stage_results esr) \
    AND esr.MemberID = %s;"
    connection.execute(sql, (memberid,))
    futureevents = connection.fetchall()

    print(memberid)
    print(membername)
    print(futureevents)




    # fetch a list of tuples with event name(s) of all past events 
    connection = getCursor()
    sql = "SELECT EventName FROM events e \
    RIGHT JOIN event_stage es ON e.EventID = es.EventID \
    RIGHT JOIN event_stage_results esr ON es.StageID = esr.StageID \
    WHERE esr.MemberID = %s;"
    connection.execute(sql, (memberid,))
    pastevents = connection.fetchall()

    print(memberid)
    print(membername)
    print(pastevents)

    


    
    return render_template("base.html")


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

@app.route("/search")
def search():
    return render_template("search.html")

@app.route("/search/result", methods=["POST"])
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



# past events: 

# SELECT CONCAT(m.FirstName,' ',m.LastName) AS Name, e.EventName, es.StageDate, es.StageName, es.Location, 
# esr.PointsScored
# FROM event_stage_results esr 
# LEFT JOIN members m ON esr.MemberID = m.MemberID
# LEFT JOIN event_stage es ON esr.StageID = es.StageID
# LEFT JOIN events e ON es.EventID = e.EventID;

# interpret esr.PointsScored

# if es.Qualifying == 1 AND esr.PointsScored >= es.PointsToQualify
# show "Q"
# else
# show "NQ"

# elif es.Qualifying == 0
#   if esr.Position == 1 
#     show "Gold"
#   elif esr.Position == 2 
#     show "Silver"
#    elif esr.Position == 3 
#     show "Bronze"  

# upcoming events:

# SELECT es.StageDate, es.StageName, es.Location 
# FROM event_stage es 
# LEFT JOIN event_stage_results esr ON es.StageID = esr.StageID
# WHERE es.StageID NOT IN (SELECT StageID FROM event_stage_results)
# LEFT JOIN members m ON m.MemberID = esr.MemberID;


# ("SELECT es.StageDate, es.StageName, es.Location 
# FROM event_stage es 
# LEFT JOIN event_stage_results esr ON es.StageID = esr.StageID
# LEFT JOIN members m ON m.MemberID = esr.MemberID
# WHERE es.StageID NOT IN (SELECT StageID FROM event_stage_results)
# AND WHERE esr.MemberID = %s;"), (memberid,)) 
