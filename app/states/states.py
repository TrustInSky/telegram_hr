from aiogram.fsm.state import State, StatesGroup

class AnonymousQuestionStates(StatesGroup):
    waiting_for_text = State()
    confirmation = State()


class CatalogStates(StatesGroup):
    waiting_for_excel = State()