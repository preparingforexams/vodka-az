from dataclasses import dataclass
from typing import Self

from bs_config import Env


@dataclass
class OpenAiConfig:
    token: str

    @classmethod
    def from_env(cls, env: Env) -> Self:
        token = env.get_string("OPENAI_TOKEN")

        if not token:
            raise ValueError("No OpenAI token")

        return cls(
            token=token,
        )


@dataclass
class SentryConfig:
    dsn: str
    release: str

    @classmethod
    def from_env(cls, env: Env) -> Self | None:
        dsn = env.get_string("SENTRY_DSN")

        if not dsn:
            return None

        return cls(
            dsn=dsn,
            release=env.get_string("APP_VERSION", default="debug"),
        )


@dataclass
class TelegramConfig:
    token: str
    polling_timeout: int

    @classmethod
    def from_env(cls, env: Env) -> Self:
        token = env.get_string("TELEGRAM_TOKEN")
        if token is None:
            raise ValueError("No Telegram token")

        return cls(
            token=token,
            polling_timeout=env.get_int("TELEGRAM_POLLING_TIMEOUT", default=10),
        )


@dataclass
class Config:
    openai: OpenAiConfig
    sentry: SentryConfig | None
    telegram: TelegramConfig

    @classmethod
    def from_env(cls, env: Env) -> Self:
        return cls(
            openai=OpenAiConfig.from_env(env),
            sentry=SentryConfig.from_env(env),
            telegram=TelegramConfig.from_env(env),
        )
