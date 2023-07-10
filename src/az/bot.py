import logging
from enum import Enum
from typing import Any, TypedDict

import aiohttp
import openai
from telegram import Update
from telegram.error import TimedOut
from telegram.ext import Application, CommandHandler

from az.config import Config


class Role(str, Enum):
    USER = "user"
    SYSTEM = "system"


class Message(TypedDict):
    role: Role
    content: str


_PROMPT = """
Schlage einen Vodka-Cocktail mit zwei Zutaten vor, benenne ihn nach dem Schema Vodka-<name>.
Bevorzuge ungewöhnliche Zutaten! Solange es essbar bzw. trinkbar ist, ist es ein guter
Vorschlag!

Eine Liste von Beispielen:
- Vodka-O: Vodka mit Orangensaft
- Vodka-E: Vodka mit Eistee
- Vodka-G: Vodka mit Gurkenwasser
- Vodka-K: Vodka mit Kaffee-Likör
- Vodka-Z: Vodka mit Zucker
- Vodka-C: Vodka mit Cranberrysaft
- Vodka-S: Vodka mit Sekt
- Vodka-K: Vodka mit Kiwisaft
- Vodka-M: Vodka mit Minzlikör
- Vodka-P: Vodka mit Pinienkernen
- Vodka-P: Vodka mit Pfirsichsaft
- Vodka-L: Vodka mit Limonade
- Vodka-Z: Vodka mit Zucker
- Vodka-C: Vodka mit Cranberrysaft
- Vodka-L: Vodka mit Litschi
- Vodka-Z: Vodka mit Zimt
- Vodka-W: Vodka mit Wassermelone
- Vodka-M: Vodka mit Mangosaft
- Vodka-M: Vodka mit Maracujasaft
- Vodka-A: Vodka mit Apfelsaft
- Vodka-A: Vodka mit Ananassaft
- Vodka-T: Vodka mit Tomatensaft
- Vodka-R: Vodka mit Rosmarinsirup
- Vodka-B: Vodka mit Blaubeerlikör
- Vodka-J: Vodka mit Johannisbeersaft
- Vodka-H: Vodka mit Honig
"""

_LOG = logging.getLogger(__name__)


class AzBot:
    def __init__(self, config: Config):
        self.config = config

    async def _suggest(self, update: Update, _: Any) -> None:
        message = update.message

        if message is None:
            _LOG.warning("Stupid sexy filters")
            return

        _LOG.info("Received /suggestion command. Generating...")

        drink = await self._suggest_drink()
        image = await self._create_image(drink)
        await message.reply_photo(
            photo=image,
            caption=drink,
        )

    def run(self) -> None:
        app = (
            Application.builder()
            .token(self.config.telegram.token)
            .get_updates_http_version("1.1")
            .http_version("1.1")
            .build()
        )
        app.add_handler(CommandHandler("suggestion", self._suggest))

        retry = True
        while retry:
            retry = False
            try:
                app.run_polling(read_timeout=5)
            except TimedOut:
                retry = True

    async def _suggest_drink(self) -> str:
        response = await openai.ChatCompletion.acreate(  # type: ignore
            model="gpt-3.5-turbo",
            max_tokens=75,
            messages=[
                Message(role=Role.USER, content=_PROMPT),
            ],
        )

        return response.choices[0].message.content

    async def _create_image(self, drink: str) -> bytes:
        response = await openai.Image.acreate(  # type: ignore
            prompt=drink,
            n=1,
            size="1024x1024",
            response_format="url",
        )

        url = response["data"][0]["url"]

        async with aiohttp.ClientSession() as session:
            response = await session.get(url, timeout=20)
            return await response.read()
