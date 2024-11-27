from datetime import datetime

from classes.FileInfo import FileInfo


class TaskInfo:
    def __init__(self, subject: str, comment: str, files_info: list[FileInfo], upload_date: datetime, teacher: str):
        self.subject = subject
        self.comment = comment
        self.files_info = files_info
        self.upload_date = upload_date
        self.teacher = teacher

    def __eq__(self, other):
        return self.subject == other.subject \
            and self.comment == other.comment \
            and self.files_info == other.files_info \
            and self.upload_date == other.upload_date \
            and self.teacher == other.teacher

    def __str__(self):
        return f'{self.subject}, {self.comment}, {self.files_info}, {self.upload_date}, {self.teacher}'
