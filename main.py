from flask import Flask
from flask_ask import Ask, statement, question, session
from pyfixit import *
import logging
import boto3

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

# Global variables

INSTRUCTIONS = 'instructions'
INSTRUCTION_NUM = 'instruction_num'
IMAGE_NUM = 'image_num'

steps = []
guide = None
guides = None
good_images = []

# Strings used for responses so no need to store as session attributes
no_steps = "There are no previous instructions."
done_steps = "You have completed the guide."

'''Contents:
Starting and exiting the skill: start_skill, no_intent, hello, yes_intent
Bookmarking: resume_bookmark, delete_bookmark, list_bookmarks, save_bookmark
Selecting a guide: search, select_guide, get_guides, select_guide_index, select_guide(title), get_guide_titles
Reading Instructions: repeat_intent, next_intent, previous_intent, text_for_step
Features of guides: len_of_guide_intent, tools_intent, num_instructions_intent, cur_instruction_intent,
    instructions_left_intent, difficulty_intent, next_picture_intent, flags_intent
Other: get_state, set_state, error_exit, get_database_table, help_intent
'''


'''Starting and Exiting the Skill'''

''' This function is ran when the skill starts.
Initializes the session attributes instruction num, source state, and image num
Asks the user if they want to resume a previous project or if they have no bookmarks what they want to fix

Returns: If they have bookmarks. Question(Continue a previous project?)
         If they don't have bookmarks. Question(What do you want to fix today?)
'''
@ask.launch
def start_skill():
    session.attributes[INSTRUCTION_NUM] = -1
    session.attributes[SOURCE_STATE] = START
    session.attributes[IMAGE_NUM] = 0

    table = get_database_table()
    user_entry = table.get_item(TableName='Bookmark', Key={'user_id': session['user']['userId']})
    if user_entry is None or 'Item' not in user_entry or len(user_entry['Item']["bookmarks"]) == 0:
        return question('What do you want to fix today?').reprompt(
            "Sorry, I missed that. What do you want to fix today?")
    return question('Would you like to continue a previous project or manage your bookmarks?').reprompt(
        'Say yes to continue an old project or say no to start a new one.')


''' If you just started, reprompts to ask what you want to fix today
If you are in the middle of a guide, asks if you want to save your current guide (bookmarking)
Otherwise, it exits the application

Returns: If in start state. Question(What do you want to fix today?)
         If they are in a guide. Question(Do you want to save the guide?)
         Otherwise. Statement(Goodbye)
'''
@ask.intent("AMAZON.StopIntent")
@ask.intent("AMAZON.NoIntent")
def no_intent():
    global guide
    if get_state() == START:
        return question('What do you want to fix today?').reprompt(
            "Sorry, I missed that. What do you want to fix today?")

    if get_state() == INSTRUCTIONS and guide != None and session.attributes[INSTRUCTION_NUM] != -1:
        set_state(NO)
        return question('Do you want to save your location in the guide?').reprompt(
            "Sorry, I missed that. Do you want to save your locatoin in the guide?")
    set_state(NO)
    session.attributes[INSTRUCTION_NUM] = -1
    guide = None
    return statement("Goodbye")


''' Easter Egg (no functional purpose)

Returns: Statement(Hello friendo)
'''
@ask.intent("HelloIntent")
def hello():
    return statement("Hello friendo!")


'''Bookmarking Section'''

'''
If the user says "Yes" when we ask if they want to resume a previous function, we tell them what the bookmarks are
If the user says "Yes" when we ask if they want to save the project, we save it in the database and say goodbye

Returns: If start. Question(Select a bookmark)
Returns: Otherwise. Statement(Your guide has been bookmarked. Bye)
'''
@ask.intent("AMAZON.YesIntent")
def yes_intent():
    if get_state() == START:
        return list_bookmarks()
    if get_state() == NO:
        save_bookmark()
        session.attributes[INSTRUCTION_NUM] = -1
        global guide
        guide = None
        return statement("Your guide has been bookmarked. Goodbye.")


