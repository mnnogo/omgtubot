class FileInfo:
    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url

    def __eq__(self, other):
        return self.name == other.name \
            and self.url == other.url

    def __str__(self):
        return f'{self.name}, {self.url}'

    def to_dict(self):
        return {"name": self.name, "url": self.url}
