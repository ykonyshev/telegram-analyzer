
from telethon import types


def format_user(user: types.User) -> str:
    def add_id(part: str):
        return f'{part} <{user.id}>'

    if user.username is not None:
        return add_id(user.username)
    elif user.first_name is not None:
        return add_id(user.first_name)

    return str(user.id)
