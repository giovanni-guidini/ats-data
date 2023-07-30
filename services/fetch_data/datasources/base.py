from typing import Callable, Coroutine, TypeVar

Datasource = TypeVar("Datasource")


class BaseDatasource(object):
    def __init__(self, config: dict = None) -> None:
        if config is None:
            config = {}
        config = config
