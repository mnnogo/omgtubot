class ParseError(Exception):
    def __init__(self, message="Ошибка при парсинге информации"):
        self.message = message
        super().__init__(self.message)


class ZeroArguementsError(Exception):
    def __init__(self, message="Должен быть передан хотя бы один параметр"):
        self.message = message
        super().__init__(self.message)
