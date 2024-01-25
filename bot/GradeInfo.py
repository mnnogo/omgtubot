from enum import Enum


class Grade(Enum):
    NA = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    PASSED = 6
    FAILED = 7

    def __str__(self):
        return f"{'нет оценки' if self == Grade.NA else
                  '🟥 Неудовлетворительно' if self == Grade.TWO else 
                  '🟨 Удовлетворительно' if self == Grade.THREE else
                  '🟦 Хорошо' if self == Grade.FOUR else
                  '🟩 Отлично' if self == Grade.FIVE else
                  '🟩 Зачтено' if self == Grade.PASSED else
                  '🟥 Не зачтено'}"


class GradeInfo:
    def __init__(self, subject: str, term: int, grade: Grade):
        self.subject = subject
        self.term = term
        self.grade = grade

    def __eq__(self, other):
        return self.subject == other.subject \
            and self.term == other.term \
            and self.grade == other.grade

    def __str__(self):
        return f'{self.subject}, {self.term}, {self.grade}'
