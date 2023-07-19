import typing
from abc import ABC

from py4web.core import Fixture


class TypedFixture(Fixture, ABC):  # type: ignore
    def on_request(self, context: dict[str, typing.Any]) -> None:
        super().on_request(context)  # called when a request arrives

    def on_error(self, context: dict[str, typing.Any]) -> None:
        super().on_error(context)  # called when a request errors

    def on_success(self, context: dict[str, typing.Any]) -> None:
        super().on_success(context)  # called when a request is successful
