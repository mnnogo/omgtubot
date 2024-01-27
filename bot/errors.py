class ParseError(Exception):
    def __init__(self, message="Ошибка при парсинге информации"):
        self.message = message
        super().__init__(self.message)