'''This intent is where we select the bookmark the user said (based on the number), and start reading instructions

Args: Bookmark_number. The number spoken by the user, which is the number of the bookmark they would like to select

Returns: if invalid number. Question(Select a valid bookmark)
Returns: otherwise. Question(Next instruction)
'''
@ask.intent("ResumeBookmark")
def resume_bookmark(bookmark_number):
    index = int(bookmark_number) - 1
    table = get_database_table()
    user_entry = table.get_item(TableName='Bookmark', Key={'user_id': session['user']['userId']})["Item"]
    bookmarks = user_entry["bookmarks"]
    if index < 0 or index >= len(bookmarks):
        return question("Select a valid bookmark").reprompt("Select a valid bookmark")
    guide_id = bookmarks[index]['guide_id']
    global guide
    guide = Guide(guide_id)
    global steps
    steps = guide.steps
    session.attributes[INSTRUCTION_NUM] = int(bookmarks[index]['step']) - 1
    set_state(INSTRUCTIONS)
    return next_intent()


'''This deletes the bookmark the user wants to delete (based on the number they said)

Args: Bookmark_number. The number spoken by the user, which is the number of the bookmark they would like to delete

Returns: The list of bookmarks
'''
@ask.intent("DeleteBookmark")
def delete_bookmark(bookmark_number):
    index = int(bookmark_number) - 1
    table = get_database_table()
    bookmarks = table.get_item(TableName='Bookmark', Key={'user_id': session['user']['userId']})["Item"]['bookmarks']
    if index > 0 and index < len(bookmarks):
        del bookmarks[index]
        table.put_item(TableName='Bookmark',
                       Item={
                           'user_id': "%s" % session['user']['userId'],
                           'bookmarks': bookmarks
                       })
    return list_bookmarks()


'''This function retrieves the bookmarks from the database, and lists them to the user so they can pick one

Returns: Question. Prompts the user to select which item they would like to delete or select, and lists the bookmarks.
'''
def list_bookmarks():
    table = get_database_table()
    user_entry = table.get_item(TableName='Bookmark', Key={'user_id': session['user']['userId']})["Item"]
    output = ""
    num = 1
    for bookmark in user_entry["bookmarks"]:
        output += "{}. Step {} for {}\n".format(num, bookmark["step"] + 1, bookmark["guide_title"])
        num += 1
    return question("Select which bookmark number to resume or delete").simple_card(title="Bookmarks",
                                                                                    content=output).reprompt(
        "Can you repeat that?")


'''This helper function saves the current project to the database so the user can resume their project later
'''
def save_bookmark():
    table = get_database_table()
    user_entry = table.get_item(TableName='Bookmark', Key={'user_id': session['user']['userId']})
    if user_entry is None or 'Item' not in user_entry:
        table.put_item(TableName='Bookmark',
                       Item={'user_id': "%s" % session['user']['userId'],
                             'bookmarks': [{
                                 'guide_id': guide.id,
                                 'guide_title': guide.title,
                                 'step': session.attributes[INSTRUCTION_NUM]
                             }]
                             })
    else:
        bookmarks = user_entry["Item"]['bookmarks']
        bookmarks.append({
            'guide_id': guide.id,
            'guide_title': guide.title,
            'step': session.attributes[INSTRUCTION_NUM]
        })
        table.put_item(TableName='Bookmark',
                       Item={
                           'user_id': "%s" % session['user']['userId'],
                           'bookmarks': bookmarks
                       })


'''Selecting a Guide'''


'''Searches the ifixit API for the item the user wants to fix

Exception: Throws exception when initializing guide names

Returns: Question: 'Here are your search results' and the list of search results
'''
@ask.intent("SearchIntent")
def search(item):
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


'''Uses the number to select the guide from the list. Sets this as the current guide and begins reading instructions.

Args: Guide_number. The number in the list of guides the user wants to use

Returns: Question. 'You have selected this guide. Say next to begin instructions.'
         Question. 'Please select a valid guide.'
'''
@ask.intent("SelectGuideIntent")
def select_guide(guide_number):
    if get_state() == SEARCH or get_state() == SELECT_GUIDE:
        found = select_guide_index(int(guide_number) - 1)
        set_state(SELECT_GUIDE)
        if found:
            return question("You have selected guide {} . Say next to begin instructions".format(guide.title)).reprompt(
                "Please say next to continue.")
        return question("Please select a valid guide.").reprompt(
            "You must state the number next to the guide title on the list sent to your phone.")
    else:
        return error_exit()


'''Searches myfixit for guides associated with the search keyword

Args: search the word used to search for guides
'''
def get_guides(search):
    global guides
    guides = Category(search).guides


