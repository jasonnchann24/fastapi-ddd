import punq
from .repositories import UserRepository
from .services import UserService


def register(container: punq.Container):
    container.register(UserRepository)
    container.register(UserService)
