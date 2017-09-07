from flask import Flask
from flask_ask import Ask, statement, question, session
from pyfixit import *
import logging

logger = logging.getLogger()

app = Flask(__name__)
ask = Ask(app, "/")
instruction_num = -1

steps = []
guide = None;
guides = None;
no_steps = "There are no previous instructions."
done_steps = "You have completed the guide."


@ask.intent("HelloIntent")
def hello():
    return statement("Hello friendo!")


@ask.launch
def start_skill():
    global instruction_num
    instruction_num = -1
    return question('What do you want to fix today?').reprompt("I missed that. What do you want to fix today?")


@ask.intent("HelloIntent")
def hello():
 return statement("Hello friendo!")

@ask.intent("SearchIntent")
def search(item):
    if item is None:
        logger.info("Item is None")
        get_guides("Stapler")
    else:
        get_guides(item)
    guide_names = ""
    i = 1
    for g in guides:
        num = "\n%i. " % i
        guide_names = guide_names + num + g.title
        i += 1
    return question("Here are your search results. Please select a guide by selecting the corresponding number.")\
        .simple_card(title="Guides", content=guide_names)


@ask.intent("SelectGuideIntent")
def selectguide(guide_number):
    found = False;
    found = select_guide_index(guide_number)
    if found:
        return question("You have selected guide {} . Say next to begin instructions".format(guide.title))
    return question("Please select a valid guide.")

# Currently irrelavent
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
    return question(text_for_step(steps[instruction_num]))


@ask.intent("AMAZON.NextIntent")
def next_intent():
    global instruction_num
    instruction_num += 1
    if instruction_num < 0:
        return question(no_steps)
    if instruction_num >= len(steps):
        instruction_num -= 1
        return question(done_steps).reprompt("I missed that." + done_steps)
    return question(text_for_step(steps[instruction_num]))


@ask.intent("AMAZON.PreviousIntent")
def previous_intent():
    global instruction_num
    instruction_num -= 1
    if instruction_num < 0:
        instruction_num += 1
        return question(no_steps)
    if instruction_num >= len(steps):
        return question(done_steps).reprompt("I missed that." + done_steps)
    return question(text_for_step(steps[instruction_num]))


def get_guides(search):
    global guides
    guides = Category(search).guides


def select_guide_index(index):
    global guide
    global steps
    global instruction_num
    if index >= 0 and index < guides.length:
        logger.info("Guide number was not available")
        return
    guide = guides[index]
    steps = guide.steps
    instruction_num = -1
    return True;

def select_guide(title):
    global guide
    global steps
    global instruction_num
    found = False
    for g in guides:
        if g.title.lower() == title.lower():
            guide = g
            steps = g.steps
            instruction_num = -1
            found = True
    return found


def text_for_step(step):
    step_text = ""
    for line in step.lines:
        step_text = "{}\n{}".format(step_text, line.text)
    return step_text


def get_guide_titles():
    titles = [g.title for g in guides]
    return titles

if __name__ == '__main__':
    app.run()