'''Initializes the guide and steps variables based on the given index

Args: index The number of the guide in the list

Returns: True if the guide exists
         False if the index is out of range
'''
def select_guide_index(index):
    global guide
    global steps
    if index < 0 or index >= len(guides):
        logger.info("Guide number was not available!")
        return False
    guide = guides[index]
    steps = guide.steps
    session.attributes[INSTRUCTION_NUM] = -1
    return True


'''Initializes the guide and steps variables based on the title of the guide

Args: title the title of the guide to be selected

Returns: True if the guide was found
         False otherwise
'''
def select_guide(title):
    global guide
    global steps
    found = False
    for g in guides:
        if g.title.lower() == title.lower():
            guide = g
            steps = g.steps
            session.attributes[INSTRUCTION_NUM] = -1
            found = True
    return found


'''Gets a list of all of the titles in guides

Returns: A list of the titles (strings) of the guides
'''
def get_guide_titles():
    titles = [g.title for g in guides]
    return titles


'''Reading Instructions'''

'''Converts the instruction/step into text to be read by Alexa

Args: step the string from the guide for the instruction

Returns: A string that can be read by Alexa
'''
def text_for_step(step):
    step_text = "Step {:d} ".format(step)
    for line in step.lines:
        step_text = "{}\n{}".format(step_text, line.text)
    return step_text


'''Rereads the current instruction

Returns. Question(There are no previous instructions)
         Question(You have finished the guide)
         Question('instruction')
'''
@ask.intent("AMAZON.RepeatIntent")
def repeat_intent():
    instruction_num = session.attributes[INSTRUCTION_NUM]
    if instruction_num < 0:
        return question(no_steps)
    if instruction_num > len(steps):
        return question(done_steps)
    return question(text_for_step(steps[instruction_num])).reprompt(
        "Say next when you are ready to begin the next step.")


'''Reads the next instruction
Sets the state, updates the instruction num, sends any pictures associated with the instruciton.

Returns: Question. '[instruciton]'
'''
@ask.intent("AMAZON.NextIntent")
def next_intent():
    global good_images
    instruction_num = session.attributes[INSTRUCTION_NUM]

    if get_state() == SELECT_GUIDE or get_state() == INSTRUCTIONS:
        set_state(INSTRUCTIONS)
        instruction_num += 1
        if instruction_num < 0:
            return question(no_steps)
        if instruction_num >= len(steps):
            session.attributes[INSTRUCTION_NUM] -= 1
            return question(done_steps).reprompt("I missed that." + done_steps)
        session.attributes[INSTRUCTION_NUM] = instruction_num
        good_images = []
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


'''Reads the previous instruction

Returns: Question([instruciton])
'''
@ask.intent("AMAZON.PreviousIntent")
def previous_intent():
    if get_state() == INSTRUCTIONS:
        instruction_num = session.attributes[INSTRUCTION_NUM]
        instruction_num -= 1
        session.attributes[INSTRUCTION_NUM] = instruction_num
        set_state(INSTRUCTIONS)  # Redundant but it's safer to be explicit
        if instruction_num < 0:
            instruction_num += 1
            session.attributes[INSTRUCTION_NUM] = instruction_num
            return question(no_steps).reprompt("I missed that." + no_steps)
        if instruction_num >= len(steps):
            return question(done_steps).reprompt("I missed that." + done_steps)
        return question(text_for_step(steps[instruction_num])).reprompt("Say next to proceed to the next step.")
    else:
        return error_exit()


'''Features of Guides'''


'''Tells the user the length of guide

Args: len_guide_number. The number of the guide in the list that the user wants to know the length of

Returns: Question(The length of this guide is [guide length])
'''
@ask.intent("LengthOfGuideIntent")
def len_of_guide_intent(len_guide_number):
    if isinstance(len_guide_number, int):
        length = select_guide_index(len_guide_number)
    else:
        length = guide.time_required_min
    hours = length / (60 * 24)
    minutes = (length % (60 * 24)) / 60
    seconds = length % 60

    return question(
        "The length of this guide is %i hours %i minutes and %i seconds" % (hours, minutes, seconds)).reprompt(
        "Say next to continue to the instructions.")


