"""Pydantic schemas for teacher form submissions and feedback validation."""
from typing import List, Optional

from pydantic import BaseModel, Field


class TeacherFormSubmission(BaseModel):
    teacher_id: str = Field(..., description="Унікальний ID вчителя")
    student_id: str = Field(..., description="Анонімний ID учня")
    student_age: int = Field(..., description="Вік учня")
    student_gender: str = Field(..., description="Стать учня")

    family_support_score: Optional[int] = Field(None, ge=0, le=2)
    optimism_score: Optional[int] = Field(None, ge=0, le=2)
    coping_score: Optional[int] = Field(None, ge=0, le=2)
    social_connections_score: Optional[int] = Field(None, ge=0, le=2)
    health_score: Optional[int] = Field(None, ge=0, le=2)
    
    family_support_comments: Optional[List[str]] = Field(default_factory=list)
    optimism_comments: Optional[List[str]] = Field(default_factory=list)
    coping_comments: Optional[List[str]] = Field(default_factory=list)
    social_connections_comments: Optional[List[str]] = Field(default_factory=list)
    health_comments: Optional[List[str]] = Field(default_factory=list)
    
    time_taken_seconds: Optional[int] = Field(None)
    teacher_comment: Optional[str] = Field(None)


class FeedbackSubmission(BaseModel):
    """Pydantic model for 11-block teacher feedback form validation."""

    teacher_id: Optional[str] = None

    # Block 1: Загальна інформація
    experience: Optional[str] = None
    grades: Optional[List[str]] = Field(default_factory=list)
    subject: Optional[str] = None

    # Block 2: Досвід використання
    completed: Optional[str] = None
    students_count: Optional[str] = None
    ease_of_use: Optional[int] = Field(None, ge=1, le=5)

    # Block 3: Прийнятність
    acceptability_1: Optional[int] = Field(None, ge=1, le=5)
    acceptability_2: Optional[int] = Field(None, ge=1, le=5)
    acceptability_3: Optional[int] = Field(None, ge=1, le=5)

    # Block 4: Відповідність
    appropriateness_1: Optional[int] = Field(None, ge=1, le=5)
    appropriateness_2: Optional[int] = Field(None, ge=1, le=5)
    appropriateness_3: Optional[int] = Field(None, ge=1, le=5)

    # Block 5: Здійсненність
    feasibility_1: Optional[int] = Field(None, ge=1, le=5)
    feasibility_2: Optional[int] = Field(None, ge=1, le=5)
    feasibility_3: Optional[int] = Field(None, ge=1, le=5)

    # Block 6: Зручність
    usability_1: Optional[int] = Field(None, ge=1, le=5)
    usability_2: Optional[int] = Field(None, ge=1, le=5)
    usability_3: Optional[int] = Field(None, ge=1, le=5)

    # Block 7: Оцінка ШІ-агента
    llm_1: Optional[int] = Field(None, ge=1, le=5)
    llm_2: Optional[int] = Field(None, ge=1, le=5)
    llm_3: Optional[int] = Field(None, ge=1, le=5)
    llm_4: Optional[int] = Field(None, ge=1, le=5)

    # Block 8: Безпека та етика
    safety_1: Optional[int] = Field(None, ge=1, le=5)
    safety_2: Optional[int] = Field(None, ge=1, le=5)
    safety_3: Optional[int] = Field(None, ge=1, le=5)

    # Block 9: Намір використання
    intention_1: Optional[int] = Field(None, ge=1, le=5)
    intention_2: Optional[int] = Field(None, ge=1, le=5)

    # Block 10: Відкриті питання
    open_1: Optional[str] = None
    open_2: Optional[str] = None
    open_3: Optional[str] = None
    open_4: Optional[str] = None

    # Block 11: Досвід роботи з учнями
    helped_understand: Optional[str] = None
    changes_made: Optional[str] = None
