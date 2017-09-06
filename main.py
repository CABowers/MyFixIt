from flask import Flask
from flask_ask import Ask, statement, question, session
from pyfixit import *

app = Flask(__name__)
ask = Ask(app, "/")
instruction_num = -1

steps = ["Step 1: Stapler is empty. Find more staples",
		"Step 2 : Put the new staples in! Close the stapler with the new staples in it.",
		"Step 3 : Start stapling stuff!"]
no_steps = "There are no previous instructions."
done_steps = "You have completed the guide. Would you like to start a new project?"


@ask.intent("HelloIntent")
def hello():
    return statement("Hello friendo!")

@ask.launch
def start_skill():
    global instruction_num
    instruction_num = -1
    return question('What do you want to fix today?').reprompt("I missed that. What do you want to fix today?")

@ask.intent("AMAZON.YesIntent")
def yes_intent():
    return question("You have selected Stapler Maintenance. This guide requires a stapler and extra staples. Say next to begin instructions.")


@ask.intent("AMAZON.NoIntent")
def no_intent():
    global instruction_num
    instruction_num = -1
    return statement("Goodbye")

@ask.intent("AMAZON.RepeatIntent")
def repeat_intent():
    if instruction_num < 0:
        return question(no_steps)
    if instruction_num > len(steps):
        return question(done_steps)
    return question(steps[instruction_num])

@ask.intent("AMAZON.NextIntent")
def next_intent():
    global instruction_num
    instruction_num += 1
    if instruction_num < 0:
        return question(no_steps)
    if instruction_num >= len(steps):
        instruction_num -= 1
        return question(done_steps).reprompt("I missed that." + done_steps)
    return question(steps[instruction_num])


@ask.intent("AMAZON.PreviousIntent")
def previous_intent():
    global instruction_num
    instruction_num -= 1
    if instruction_num < 0:
        instruction_num += 1
        return question(no_steps)
    if instruction_num >= len(steps):
        return question(done_steps).reprompt("I missed that." + done_steps)
    return question(steps[instruction_num])

@ask.intent("ItemIntent")
def item_intent():
    return question("I sent a list of possible guides through the alexa app. Please choose one or try searching again.").simple_card(title="Guides",content="Stapler Maintenance\nSearch Again")

if __name__ == '__main__':
    app.run()