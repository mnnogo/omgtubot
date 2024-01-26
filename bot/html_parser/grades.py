import re
import requests
from GradeInfo import *
from bs4 import BeautifulSoup
from logger import logging


# конфигурация логгинга
logging = logging.getLogger(__name__)


def get_student_grades(session: requests.Session) -> list[GradeInfo]:
    r"""Returns :class:`GradeInfo` list of ALL current grades from site

    :param session: :class:`Session` object with authorized user"""
    student_grades = []



    return student_grades
