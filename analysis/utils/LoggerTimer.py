from time import perf_counter

from analysis.logging import get_logger


class LoggerTimer():
    def __init__(
        self,
        message: str,
        *formattings: object,
        **additional: object
    ) -> None:
        self.message = message
        self.formattings = formattings
        self.additional = additional
        self.logger = get_logger(__name__)


    def __enter__(self) -> "LoggerTimer":
        self.start = perf_counter()
        return self


    def __exit__(self, *_) -> None:
        diff = perf_counter() - self.start

        # * Convert all lists into ", " separated strings
        for key, value in self.additional.items():
            if isinstance(value, list):
                self.additional[key] = ', '.join(map(str, value))

        new_formatting = []
        for item in self.formattings:
            if isinstance(item, list):
                new_formatting.append(', '.join(map(str, item)))
                continue

            new_formatting.append(item)

        message = self.message.format(diff, *self.formattings, **self.additional)
        self.logger.info(message)
