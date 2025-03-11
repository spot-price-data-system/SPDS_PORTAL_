from flask import Flask, render_template, request, redirect, send_file, make_response

from login import session_code, valid_session
from db_conv import excel
from params import get_data,make_request,email_str

import requests
import os

PSPDS_url = "http://4.147.152.32"

app = Flask(__name__,static_url_path="/static")

#Default url, login page
@app.route('/')
def index():
  return(render_template("login.html"))

#login submission, redirects to homepage
@app.route('/login', methods=["GET", "POST"])
def login():
  if request.method == "POST":
    password = request.form.get("password")  #get form data
    if password == "cumberland_power":  #correct password
      resp = make_response(redirect("/home"))
      resp.set_cookie("SessionID",session_code(app.root_path))
    else:
       resp = make_response(redirect("/"))
  else:
     resp = make_response(redirect("/"))
  return(resp)

def download_plot(plot):
  req = requests.get(PSPDS_url+"/get_plot",params={"password":"SPDS_connect","plot":plot})  
  with open("static/images/"+plot,"wb") as figure:
    figure.write(req.content)

#homepage
@app.route('/home')
def home():
  session = request.cookies.get("SessionID")  #get session code param
  file_exists = os.path.exists(os.path.join(app.root_path,"current_session.txt"))
  if not file_exists or session is None or not valid_session(session,app.root_path):
    resp = redirect("/")  #no session code or invalid session code --> redirect to login page
  else:
    #Get parameters from SPDS
    req = requests.get(PSPDS_url+"/request_params",params={"password":"SPDS_connect"})
    with open("params.json","wb") as params:
        params.write(req.content)
    
    #Get plot(s) from SPDS
    req = requests.get(PSPDS_url+"/generate_plots",params={"password":"SPDS_connect"})
    download_plot("spot_price.jpg")
    download_plot("connected.jpg")
    download_plot("signals.jpg")
    download_plot("water_levels.jpg")

    #Get PLC data from SPDS
    req = requests.get(PSPDS_url+"/request_PLC",params={"password":"SPDS_connect"})
    with open("PLC_data.json","wb") as PLC_data:
        PLC_data.write(req.content)

    #Get list of avaliable parameters
    req = requests.get(PSPDS_url+"/list_headers",params={"password":"SPDS_connect"})
    headers = req.content.decode("utf-8").strip("\"").split(",")

    #Get list of column headers
    with open("headings.txt","r") as file:
      headings = "\n".join(file.readline().strip().split(","))

    #Process data into necessary structure
    pathdata = get_data()
    emails = email_str()

    resp = render_template("home.html",#valid session code, delete code and render homepage
                           emails=emails,
                           setpointA = pathdata["setpoints"]["A"],
                           setpointA1 = pathdata["setpoints"]["A1"],
                           setpointA2 = pathdata["setpoints"]["A2"],
                           setpointA3 = pathdata["setpoints"]["A3"],
                           setpointB = pathdata["setpoints"]["B"],
                           setpointB1 = pathdata["setpoints"]["B1"],
                           setpointB2 = pathdata["setpoints"]["B2"],
                           setpointB3 = pathdata["setpoints"]["B3"],
                           setpointC = pathdata["setpoints"]["C"],
                           setpointC1 = pathdata["setpoints"]["C1"],
                           setpointC2 = pathdata["setpoints"]["C2"],
                           setpointC3 = pathdata["setpoints"]["C3"],
                           water_level = pathdata["waterlevel"],
                           spot_price = pathdata["spot_price"],
                           life_bit = pathdata["lifebit"],
                           signal = pathdata["signal"],
                           headers = headers,
                           headings_existing = headings
                           )
  return(resp)

