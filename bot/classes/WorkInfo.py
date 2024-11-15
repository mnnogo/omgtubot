from enum import Enum


class WorkStatus(Enum):
    PENDING = 0
    ACCEPTED = 1
    DECLINED = 2

    def __str__(self):
        return f'{"работа принята ✅" if self == WorkStatus.ACCEPTED else
                  "работа отклонена ❌" if self == WorkStatus.DECLINED else
                  "работа не посмотрена 📋"}'


class WorkInfo:
    def __init__(self, work_name: str, subject: str, status: WorkStatus):
        self.work_name = work_name
        self.subject = subject
        self.status = status

    def __eq__(self, other):
        return self.work_name == other.work_name \
            and self.subject == other.subject \
            and self.status == other.status

    def __str__(self):
        return f'{self.work_name}, {self.subject}, {self.status}'
