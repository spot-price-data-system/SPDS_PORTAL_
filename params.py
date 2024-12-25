import json

def get_data():
    with open("params.json","r") as f:
        params = json.load(f)
    with open("PLC_data.json","r") as f:
        PLC_data = json.load(f)
    return({**params,**PLC_data})

def make_request(data):
    with open("params.json","w") as f:
        json.dump(data,f,indent=4)

def email_str():
    string = ""
    with open("params.json") as f:
        data = json.load(f)
        for line in data["emails"]:
            string += line.strip() + ";\n"
    return(string)
