from flask import Flask
from flask_ask import Ask, statement

app = Flask(__name__)
ask = Ask(app, "/")

@ask.intent("HelloIntent")
def hello():
    return statement("Hello friendo!")

@ask.launch
def start_skill():
    return statement("What do you want to fix today?")

@ask.intent("AMAZON.YesIntent")
def yes_intent():
    return statement("YES!")

@ask.intent("AMAZON.NoIntent")
def no_intent():
    return statement("NO!")

@ask.intent("AMAZON.RepeatIntent")
def repeat_intent():
    return statement("repeat")

@ask.intent("AMAZON.NextIntent")
def next_intent():
    return statement("Next!")

@ask.intent("AMAZON.PreviousIntent")
def previous_intent():
    return statement("previous!")

@ask.intent("ItemIntent")
def item_intent():
    return statement("I sent a list of possible guides through the alexa app. Please choose one or try searching again.")
