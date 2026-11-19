"""
Plain Data Models (DTOs - Data Transfer Objects)
Built with Python's standard library dataclasses.
Pure Non-ORM architecture: No SQLAlchemy, no ORM generators, no database coupling.
"""

from dataclasses import dataclass, asdict
from datetime import date, datetime
from typing import Optional

@dataclass
class Student:
    student_id: str
    full_name: str
    grade: int
    date_of_birth: date
    gender: str
    email: str
    parent_name: Optional[str] = None
    parent_phone: Optional[str] = None
    status: str = "Active"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_row(cls, row):
        """Constructs a Student instance from a database dictionary row."""
        if not row:
            return None
        d = dict(row)
        return cls(
            student_id=d.get("student_id", ""),
            full_name=d.get("full_name", ""),
            grade=int(d.get("grade", 1)),
            date_of_birth=d.get("date_of_birth"),
            gender=d.get("gender", "Male"),
            email=d.get("email", ""),
            parent_name=d.get("parent_name"),
            parent_phone=d.get("parent_phone"),
            status=d.get("status", "Active"),
            created_at=d.get("created_at"),
            updated_at=d.get("updated_at"),
        )

    def to_dict(self):
        """Serializes the student data object to a clean dictionary."""
        d = asdict(self)
        if isinstance(d.get("date_of_birth"), (date, datetime)):
            d["date_of_birth"] = d["date_of_birth"].strftime("%Y-%m-%d")
        if isinstance(d.get("created_at"), (date, datetime)):
            d["created_at"] = d["created_at"].strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(d.get("updated_at"), (date, datetime)):
            d["updated_at"] = d["updated_at"].strftime("%Y-%m-%d %H:%M:%S")
        return d


@dataclass
class Teacher:
    teacher_id: str
    full_name: str
    email: Optional[str] = None

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        d = dict(row)
        return cls(
            teacher_id=d.get("teacher_id", ""),
            full_name=d.get("full_name", ""),
            email=d.get("email"),
        )

    def to_dict(self):
        return asdict(self)


@dataclass
class Course:
    course_code: str
    title: str
    grade_level: int
    capacity: int
    teacher_id: Optional[str] = None

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        d = dict(row)
        return cls(
            course_code=d.get("course_code", ""),
            title=d.get("title", ""),
            grade_level=int(d.get("grade_level", 1)),
            capacity=int(d.get("capacity", 30)),
            teacher_id=d.get("teacher_id"),
        )

    def to_dict(self):
        return asdict(self)


@dataclass
class Enrollment:
    student_id: str
    course_code: str
    enrollment_id: Optional[int] = None
    term: Optional[str] = None

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        d = dict(row)
        return cls(
            enrollment_id=d.get("enrollment_id"),
            student_id=d.get("student_id", ""),
            course_code=d.get("course_code", ""),
            term=d.get("term"),
        )

    def to_dict(self):
        return asdict(self)
