from pydantic import BaseModel, Field
from typing import Optional

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
    
    family_support_comment: Optional[str] = Field(None)
    optimism_comment: Optional[str] = Field(None)
    coping_comment: Optional[str] = Field(None)
    social_connections_comment: Optional[str] = Field(None)
    health_comment: Optional[str] = Field(None)
    
    time_taken_seconds: int = Field(...)
    
    teacher_comment: Optional[str] = Field(None, description="Текстовий коментар вчителя")