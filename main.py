from flask import Flask
from flask_ask import Ask, statement, question, session
from pyfixit import *
import logging

logger = logging.getLogger()

app = Flask(__name__)
ask = Ask(app, "/")

SOURCE_STATE = 'source_state'
# LIST OF STATES
HELP = 'help'
START = 'start'
SEARCH = 'search'
SELECT_GUIDE = 'select_guide'
YES = 'yes'
NO = 'no'
INSTRUCTIONS = 'instructions'

STEPS = 'steps'
GUIDE = 'guide'
GUIDES = 'guides'
NO_STEPS = 'no_steps'
DONE_STEPS = 'done_steps'
IMAGE_NUM = 'image_num'
GOOD_IMAGES = 'good_images'

@ask.intent("HelloIntent")
def hello():
    return statement("Hello friendo!")


@ask.launch
def start_skill():
    session.attributes['instruction_num'] = -1
    session.attributes[SOURCE_STATE] = START
    session.attributes[DONE_STEPS] = "You have completed the guide."
    session.attributes[NO_STEPS] = "There are no previous instructions."
    session.attributes[STEPS] = []
    session.attributes[GUIDE] = None;
    session.attributes[GUIDES] = None;
    session.attributes[IMAGE_NUM] = 0
    session.attributes[GOOD_IMAGES] = [];

    return question('What do you want to fix today?').reprompt("Sorry, I missed that. What do you want to fix today?")


@ask.intent("SearchIntent")
def search(item):
    guides = get_attribute(GUIDES)
    if get_state() == START:
        if item is None:
            logger.info("Item is None")
            start_skill()
        else:
            get_guides(item)
        try:
            guide_names = ""
            i = 1
            for g in guides:
                num = "\n%i. " % i
                if g and g.title:
                    guide_names = guide_names + num + g.title
                    i += 1
        except Exception, e:
            logger.info(str(e))

        set_state(SEARCH)
        return question("Here are your search results. Please select a guide by selecting the corresponding number.") \
            .simple_card(title="Guides", content=guide_names)
    else:
        return error_exit()


@ask.intent("SelectGuideIntent")
def select_guide(guide_number):
    if get_state() == SEARCH or get_state() == SELECT_GUIDE:
        found = select_guide_index(int(guide_number) - 1)
        set_state(SELECT_GUIDE)
        if found:
            return question("You have selected guide {} . Say next to begin instructions".format(guide.title)).reprompt("Please say next to continue.")
        return question("Please select a valid guide.").reprompt("You must state the number next to the guide title on the list sent to your phone.")
    else:
        return error_exit()


@ask.intent("AMAZON.StopIntent")
@ask.intent("AMAZON.NoIntent")
def no_intent():
    session.attributes['instruction_num'] = -1
    set_state(NO)
    return statement("Goodbye")


@ask.intent("AMAZON.RepeatIntent")
def repeat_intent():
    steps = get_attribute(STEPS)
    instruction_num = session.attributes['instruction_num']
    if instruction_num < 0:
        return question(get_attribute(NO_STEPS))
    if instruction_num > len(steps):
        return question(get_attribute(DONE_STEPS))
    return question(text_for_step(steps[instruction_num])).reprompt("Say next when you are ready to begin the next step.")


@ask.intent("AMAZON.NextIntent")
def next_intent():
    good_images = get_attribute(GOOD_IMAGES)
    instruction_num = session.attributes['instruction_num']
    steps = get_attribute(STEPS)
    if get_state() == SELECT_GUIDE or get_state() == INSTRUCTIONS:
        set_state(INSTRUCTIONS)
        instruction_num += 1
        if instruction_num < 0:
            return question(get_attribute(NO_STEPS))
        if instruction_num >= len(steps):
            session.attributes['instruction_num'] -= 1
            return question(get_attribute(DONE_STEPS)).reprompt("I missed that." + get_attribute(DONE_STEPS))
        session.attributes['instruction_num'] = instruction_num
        empty_array = []
        set_attribute(good_images, empty_array)
        for image in steps[instruction_num].media:
            if image.original:
                good_images.append(image)
        if len(good_images) > 1:
            reply = "We have sent the first of %i images to your Alexa app. To get the next image say next image" \
                    % len(good_images) \
                    + text_for_step(steps[instruction_num])
        elif len(good_images) == 1:
            reply = "We have sent an image associated with this step to your Alexa app." \
                    + text_for_step(steps[instruction_num])
        elif len(good_images) == 0:
            return question(text_for_step(steps[instruction_num])).reprompt("Can you repeat that?")

        if reply:
            return question(reply).simple_card(title="Step %i" % (instruction_num + 1),
                                                content=good_images[0].original).reprompt("Can you repeat that?")
        else:
            logger.error("good_images was not set correctly!")
    logger.error("State not correct")
    return error_exit()


