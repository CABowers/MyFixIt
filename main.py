from flask import Flask
from flask_ask import Ask, statement

app = Flask(__name__)
ask = Ask(app, "/")

step1 = "Step 1: Put the new staples in! Close the stapler with the new staples in it."
step2 = "Step 2 : Put the new staples in! Close the stapler with the new staples in it."
step3 = "Step 3 : Start stapling stuff!"

instructionnum = 0

@ask.intent("HelloIntent")
def hello():
    return statement("Hello friendo!")

@ask.launch
def start_skill():
    return statement("What do you want to fix today?")

@ask.intent("AMAZON.YesIntent")
def yes_intent():
	instructionnum++
    return statement("You have selected Stapler Maintenance. This guide requires a stapler and extra staples." + step1)

@ask.intent("AMAZON.NoIntent")
def no_intent():
    return statement("Goodbye")

@ask.intent("AMAZON.RepeatIntent")
def repeat_intent():
	if instructionnum == 1:
		return statement(step1)
	else if instructionnum == 2:
		return statement(step2)
	else if instructionnum == 3:
		return statement(step3))
	return ("You are not currently using an instruction guide.")
		
@ask.intent("AMAZON.NextIntent")
def next_intent():
	instructionnum++
	if instructionnum == 1:
		return statement(step1)
	else if instructionnum == 2:
		return statement(step2)
	else if instructionnum == 3:
		return statement(step3)
	return statement("You have completed the guide. Would you like to start a new project?")
	
@ask.intent("AMAZON.PreviousIntent")
def previous_intent():
	instructionnum--
	if instructionnum == 0:
		return statement("There are no previous instructions.")
	else if instructionnum == 1:
	return statement(step1)
	else if instructionnum == 2:
		return statement(step2)
	else if instructionnum == 3:
		return statement(step3)
    return statement("You are not currently using an instruction guide.")

@ask.intent("ItemIntent")
def item_intent():
    return statement("I sent a list of possible guides through the alexa app. Please choose one or try searching again.")
