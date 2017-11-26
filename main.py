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
INSTRUCTIONS = 'instructions'

# Global variables

INSTRUCTION_NUM = 'instruction_num'
IMAGE_NUM = 'image_num'
GUIDE_ID = 'guide_id'
GUIDE_ID_LIST = 'guide_id_list'


# Strings used for responses so no need to store as session attributes
no_steps = "There are no previous instructions."
done_steps = "You have completed the guide. Do you want to save your location in the guide?"

'''Contents:
Starting and exiting the skill: start_skill, no_intent, hello, yes_intent
Bookmarking: resume_bookmark, delete_bookmark, list_bookmarks, save_bookmark
Selecting a guide: search, select_guide, get_guides, select_guide_index, get_guide_titles
Reading Instructions: repeat_intent, next_intent, previous_intent, text_for_step
Features of guides: len_of_guide_intent, tools_intent, num_instructions_intent, cur_instruction_intent,
    instructions_left_intent, difficulty_intent, next_picture_intent, flags_intent
Other: get_state, set_state, error_exit, get_database_table, help_intent
'''

'''
Performs setup for session attributes
'''
def setup():
    session.attributes[INSTRUCTION_NUM] = -1
    session.attributes[SOURCE_STATE] = START
    session.attributes[IMAGE_NUM] = 0
    session.attributes[GUIDE_ID] = -1

'''Starting and Exiting the Skill'''

''' This function is run when the skill starts.
Initializes the session attributes instruction num, source state, and image num
If the user has no bookmarks, it asks the user if they want to resume a previous project
Else it asks what the user wants to fix

Returns: If they have bookmarks. Question(Continue a previous project?)
         If they don't have bookmarks. Question(What do you want to fix today?)
'''
@ask.launch
def start_skill():
    setup()

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

@ask.intent("AMAZON.NoIntent")
def no_intent():
    guide = None
    if (session.attributes[GUIDE_ID] != -1):
        guide = Guide(session.attributes[GUIDE_ID])
    if get_state() == START:
        return question('What do you want to fix today?').reprompt(
            "Sorry, I missed that. What do you want to fix today?")

    if get_state() == INSTRUCTIONS and guide is not None and session.attributes[INSTRUCTION_NUM] != -1:
        set_state(NO)
        return question('Do you want to save your location in the guide?').reprompt(
            "Sorry, I missed that. Do you want to save your location in the guide?")
    set_state(NO)
    session.attributes[INSTRUCTION_NUM] = -1
    session.attributes[GUIDE_ID] = -1
    return statement("Goodbye")


''' Stops the guide and asks if they want to save the location of the guide
Returns: If they are in a guide. Question(Do you want to save the guide?)
         Otherwise. Statement(Goodbye)
'''
@ask.intent("AMAZON.CancelIntent") # cancel could be used in the future to cancel an in skill task but remain in the skill
@ask.intent("AMAZON.StopIntent")
def stop_intent():
    guide = None
    if GUIDE_ID in session.attributes.keys() and session.attributes[GUIDE_ID] != -1:
        guide = Guide(session.attributes[GUIDE_ID])
    
    if get_state() == INSTRUCTIONS and guide is not None and session.attributes[INSTRUCTION_NUM] != -1:
        set_state(NO)
        return question('Do you want to save your location in the guide?').reprompt(
            "Sorry, I missed that. Do you want to save your location in the guide?")
    set_state(NO)
    session.attributes[INSTRUCTION_NUM] = -1
    session.attributes[GUIDE_ID] = -1
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
    if get_state() == NO or get_state() == INSTRUCTIONS:
        save_bookmark()
        session.attributes[INSTRUCTION_NUM] = -1
        session.attributes[GUIDE_ID] = -1
        return statement("Your guide has been bookmarked. Goodbye.")


'''This intent is where we select the bookmark the user said (based on the number), and start reading instructions

Args: bookmark_number. The number spoken by the user, which is the number of the bookmark they would like to select

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
    session.attributes[GUIDE_ID] = int(str(guide_id))
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
    if index < 0 or index >= len(bookmarks):
        return question("Select a valid bookmark").reprompt("Select a valid bookmark")
    return list_bookmarks("Deleted bookmark {}. ".format(index + 1))


'''This function retrieves the bookmarks from the database, and lists them to the user so they can pick one

