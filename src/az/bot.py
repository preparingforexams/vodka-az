import logging
import signal
from typing import Any

import httpx
from openai import AsyncOpenAI
from telegram import Bot, Update, User
from telegram.ext import Application, CommandHandler

from az.config import Config

_SYSTEM_PROMPT = """
Du bist ein Assistent, der Nutzern bei der Getränkeauswahl hilft, indem du einen
außergewöhnlichen Drink vorschlägst. Das Getränk sollte immer ein Longdrink
auf Vodkabasis mit zwei Zutaten sein. Benenne den Drink nach dem Schema
"Vodka-<Buchstabe>", also Vodka-E, Vodka-A, Vodka-T, etc.

Bevorzuge ungewöhnliche Zutaten! Solange es essbar bzw. trinkbar ist, ist es ein guter
Vorschlag!

Gute Beispiele:
- Vodka-O: Vodka mit Orangensaft
- Vodka-E: Vodka mit Eistee
- Vodka-G: Vodka mit Gurkenwasser
- Vodka-K: Vodka mit Kaffee
- Vodka-Z: Vodka mit Zucker
- Vodka-C: Vodka mit Cranberrysaft
- Vodka-S: Vodka mit Sekt
- Vodka-K: Vodka mit Kiwisaft
- Vodka-M: Vodka mit Minze
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
- Vodka-B: Vodka mit Blaubeersaft
- Vodka-J: Vodka mit Johannisbeersaft
- Vodka-H: Vodka mit Honig
- Vodka-Q: Vodka mit Quittensaft
- Vodka-X: Vodka mit Xylit
"""

_USER_PROMPT = """
Schlag mir einen Drink vor, und fass dich kurz.
"""

_LOG = logging.getLogger(__name__)


class AzBot:
    def __init__(self, config: Config):
        self.config = config
        self.http_client = httpx.AsyncClient(timeout=20)
        self.open_ai = AsyncOpenAI(
            api_key=config.openai.token,
            http_client=self.http_client,
        )

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

    async def _post_init(
        self,
        app: Application,  # type: ignore[type-arg]
    ) -> None:
        bot: Bot = app.bot
        bot_user: User = bot.bot
        _LOG.info(
            "Initialized as bot %s (%s)",
            bot_user.first_name,
            bot_user.username,
        )

    def run(self) -> None:
        app = (
            Application.builder()
            .token(self.config.telegram.token)
            .post_init(self._post_init)
            .build()
        )
        app.add_handler(CommandHandler("suggestion", self._suggest))
        app.run_polling(
            read_timeout=5,
            stop_signals=[signal.SIGTERM, signal.SIGINT],
        )

    async def _suggest_drink(self) -> str:
        response = await self.open_ai.chat.completions.create(
            model="gpt-4o-2024-08-06",
            max_tokens=100,
            temperature=1.5,
            messages=[
                dict(role="system", content=_SYSTEM_PROMPT),
                dict(role="user", content=_USER_PROMPT),
            ],
        )

        result = response.choices[0].message.content

        if not result:
            raise ValueError("Received empty message as response")

        _LOG.debug("Received suggestion: %s", result)
        return result

    async def _create_image(self, drink: str) -> bytes:
        prompt_response = await self.open_ai.images.generate(
            model="dall-e-3",
            prompt=f"Ein Longdrink: {drink}",
            n=1,
            size="1024x1024",
            response_format="url",
        )

        url = prompt_response.data[0].url

        if not url:
            raise ValueError("Received empty url as response")

        image_response = await self.http_client.get(httpx.URL(url), timeout=60)
        return await image_response.aread()
