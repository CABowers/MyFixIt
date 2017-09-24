from flask import Flask
from flask_ask import Ask, statement, question, session
from pyfixit import *
import logging

logger = logging.getLogger()

app = Flask(__name__)
ask = Ask(app, "/")
instruction_num = -1

SOURCE_STATE = 'source_state'
# LIST OF STATES
HELP = 'help'
START = 'start'
SEARCH = 'search'
SELECT_GUIDE = 'select_guide'
YES = 'yes'
NO = 'no'
INSTRUCTIONS = 'instructions'

steps = []
guide = None
guides = None
no_steps = "There are no previous instructions."
done_steps = "You have completed the guide."


@ask.launch
def start_skill():
    global instruction_num
    instruction_num = -1
    session.attributes[SOURCE_STATE] = START
    return question('What do you want to fix today?').reprompt("I missed that. What do you want to fix today?")


@ask.intent("SearchIntent")
def search(item):
    if get_state() == START:
        if item is None:
            logger.info("Item is None")
            start_skill()
        else:
            get_guides(item)
        guide_names = ""
        i = 1
        for g in guides:
            num = "\n%i. " % i
        guide_names = guide_names + num + g.title
        i += 1
        set_state(SEARCH)
        return question("Here are your search results. Please select a guide by selecting the corresponding number.") \
            .simple_card(title="Guides", content=guide_names)
    else:
        return error_exit()


@ask.intent("SelectGuideIntent")
def selectguide(guide_number):
    if get_state() == SEARCH or get_state() == SELECT_GUIDE:
        found = select_guide_index(int(guide_number) - 1)
        set_state(SELECT_GUIDE)
        if found:
            return question("You have selected guide {} . Say next to begin instructions".format(guide.title))
        return question("Please select a valid guide.")
    else:
        return error_exit()


@ask.intent("AMAZON.NoIntent")
def no_intent():
    global instruction_num
    instruction_num = -1
    set_state(NO)
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
    if get_state() == SELECT_GUIDE or get_state() == INSTRUCTIONS:
        global instruction_num
        instruction_num += 1
        if instruction_num < 0:
            return question(no_steps)
        if instruction_num >= len(steps):
            instruction_num -= 1
            return question(done_steps).reprompt("I missed that." + done_steps)
        for image in steps[instruction_num].media:
            if image.thumbnail and image.original:
                return question(text_for_step(steps[instruction_num])).standard_card(title="Step %i" % instruction_num,
                                           text="",
                                           small_image_url=image.thumbnail,
                                           large_image_url=image.original)
        set_state(INSTRUCTIONS)
        return question(text_for_step(steps[instruction_num]))
    else:
        return error_exit()


@ask.intent("AMAZON.PreviousIntent")
def previous_intent():
    if get_state() == INSTRUCTIONS:
        global instruction_num
        instruction_num -= 1
        set_state(INSTRUCTIONS) #Redundant but it's safer to be explicit
        if instruction_num < 0:
            instruction_num += 1
            return question(no_steps)
        if instruction_num >= len(steps):
            return question(done_steps).reprompt("I missed that." + done_steps)
        return question(text_for_step(steps[instruction_num]))
    else:
        return error_exit()

'''
HELP = 'help'
START = 'start'
SEARCH = 'search'
SELECT_GUIDE = 'select_guide'
YES = 'yes'
NO = 'no'
NEXT = 'next'
PREVIOUS = 'previous' 
'''


@ask.intent("AMAZON.HelpIntent")
def help_intent():
    previous = get_state()
    response = 'You are using the My Fix It skill'
    if previous == HELP:
        response = "I'm sorry, I don't know how to help you get help."
    elif previous == START:
        response = "Please tell me what you would like to fix today, and I will guide you through the process."
    elif previous == SEARCH:
        response = "I sent a list of guides to your phone, please tell me the number of the guide you would like to complete."
    elif previous == SELECT_GUIDE:
        response == "Please say next if you have selected a valid guide"


def get_guides(search):
    global guides
    guides = Category(search).guides


def select_guide_index(index):
    global guide
    global steps
    global instruction_num
    if index < 0 or index >= len(guides):
        logger.info("Guide number was not available!")
        return False
    guide = guides[index]
    steps = guide.steps
    instruction_num = -1
    return True


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


def get_state():
    return session.attributes.get(SOURCE_STATE)


def set_state(state):
    session.attributes[SOURCE_STATE] = state


def error_exit():
    # TODO: Return to source state's intent
    logger.info("Search state did not follow start state")
    return statement("There was an error. Goodbye")


if __name__ == '__main__':
    app.run()
