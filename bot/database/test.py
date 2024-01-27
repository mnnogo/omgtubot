import unittest

import database.get


class MyTestCase(unittest.TestCase):
    def test_something(self):
        works = database.get.get_student_works(user_id=1876123382)
        for work in works:
            print(work)


if __name__ == '__main__':
    unittest.main()
