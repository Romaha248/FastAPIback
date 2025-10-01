from enum import Enum


class TodoCategory(str, Enum):
    WORK = "work"
    PERSONAL = "personal"
    STUDY = "study"
    FITNESS = "fitness"
    SHOPPING = "shopping"
    HEALTH = "health"
    HOBBY = "hobby"
    OTHER = "other"
