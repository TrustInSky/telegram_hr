from sqlalchemy import insert,select, func
from app.database.models import AnonymousQuestion

class AnonymousQuestionRepo:
    def __init__(self, session):
        self.session = session

    async def save(self, question: AnonymousQuestion):
        self.session.add(question)
        await self.session.commit()
        await self.session.refresh(question)
        return question
    
    async def get_next_unread(self) -> AnonymousQuestion | None:
        stmt = (
            select(AnonymousQuestion)
            .where(AnonymousQuestion.question_status.is_(None))
            .order_by(AnonymousQuestion.submitted_at.asc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_status(self, question_id: int, status: str):
        stmt = (
            select(AnonymousQuestion)
            .where(AnonymousQuestion.id == question_id)
        )
        result = await self.session.execute(stmt)
        question = result.scalar_one_or_none()
        if question:
            question.question_status = status
            await self.session.commit()
            
    async def get_all_questions(self) -> list[AnonymousQuestion]:
        stmt = select(AnonymousQuestion).order_by(AnonymousQuestion.submitted_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()    