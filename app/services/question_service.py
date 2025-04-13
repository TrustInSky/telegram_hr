
from app.database.models import AnonymousQuestion
from app.repositories.anon_question_repo import AnonymousQuestionRepo

class AnonymousQuestionService:
    def __init__(self, repo: AnonymousQuestionRepo):
        self.repo = repo

    async def create_question(self, text: str) -> AnonymousQuestion:
        question = AnonymousQuestion(question_text=text)
        saved_question = await self.repo.save(question)
        return saved_question
    
    