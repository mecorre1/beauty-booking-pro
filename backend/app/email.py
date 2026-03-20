"""Email sending abstraction (SPEC: confirmation email on booking)."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class EmailSender(Protocol):
    def send(self, to: str, subject: str, body: str) -> None: ...


class LoggingEmailSender:
    """Dev/test: record last message; optional print."""

    def __init__(self, *, also_print: bool = True) -> None:
        self.also_print = also_print
        self.last_to: str | None = None
        self.last_subject: str | None = None
        self.last_body: str | None = None

    def send(self, to: str, subject: str, body: str) -> None:
        self.last_to = to
        self.last_subject = subject
        self.last_body = body
        if self.also_print:
            print(f"[email] to={to} subject={subject!r}")  # noqa: T201


class NoOpEmailSender:
    def send(self, to: str, subject: str, body: str) -> None:
        pass


# Swappable in tests via assignment.
default_email_sender: EmailSender = LoggingEmailSender(also_print=False)
