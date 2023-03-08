import logging

import openai
import sentry_sdk

from az.config import load_env, Config, SentryConfig

_LOG = logging.getLogger(__name__)


def _setup_logging() -> None:
    logging.basicConfig()

    logging.root.level = logging.WARNING
    logging.getLogger(__package__).level = logging.DEBUG


def _setup_sentry(config: SentryConfig | None) -> None:
    if not config:
        _LOG.warning("Sentry not configured")
        return

    sentry_sdk.init(
        dsn=config.dsn,
        release=config.release,
    )


def initialize() -> Config:
    _setup_logging()

    config = Config.from_env(load_env(""))
    _setup_sentry(config.sentry)

    openai.api_key = config.openai.token

    return config
