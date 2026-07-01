from enum import Enum


class ProjectRole(str, Enum):
    OWNER = "Owner"
    PARTICIPANT = "Participant"