Returns: Question. Prompts the user to select which item they would like to delete or select, and lists the bookmarks.
'''
def list_bookmarks(prefix = None):
    table = get_database_table()
    user_entry = table.get_item(TableName='Bookmark', Key={'user_id': session['user']['userId']})["Item"]
    output = ""
    num = 1
    for bookmark in user_entry["bookmarks"]:
        output += "{}. Step {} for {}\n".format(num, bookmark["step"] + 1, bookmark["guide_title"])
        num += 1
    response = "Select which bookmark number to resume or delete."
    if prefix != None:
        response = prefix + response

    return question(response).simple_card(title="Bookmarks", content=output).reprompt(
        "Can you repeat that?")


'''This helper function saves the current project to the database so the user can resume their project later
'''
def save_bookmark():
    guide = Guide(session.attributes[GUIDE_ID])
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
        bookmarks = user_entry['Item']['bookmarks']
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
    guides = []
    if get_state() == START or get_state() == None:
        if item is None:
            logger.info("Item is None")
            return no_intent() # Will ask to re-search
        else:
            get_guides(item)
        try:
            guides = session.attributes[GUIDE_ID_LIST]
            guide_names = ""
            i = 1
            for guide in guides:
                g = Guide(guide)
                num = "%i. " % i
                if g and g.title:
                    guide_names = guide_names + num + g.title + "\n"
                    i += 1
        except Exception, e:
            logger.info("Error: " + str(e))
        if i == 1: # ie no valid guide and guide title
            return question("No guides were found for that item. please search again by saying what you want to fix.").reprompt("Please search again.")
        set_state(SEARCH)
        return question("A list of guides has been sent to your device. Please say the number of the guide you want to begin.") \
            .simple_card(title="Guides", content=guide_names).reprompt("Please say the guide number you want begin.")
    else:
        return error_exit()


'''Uses the number to select the guide from the list. Sets this as the current guide and begins reading instructions.

Args: guide_number. The number in the list of guides the user wants to use

Returns: Question. 'You have selected this guide. Say next to begin instructions.'
         Question. 'Please select a valid guide.'
'''
@ask.intent("SelectGuideIntent")
def select_guide(guide_number):
    if get_state() == SEARCH or get_state() == SELECT_GUIDE:
        if guide_number is not int:
            return question("Please say the number next to the guide title on your device. Here is an example. Guide Number One.")
        found = select_guide_index(int(guide_number) - 1)
        set_state(SELECT_GUIDE)
        if found:
            guide = Guide(session.attributes[GUIDE_ID])
            return question("You have selected guide {}. Say next to begin reading instructions.".format(guide.title)).reprompt(
                "Say next to begin reading instructions.")
        return question("Please select a valid guide.").reprompt(
            "Say the number next to the guide title on your device. Here is an example. Guide Number One.")
    else:
        return error_exit()


'''Searches myfixit for guides associated with the search keyword

Args: search_word the word used to search for guides
'''
def get_guides(search_word):
    session.attributes[GUIDE_ID_LIST] = [g.id for g in Category(search_word).guides]


'''Initializes the guide variable based on the given index

Args: index The number of the guide in the list

Returns: True if the guide exists
         False if the index is out of range
'''
def select_guide_index(index):
    guides = session.attributes[GUIDE_ID_LIST]
    if index < 0 or index >= len(guides):
        logger.info("Guide number was not available!")
        return False

    session.attributes[GUIDE_ID] = Guide(guides[index]).id
    session.attributes[INSTRUCTION_NUM] = -1
    return True


'''Gets a list of all of the titles in guides

Returns: A list of the titles (strings) of the guides
'''
def get_guide_titles():
    guides = session.attributes[GUIDE_ID_LIST]
    titles = [Guide(g).title for g in guides]
    return titles


'''Reading Instructions'''

'''Converts the instruction/step into text to be read by Alexa

Args: step the string from the guide for the instruction

