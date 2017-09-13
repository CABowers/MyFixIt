from alexafsm.states import with_transitions, States as StatesBase
from alexafsm import response
from alexafsm import amazon_intent
from flask_ask import question, statement


def guide_length():
    return ("Here is the length of your instruction guide")

class States(StatesBase):
    def help(self):
        return question("What do you need help with?")

    def start(self):
        return question("Welcome to Alexa?")

    def search(self):
        return question("What do you want to search for")

    def search_results(self):
        return question("Here are your search results")

    def instruction(self):
        return question("Here is the next instruction")

    def goodbye(self):
        return statement("Goodbye")