@ask.intent("AMAZON.PreviousIntent")
def previous_intent():
    steps = get_attribute(STEPS)
    if get_state() == INSTRUCTIONS:
        instruction_num = session.attributes['instruction_num']
        instruction_num -= 1
        session.attributes['instruction_num'] = instruction_num
        set_state(INSTRUCTIONS) #Redundant but it's safer to be explicit
        if instruction_num < 0:
            instruction_num += 1
            session.attributes['instruction_num'] = instruction_num
            return question(get_attribute(NO_STEPS)).reprompt("I missed that." + get_attribute(NO_STEPS))
        if instruction_num >= len(steps):
            return question(get_attribute(DONE_STEPS)).reprompt("I missed that." + get_attribute(DONE_STEPS))
        return question(text_for_step(steps[instruction_num])).reprompt("Say next to proceed to the next step.")
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


@ask.intent("HelpIntent")
def help_intent():
    previous = get_state()
    steps = get_attribute(STEPS)
    response = 'You are using the My Fix It skill'
    if previous == HELP:
        response = "I'm sorry, I don't know how to help you get help."
    elif previous == START:
        response = "Please tell me what you would like to fix today, and I will guide you through the process."
    elif previous == SEARCH:
        response = "I sent a list of guides to your phone, please tell me the number of the guide you would like to complete."
    elif previous == SELECT_GUIDE:
        response == "Please say next if you have selected a valid guide"
    return question(response).reprompt("I don't understand. Can you repeat that?")

# Length of task
@ask.intent("LengthOfGuideIntent")
def len_of_guide_intent(len_guide_number):
    if isinstance(len_guide_number, int):
        length = select_guide_index(len_guide_number)
    else:
        length = guide.time_required_min
    hours = length / (60 * 24)
    minutes = (length % (60 * 24)) / 60
    seconds = length % 60

    return question("The length of this guide is %i hours %i minutes and %i seconds" %(hours, minutes, seconds)).reprompt("Say next to continue to the instructions.")


# Number of instructions
@ask.intent("NumberInstructionsIntent")
def num_instructions_intent():
    steps = get_attribute(STEPS)
    return question("The number of instructions in this guide is %i" %len(steps)).reprompt("Say next to continue to the instructions.")

# Current instruction
@ask.intent("CurrentInstructionIntent")
def cur_instruction_intent():
    num = session.attributes['instruction_num']
    num = num + 1
    if num <= 0:
        return question("You have not started any instructions yet. Say next to go to the first instruction.").reprompt("Say next to continue to the instructions.")
    return question("The current instruction number for the current guide is %i" %num).reprompt("Say next to go to the next step.")

# Number of instructions remaining
@ask.intent("InstructionsLeftIntent")
def instructions_left_intent():
    steps = get_attribute(STEPS)
    instructions_left = len(steps) - session.attributes['instruction_num']
    return question("The number of instructions left in this guide is %i" %instructions_left).reprompt("Say next to go to the next step.")

# Difficulty of the instruction guide
@ask.intent("DifficultyIntent")
def difficulty_intent():
    return question("The difficulty of the guide is " + guide.difficulty).reprompt("Say next to continue to the instructions.")


@ask.intent("NextPicture")
def next_picture_intent():
    image_num = get_attribute(IMAGE_NUM)
    good_images = get_attribute(GOOD_IMAGES)
    instruction_num = get_attribute('instruction_num')
    set_attribute(IMAGE_NUM, image_num + 1)
    image_num = get_attribute(IMAGE_NUM)
    if image_num >= len(good_images):
        return question("There are no more images for this step.")
    image = good_images[image_num]
    text = ": Image {} of {}".format(image_num + 1, len(good_images))
    return question(text).simple_card(title="Step %i" % instruction_num + text,
                                      content=image.original).reprompt("I didn't catch that. "
                                                                       "Can you please repeat what you said?")

@ask.intent("FlagsIntent")
def flags_intent():
    if guide:
        statement = "The flags for this guide are"
        for flag in guide.flags:
            statement += ", " + flag.title 
    else:
        statement = "You have not selected a guide, so I cannot tell you the flags"
    return question(statement)

# Helper methods
def get_guides(search):
    set_attribute(GUIDES, Category(search).guides)

def select_guide_index(index):
    guide = get_attribute(GUIDE)
    guides = get_attribute(GUIDES)
    if index < 0 or index >= len(guides):
        logger.info("Guide number was not available!")
        return False
    set_attribute(GUIDE, guides[index])
    set_attribute(STEPS, guide.steps)
    session.attributes['instruction_num'] = -1
    return True


def select_guide(title):
    guides = get_attribute(GUIDES)
    found = False
    for g in guides:
        if g.title.lower() == title.lower():
            set_attribute(GUIDE, g)
            set_attribute(STEPS, g.steps)
            session.attributes['instruction_num'] = -1
            found = True
    return found


def text_for_step(step):
    step_text = ""
    for line in step.lines:
        step_text = "{}\n{}".format(step_text, line.text)
    return step_text


def get_guide_titles():
    guides = get_attribute(GUIDES)
    titles = [g.title for g in guides]
    return titles

# Gets the stored previous state of the session
def get_state():
    return session.attributes.get(SOURCE_STATE)

# Gets the stored session attribute
def get_attribute(state):
    return session.attributes.get(state)

def set_state(state):
    session.attributes[SOURCE_STATE] = state

def set_attribute(state, value):
    session.attributes[state] = value

def error_exit():
    # TODO: Return to source state's intent
    logger.info("Search state did not follow start state")
    return statement("There was an error. Goodbye")


if __name__ == '__main__':
    app.run()


