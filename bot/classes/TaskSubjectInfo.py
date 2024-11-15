class TaskSubjectInfo:
    def __init__(self, subject: str, subject_url: str):
        self.subject = subject
        self.subject_url = subject_url

    def __str__(self):
        return f'{self.subject}, {self.subject_url}'