Returns: A string that can be read by Alexa
'''
def text_for_step(step):
    step_text = "Step {} ".format(session.attributes[INSTRUCTION_NUM] + 1)
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
    guide = Guide(session.attributes[GUIDE_ID])
    steps = guide.steps
    if instruction_num < 0:
        return question(no_steps)
    if instruction_num > len(steps):
        return question(done_steps).reprompt(done_steps)
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
    guide = Guide(session.attributes[GUIDE_ID])
    steps = guide.steps

    if get_state() == SELECT_GUIDE or get_state() == INSTRUCTIONS:
        set_state(INSTRUCTIONS)
        instruction_num += 1
        if instruction_num < 0:
            return question(no_steps)
        if instruction_num >= len(steps):
            instruction_num -= 1
            session.attributes[INSTRUCTION_NUM] = instruction_num
            return question(done_steps).reprompt(done_steps)
        session.attributes[INSTRUCTION_NUM] = instruction_num
        reply = text_for_step(steps[instruction_num])
        # Currently commented out due to iFixIt Hosing issue: See next_picture_intent()
        '''
        good_images = []
        for image in steps[instruction_num].media:
            if image.original:
                good_images.append(image)
        session.attributes['good_images'] = good_images
        if len(good_images) > 1:
            reply = "I have sent the first of %i images to your Alexa app. To get the next image say next image" \
                    % len(good_images) \
                    + text_for_step(steps[instruction_num])
        elif len(good_images) == 1:
            reply = "I have sent an image associated with this step to your Alexa app." \
                    + text_for_step(steps[instruction_num])
        elif len(good_images) == 0:
            return question(text_for_step(steps[instruction_num])).reprompt("Can you repeat that?")
        '''
        # Add this between question and reprompt
        '''    
        .standard_card(title="Step %i" % (instruction_num + 1),
                                           text="",
                                           small_image_url=good_images[0].original,
                                           large_image_url=good_images[0].original)
        '''

        if reply:
            return question(reply).reprompt("Can you repeat that?")

        else:
            logger.error("good_images was not set correctly!")
    logger.error("State not correct")
    return error_exit()


'''Reads the previous instruction

Returns: Question([instruciton])
'''
@ask.intent("AMAZON.PreviousIntent")
def previous_intent():
    guide = Guide(session.attributes[GUIDE_ID])
    steps = guide.steps
    if get_state() == INSTRUCTIONS:
        instruction_num = session.attributes[INSTRUCTION_NUM]
        instruction_num -= 1
        session.attributes[INSTRUCTION_NUM] = instruction_num
        set_state(INSTRUCTIONS)  # Redundant but it's safer to be explicit
        if instruction_num < 0:
            instruction_num += 1
            session.attributes[INSTRUCTION_NUM] = instruction_num
            return question(no_steps).reprompt(no_steps + " Say next to proceed to the next step.")
        if instruction_num >= len(steps):
            return question(done_steps).reprompt(done_steps)
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
    if get_state() == INSTRUCTIONS or get_state() == SEARCH or get_state() == SELECT_GUIDE:
        if len_guide_number is None:
            guide = Guide(session.attributes[GUIDE_ID])
        elif int(len_guide_number) - 1 >= len(session.attributes[GUIDE_ID_LIST]) or int(len_guide_number) - 1 < 0:
            return question("That was an invalid guide number").reprompt("Please choose a a valid guide number or select a guide.")
        else:
            guide = Guide(session.attributes[GUIDE_ID_LIST][int(len_guide_number) - 1])
        min_length = guide.time_required_min
        max_length = guide.time_required_max
        if min_length == -1 and max_length == -1:
             response = "No time estimate available."
        elif min_length == -1:
            response = "This guide will take " + length_response(max_length) + " to complete."
        elif max_length == -1:
            response = "This guide will take " + length_response(min_length) + " to complete."
        elif max_length == min_length:
            response = "This guide will take " + length_response(max_length) + " to complete."
        else:
            response = "This guide will take bewteen " + length_response(min_length) + " and " + length_response(max_length) + " to complete."

        return question(response).reprompt("Please select a guide or say next to continue instructions.")
    
    setup()
    return question('Please search for guides before asking that. What do you want to fix today?').reprompt(
            "Sorry, I missed that. What do you want to fix today?")


'''Function that creates the string response for the length of guide intent

