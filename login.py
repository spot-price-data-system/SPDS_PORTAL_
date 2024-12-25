from random import randint
import os

chars = "0123456789qwertyuiopasdfghjklzxcvbnm"


def session_code(root):
  #generate random session code
  code = ""
  for i in range(10):
    code += chars[randint(0, 35)]

  #save code in txt file
  with open(os.path.join(root,"current_session.txt"), "w") as file:
    file.write(code)

  return (code)


def valid_session(code,root):
  filepath = os.path.join(root,"current_session.txt")
  #get sesion code from txt file
  with open(filepath, "r") as file:
    current = file.read().strip()
  return (current == code)#return boolean for code matching
