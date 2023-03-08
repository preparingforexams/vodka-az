import logging
from typing import Any

import aiohttp
import openai
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

from az.config import Config

_PROMPT = """
Schlage einen Vodka-Cocktail mit zwei Zutaten vor, benenne ihn nach dem Schema Vodka-<name>.

Beispiele:
- Vodka-O: Vodka mit Orangensaft
- Vodka-G: Vodka mit Gurkenwasser
- Vodka-K: Vodka mit Kaffee-Likör
- Vodka-Z: Vodka mit Zucker
- Vodka-M: Vodka mit Minzlikör

Vorschlag:"""

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
        app = Application.builder().token(self.config.telegram.token).build()
        app.add_handler(CommandHandler("suggestion", self._suggest))
        app.run_polling()

    async def _suggest_drink(self) -> str:
        response = await openai.Completion.acreate(  # type: ignore
            model="text-davinci-003",
            prompt=_PROMPT,
            temperature=1,
            max_tokens=75,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )
        return response.choices[0].text

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
