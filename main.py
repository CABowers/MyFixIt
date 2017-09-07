from flask import Flask
from flask_ask import Ask, statement, question, session
from pyfixit import *

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


@ask.intent("SearchIntent")
def search(item):
    get_guides(item)
    guide_names = "\n".join(g.title for g in guides)
    return question("Here are your search results. Please select a guide by reading the title.").simple_card(title="Guides",content=guide_names)


@ask.intent("SelectGuideIntent")
def selectguide(title):
    found = select_guide(title)
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


 # TODO: new search intent replaces this. When we remove this, remove it from sample utterances and Intent Schema
@ask.intent("ItemIntent")
def item_intent():
    return question("I sent a list of possible guides through the alexa app. Please choose one or try searching again.").simple_card(title="Guides",content="Stapler Maintenance\nSearch Again")


def get_guides(search):
    global guides
    guides = Category(search).guides


def select_guide_index(index):
    global guide
    global steps
    global instruction_num
    guide = guides[index]
    steps = guide.steps
    instruction_num = -1


def select_guide(title):
    global guide
    global steps
    global instruction_num
    found = False
    for g in guides:
        if g.title == title:
            guide = g
            steps = g.steps
            instruction_num = -1
            found = True
    return found


def text_for_step(step):
    step_text = ""
    for line in step.lines:
        text = '(%s) %s' % (line.bullet, line.text)
        step_text = "{}\n{}".format(step_text, text)
    return step_text
    

def get_guide_titles():
    titles = [g.title for g in guides]
    return titles

if __name__ == '__main__':
    app.run()