#converts db to excel, downloads
@app.route('/download', methods=["GET", "POST"])
def download():
  if request.method == "POST":
    rows = int(request.form.get("rows"))  #get n. of rows to download
    filetype = str(request.form.get("type"))
    session = request.cookies.get("SessionID")  #get session code param
    file_exists = os.path.exists(os.path.join(app.root_path,"current_session.txt"))
    if not file_exists or session is None or not valid_session(session,app.root_path):
      resp = redirect("/")#no session code or invalid session code --> redirect to login page
    else:#valid session code
      req = requests.get(PSPDS_url+"/get_db",params={"password":"SPDS_connect","rows":rows})#request database from SPDS
      with open("portal_data.db","wb") as database:
          database.write(req.content)#save database as file
      if filetype == "xlsx":
        excel("portal_data.db",app.root_path)#make an excel document from database
        filepath = os.path.join(app.root_path, "portal_data.xlsx")#generate filepath
        resp = send_file(filepath)#return file
      else:
        filepath = os.path.join(app.root_path, "portal_data.db")#generate filepath
        resp = send_file(filepath)#return file
    return(resp)
  else:
    return(render_template("login.html"))
  
#download custom graph and display
@app.route("/custom_graph", methods=["GET", "POST"])
def custom_graph():
  if request.method == "POST":
    rows = int(request.form.get("rows"))  #get n. of rows to download
    header = request.form.get("headers")  #get n. of rows to download
    session = request.cookies.get("SessionID")  #get session code param
    file_exists = os.path.exists(os.path.join(app.root_path,"current_session.txt"))
    if not file_exists or session is None or not valid_session(session,app.root_path):
      resp = redirect("/")#no session code or invalid session code --> redirect to login page
    else:#valid session code
       #get custom graph
       req = requests.get(PSPDS_url+"/custom_plot",params={"password":"SPDS_connect","variable":header,"rows":str(rows)})
       print(req.content)
       download_plot("custom.jpg")
       resp = render_template("custom_graph.html")
    return(resp)
  return(render_template("/login.html"))

#send changed parameters to PSPDS
@app.route("/params_change", methods=["GET", "POST"])
def params_change():
    pathdata = get_data()
    
    #Get form parameters
    #Get XPATHS
    AEMO_path = pathdata["XPATHS"]["AEMO"]["path"]
    AEMO_index = pathdata["XPATHS"]["AEMO"]["index"],
    DGEM_path = pathdata["XPATHS"]["DiamondGem"]["path"],
    DGEM_index = pathdata["XPATHS"]["DiamondGem"]["index"]
    
    #Get and process emails
    emails = request.form.get("emails").split(";")
    new_emails = []
    for email in emails:
        if "@" in email:
            new_emails.append(email.strip("\r\n; "))
    emails = new_emails

    #Get Setpoints
    setpointA = int(request.form.get("SetpointA"))
    setpointA1 = int(request.form.get("SetpointA1"))
    setpointA2 = int(request.form.get("SetpointA2"))
    setpointA3 = int(request.form.get("SetpointA3"))
    setpointB = int(request.form.get("SetpointB"))
    setpointB1 = int(request.form.get("SetpointB1"))
    setpointB2 = int(request.form.get("SetpointB2"))
    setpointB3 = int(request.form.get("SetpointB3"))
    setpointC = int(request.form.get("SetpointC"))
    setpointC1 = int(request.form.get("SetpointC1"))
    setpointC2 = int(request.form.get("SetpointC2"))
    setpointC3 = int(request.form.get("SetpointC3"))

    json = {
        "XPATHS":{
            "AEMO":{
                "path":AEMO_path,
                "index":AEMO_index
            },
            "DiamondGem":{
                "path":DGEM_path,
                "index":DGEM_index
            }
        },
        "emails":emails,
        "setpoints":{
          "A":setpointA,
          "A1":setpointA1,
          "A2":setpointA2,
          "A3":setpointA3,
          "B":setpointB,
          "B1":setpointB1,
          "B2":setpointB2,
          "B3":setpointB3,
          "C":setpointC,
          "C1":setpointC1,
          "C2":setpointC2,
          "C3":setpointC3,
        }
    }
    make_request(json)

    f = open("params.json", 'rb')  #open database
    files = {"file": (f.name, f, "multipart/form-data")}  #file format for FastAPI
    req = requests.post(url=PSPDS_url+"/change_params",params={"password":"SPDS_connect"},files=files)  #send file to PSPDS
    return(req.content)

#change the headings
@app.route("/headings_change", methods=["GET", "POST"])
def headings_change():
  headings = request.form.get("headings")
  headings = ",".join(headings.splitlines())
  with open("headings.txt","w") as file:
    file.write(headings)
  return("modified headings")

if __name__ == '__main__':
  app.run()