'''Sends a list of tools to the Alexa app if there are any

Returns: Question(There are no tools for this guide)
         Question(I have sent a list of tools to the alexa app [tools])
'''
@ask.intent("ToolsIntent")
def tools_intent():
    if guide.tools is None:
        return question("There are no tools required for this guide.").reprompt(
            "Say next to continue to the next instruction.")
    tools_list = guide.tools
    display_list = ""
    for tool in tools_list:
        if tool["text"]:
            display_list = display_list + "- " + tool["text"] + " (%i)\n" % tool["quantity"]
    return question("I have sent a list of tools you will need to your Alexa app.").simple_card(title="Tools Required",
                                                                                                content=display_list) \
        .reprompt("Say next to continue to the next instruction.")


'''Tells the user the total number of instructions in the current guide

Returns: Question(The number of instructions in this guide is [number of steps])
'''
@ask.intent("NumberInstructionsIntent")
def num_instructions_intent():
    return question("The number of instructions in this guide is %i" % len(steps)).reprompt(
        "Say next to continue to the instructions.")


'''Tells the user the number of the current instruction

Returns: Question(You have not started any instructions yet)
         Question(The current instruction number is [instruction number])
'''
@ask.intent("CurrentInstructionIntent")
def cur_instruction_intent():
    num = session.attributes[INSTRUCTION_NUM]
    num = num + 1
    if num <= 0:
        return question("You have not started any instructions yet. Say next to go to the first instruction.").reprompt(
            "Say next to continue to the instructions.")
    return question("The current instruction number for the current guide is %i" % num).reprompt(
        "Say next to go to the next step.")


'''Tells the user the number of instructions remaining in the guide

Returns: Question(The number of instructions left in this guide is [number of instructions left])
'''
@ask.intent("InstructionsLeftIntent")
def instructions_left_intent():
    instructions_left = len(steps) - session.attributes[INSTRUCTION_NUM]
    return question("The number of instructions left in this guide is %i" % instructions_left).reprompt(
        "Say next to go to the next step.")


'''Tells the user the difficulty of the instruction guide

Returns: Question(The difficulty of this guide is [difficulty])
'''
@ask.intent("DifficultyIntent")
def difficulty_intent():
    return question("The difficulty of the guide is " + guide.difficulty).reprompt(
        "Say next to continue to the instructions.")

'''Sends any pictures associated with the current instruction to the phone

Returns: Question(Image and step)
'''
@ask.intent("NextPicture")
def next_picture_intent():
    image_num = session.attributes[IMAGE_NUM]
    instruction_num = session.attributes[INSTRUCTION_NUM]
    global good_images
    image_num += 1
    session.attributes[IMAGE_NUM] = image_num
    if image_num >= len(good_images):
        return question("There are no more images for this step.")
    image = good_images[image_num]
    text = ": Image {} of {}".format(image_num + 1, len(good_images))
    return question(text).simple_card(title="Step %i" % (instruction_num + 1) + text,
                                      content=image.original).reprompt("I didn't catch that. "
                                                                       "Can you please repeat what you said?")


'''Informs the user of any flags associated with a guide

Returns: question(The flags for this guide are)
         question(There are no flags for this guide)
'''
@ask.intent("FlagsIntent")
def flags_intent():
    if guide:
        statement = "The flags for this guide are"
        for flag in guide.flags:
            statement += ", " + flag.title
    else:
        statement = "You have not selected a guide, so I cannot tell you the flags"
    return question(statement)


'''Other functions'''

'''Gets the stored previous state of the session

Returns: Source_state
'''
def get_state():
    return session.attributes.get(SOURCE_STATE)


'''Sets the state to be "state"

Args: state the new state
'''
def set_state(state):
    session.attributes[SOURCE_STATE] = state


'''Informs the user an error occurred

Returns: Statement(There was an error)
'''
def error_exit():
    # TODO: Return to source state's intent
    logger.info("Search state did not follow start state")
    return statement("There was an error. Goodbye")


'''Gets the dynamodb table

Returns: The table that stores the bookmarks
'''
def get_database_table():
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    return dynamodb.Table('Bookmark')


'''Instructs the user what they should do based on their current state

Returns: Question(Response based on state)
'''
@ask.intent("HelpIntent")
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
    return question(response).reprompt("I don't understand. Can you repeat that?")


if __name__ == '__main__':
    app.run()