Args: time which is the time in seconds

Returns: Response string which is the time in hours, minutes, and seconds
'''
def length_response(time):
    minutes, seconds = divmod(time, 60)
    hours, minutes = divmod(minutes, 60)    
    if hours != 0 and minutes != 0 and seconds != 0:
        response = "%i %s %i %s and %i %s" % (hours, "hours" if hours != 1 else "hour",
                                                        minutes, "minutes" if minutes != 1 else "minute",
                                                        seconds, "seconds" if seconds != 1 else "second")
    elif hours != 0 and minutes != 0:
        response = "%i %s and %i %s" % (hours, "hours" if hours != 1 else "hour",
                                                        minutes, "minutes" if minutes != 1 else "minute")
    elif hours != 0 and seconds != 0:
        response = "%i %s and %i %s" % (hours, "hours" if hours != 1 else "hour",
                                                        seconds, "seconds" if seconds != 1 else "second")
    elif minutes != 0 and seconds != 0:
        response = "%i %s and %i %s" % (minutes, "minutes" if minutes != 1 else "minute",
                                                        seconds, "seconds" if seconds != 1 else "second")
    elif hours != 0:
        response = "%i %s" % (hours, "hours" if hours != 1 else "hour")
    elif minutes != 0:
        response = "%i %s" % (minutes, "minutes" if minutes != 1 else "minute")
    else:
        response = "%i %s" % (seconds, "seconds" if seconds != 1 else "second")
    return response


'''Sends a list of tools to the Alexa app if there are any

Returns: Question(There are no tools for this guide)
         Question(I have sent a list of tools to the alexa app [tools])
'''
@ask.intent("ToolsIntent")
def tools_intent(tools_guide_number):
    logger.info(get_state())
    if get_state() == INSTRUCTIONS or get_state() == SEARCH or get_state() == SELECT_GUIDE:
        if tools_guide_number is None or tools_guide_number is not int:
            guide = Guide(session.attributes[GUIDE_ID])
        elif int(tools_guide_number) - 1 >= len(session.attributes[GUIDE_ID_LIST]) or int(tools_guide_number) - 1 < 0:
            return question("That was an invalid guide number").reprompt("Please choose a a valid guide number or select a guide.")
        else:
            guide = Guide(session.attributes[GUIDE_ID_LIST][int(tools_guide_number) - 1])
        if guide.tools is None or len(guide.tools) == 0:
            return question("There are no tools required for this guide.").reprompt(
                "Say next to continue to the next instruction.")
        tools_list = guide.tools
        display_list = ""
        for tool in tools_list:
            if tool["text"]:
                display_list = display_list + "- " + tool["text"] + " (%i)\n" % tool["quantity"]
        return question("I have sent a list of tools you will need to your Alexa app. ").simple_card(title="Tools Required",
                                                                                                    content=display_list) \
            .reprompt("Say next to continue to the next instruction.")
    setup()
    return question('Please search for guides before asking that. What do you want to fix today?').reprompt(
            "Sorry, I missed that. What do you want to fix today?")


'''Tells the user the total number of instructions in the current guide

Returns: Question(The number of instructions in this guide is [number of steps])
'''
@ask.intent("NumberInstructionsIntent")
def num_instructions_intent():
    if get_state() == INSTRUCTIONS or get_state() == SEARCH or get_state() == SELECT_GUIDE:
        guide = Guide(session.attributes[GUIDE_ID])
        steps = guide.steps
        return question("There are %i instructions in this guide. " % len(steps)).reprompt(
            "Say next to continue to the instructions.")
    setup()
    return question('Please search for guides before asking that. What do you want to fix today?').reprompt(
            "Sorry, I missed that. What do you want to fix today?")

'''Tells the user the number of the current instruction

Returns: Question(You have not started any instructions yet)
         Question(The current instruction number is [instruction number])
