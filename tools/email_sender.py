#!/usr/bin/env python3
"""
Provider-agnostic email sending interface.

To add a new provider (e.g. SendGrid), implement send_newsletter() in
tools/send_via_sendgrid.py and import it instead of send_via_gmail in the workflow.
"""

from typing import Protocol


class Subscriber:
    def __init__(self, email: str, name: str):
        self.email = email
        self.name = name


class EmailProvider(Protocol):
    def send_newsletter(
        self,
        html_path: str,
        plain_path: str,
        subject: str,
        subscribers: list[Subscriber],
    ) -> dict:
        """
        Send the newsletter to a list of subscribers.
        Returns: {"sent": int, "failed": list[str]}
        """
        ...
