import logging
from datetime import datetime


class TaskInfo:
    def __init__(self, subject: str, comment: str, file_url: str | None, upload_date: datetime, teacher: str):
        self.subject = subject
        self.comment = comment
        self.file_url = file_url
        self.upload_date = upload_date
        self.teacher = teacher

    def __eq__(self, other):
        return self.subject == other.subject \
            and self.comment == other.comment \
            and self.file_url == other.file_url \
            and self.upload_date == other.upload_date \
            and self.teacher == other.teacher

    def __hash__(self):
        return hash((self.subject, self.comment, self.file_url, self.upload_date, self.teacher))

    def __str__(self):
        return f'{self.subject}, {self.comment}, {self.file_url}, {self.upload_date}, {self.teacher}'
