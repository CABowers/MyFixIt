from flask import Flask
from flask_ask import Ask, statement

app = Flask(__name__)
ask = Ask(app, "/")

steps = ["Step 1: Put the new staples in! Close the stapler with the new staples in it.",
		"Step 2 : Put the new staples in! Close the stapler with the new staples in it.",
		"Step 3 : Start stapling stuff!"]
nosteps = "There are no previous instructions."
donesteps = "You have completed the guide. Would you like to start a new project?"

instructionnum = -1

@ask.intent("HelloIntent")
def hello():
    return statement("Hello friendo!")

@ask.launch
def start_skill():
    return statement("What do you want to fix today?")

@ask.intent("AMAZON.YesIntent")
def yes_intent():
	instructionnum++
    return statement("You have selected Stapler Maintenance. This guide requires a stapler and extra staples." + steps[instructionnum])

@ask.intent("AMAZON.NoIntent")
def no_intent():
    return statement("Goodbye")

@ask.intent("AMAZON.RepeatIntent")
def repeat_intent():
	if instructionnum < 1:
		return statement(nosteps)
	if instructionnum > len(steps):
		return statement(donesteps)
	return statement(steps[instructionnum])
		
@ask.intent("AMAZON.NextIntent")
def next_intent():
	instructionnum++
	if instructionnum < 1:
		return statement(nosteps)
	if instructionnum > len(steps):
		instructionnum--
		return statement(donesteps)
	return statement(steps[instructionnum])
	
@ask.intent("AMAZON.PreviousIntent")
def previous_intent():
	instructionnum--
	if instructionnum < 1:
		instructionnum++
		return statement(nosteps)
	if instructionnum > len(steps):
		return statement(donesteps)
	return statement(steps[instructionnum])

@ask.intent("ItemIntent")
def item_intent():
    return statement("I sent a list of possible guides through the alexa app. Please choose one or try searching again.")