'''
@ask.intent("CurrentInstructionIntent")
def cur_instruction_intent():
    if get_state() == INSTRUCTIONS or get_state() == SEARCH or get_state() == SELECT_GUIDE:
        num = session.attributes[INSTRUCTION_NUM]
        num = num + 1
        if num <= 0:
            return question("You have not started any instructions yet. Say next to go to the first instruction.").reprompt(
                "Say next to continue to the instructions.")
        return question("You are on instruction number %i. " % num).reprompt(
            "Say next to go to the next step.")
    setup()
    return question('Please search for guides before asking that. What do you want to fix today?').reprompt(
            "Sorry, I missed that. What do you want to fix today?")


'''Tells the user the number of instructions remaining in the guide

Returns: Question(The number of instructions left in this guide is [number of instructions left])
'''
@ask.intent("InstructionsLeftIntent")
def instructions_left_intent():
    if get_state() == INSTRUCTIONS or get_state() == SEARCH or get_state() == SELECT_GUIDE:
        guide = Guide(session.attributes[GUIDE_ID])
        steps = guide.steps
        instructions_left = len(steps) - session.attributes[INSTRUCTION_NUM] - 1
        return question("There are %i instructions left in this guide. " % instructions_left).reprompt(
            "Say next to go to the next step.")
    setup()
    return question('Please search for guides before asking that. What do you want to fix today?').reprompt(
            "Sorry, I missed that. What do you want to fix today?")

'''Tells the user the difficulty of the instruction guide

Returns: Question(The difficulty of this guide is [difficulty])
'''
@ask.intent("DifficultyIntent")
def difficulty_intent():
    if get_state() == INSTRUCTIONS or get_state() == SEARCH or get_state() == SELECT_GUIDE:
        guide = Guide(session.attributes[GUIDE_ID])
        return question("The difficulty of the guide is " + guide.difficulty).reprompt(
            "Say next to continue to the instructions.")
    setup()
    return question('Please search for guides before asking that. What do you want to fix today?').reprompt(
            "Sorry, I missed that. What do you want to fix today?")

'''Sends any pictures associated with the current instruction to the phone

Returns: Question(Image and step)
'''
'''
# Sample Utterances additions: NextPicture Next Picture
# Intent Schema addition: { "intent": "NextPicture"},
# Currently removed Picture due to iFixIt hosting issues: Comment back in when that is fixed
@ask.intent("NextPicture")
def next_picture_intent():
    image_num = session.attributes[IMAGE_NUM]
    instruction_num = session.attributes[INSTRUCTION_NUM]
    good_images = session.attributes['good_images']
    image_num += 1
    session.attributes[IMAGE_NUM] = image_num
    if image_num >= len(good_images):
        return question("There are no more images for this step.")
    image = good_images[image_num]
    text = ": Image {} of {}".format(image_num + 1, len(good_images))
    return question(text).standard_card(title="Step %i" % (instruction_num + 1) + text,
                                               text="",
                                               small_image_url=image.original,
                                               large_image_url=image.original).reprompt("I didn't catch that. "
                                                                       "Can you please repeat what you said?")
    
'''


'''Informs the user of any flags associated with a guide

Returns: question(The flags for this guide are)
         question(There are no flags for this guide)
'''
@ask.intent("FlagsIntent")
def flags_intent():
    if get_state() == INSTRUCTIONS or get_state() == SEARCH or get_state() == SELECT_GUIDE:
        guide = None
        if session.attributes[GUIDE_ID] != -1:
            guide = Guide(session.attributes[GUIDE_ID])

        if guide:
            statement = "The flags for this guide are"
            for flag in guide.flags:
                statement += ", " + flag.title
        else:
            statement = "You have not selected a guide, so I cannot tell you the flags."
        return question(statement)
    setup()
    return question('Please search for guides before asking that. What do you want to fix today?').reprompt(
            "Sorry, I missed that. What do you want to fix today?")

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
    return statement("There was an error.")


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
    current_state = get_state()
    response = 'You are using the My Fix It skill'
    if current_state == HELP:
        response = "I'm sorry, I don't know how to help you get help."
    elif current_state == START:
        response = "Please tell me what you would like to fix today, and I will guide you through the process."
    elif current_state == SEARCH:
        response = "I sent a list of guides to your phone, please tell me the number of the guide you would like to complete."
    elif current_state == SELECT_GUIDE:
        response == "Please say next if you have selected a valid guide."
    return question(response).reprompt("I don't understand. Can you repeat that?")


if __name__ == '__main__':
    app.run()
