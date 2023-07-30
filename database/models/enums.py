from enum import Enum


class GitProviders(Enum):
    github = "gh"
    gitlab = "gl"
    bitbucket = "bb"


class CiProviders(Enum):
    circleci = "circleci"
