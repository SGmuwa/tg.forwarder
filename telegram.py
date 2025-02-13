#!/usr/bin/env python3

from telethon import TelegramClient, events
import telethon
import telethon.requestiter
from telethon.sessions import StringSession
from loguru import logger
from os import environ, remove
import re
from json5 import load, loads

logger.trace("application started.")

class Settings:
    def __init__(
        self,
        secret_path = environ.get("TELEGRAM_SECRET_PATH", "./secret.json5"),
        content = environ.get("TELEGRAM_SECRET", None)
    ):
        if content:
            logger.debug("use secret environment")
            self.json = loads(content)
        else:
            logger.debug("use secret file")
            with open(secret_path) as f:
                self.json = load(f)
            try:
                remove(secret_path)
            except Exception as e:
                logger.warning("Can't remove secret file, error: «{}»", e)
        self._is_session_and_auth_key_configurated = None

    @property
    def session_and_auth_key(self) -> str:
        output = self.json.pop("session_and_auth_key", None)
        if self._is_session_and_auth_key_configurated is None:
            if output:
                self._is_session_and_auth_key_configurated = True
            else:
                self._is_session_and_auth_key_configurated = False
        return output

    @property
    def is_session_and_auth_key_configurated(self) -> str:
        if self._is_session_and_auth_key_configurated is None:
            return "session_and_auth_key" in self.json
        else:
            return self._is_session_and_auth_key_configurated

    @property
    def api_id(self) -> int:
        return self.json.pop("api_id", 1)

    @property
    def api_hash(self) -> str:
        return self.json.pop("api_hash", "0")

    @property
    def bot_token(self) -> str:
        return self.json.pop("bot_token")

    @property
    def target_chat(self) -> int:
        return self.json["target_chat"]

    @property
    def source_chat(self) -> int:
        return self.json["source_chat"]

    @property
    def search_only_regex(self) -> int:
        return self.json["search_only_regex"]


settings = Settings()

searcher_targets = re.compile(settings.search_only_regex)

logger.trace("Init TelegramClient...")
with TelegramClient(
    StringSession(settings.session_and_auth_key),
    settings.api_id,
    settings.api_hash,
    base_logger=logger
).start() as client:
    client: TelegramClient = client
    logger.trace("Telegram client instance created")
    if not settings.is_session_and_auth_key_configurated:
        raise Exception(f"Use session, instead of api_id and api_hash. Set session_and_auth_key to value: «{client.session.save()}»")

    def split_str_by_length(s: str, chunk_limit: int):
        return [s[i:i+chunk_limit] for i in range(0, len(s), chunk_limit)]
    
    async def send_to_future(peer_id, msg, **kwargs) -> list[telethon.types.Message]:
        logger.trace("send_to_future: begin")
        logger.trace("Ready to send {} KiB", len(msg) / 1024)
        sendent = []
        if msg:
            logger.trace(f"ready chars {len(msg)}")
            msgs = split_str_by_length(msg, 4096)
            logger.trace(f"splitted! count: {len(msgs)}")
            logger.trace("Sending...")
            for m in msgs:
                sendent.append(await client.send_message(peer_id, m, **kwargs))
            logger.trace("Sent.")
        logger.trace("sendent: {sendent}", sendent=sendent)
        return sendent
    
    async def getLinkOfMessage(message: telethon.tl.patched.Message):
        chat: telethon.types.Chat = await message.get_chat()
        if chat.username:
            return f"https://t.me/{chat.username}/{message.id}"
        else:
            return f"https://t.me/c/{chat.id}/{message.id}"
    
    async def alert(event: telethon.events.newmessage.NewMessage.Event):
        message: telethon.tl.patched.Message = event.message
        if (await client.get_me()).id == message.sender_id:
            logger.warning(f"Sender is me! Skip: {message.message}")
            return
        matcher = searcher_targets.search(message.message)
        if matcher == None:
            logger.debug("no target message {}", message)
        else:
            try:
                await client.forward_messages(settings.target_chat, message)
            except ValueError as e:
                if "Could not find the input entity for" in e.args[0]:
                    await client.get_dialogs()
                    await client.forward_messages(settings.target_chat, message)
                else:
                    raise

    @client.on(events.NewMessage(chats=settings.source_chat))
    async def handler(event: telethon.events.newmessage.NewMessage.Event):
        try:
            message: telethon.tl.patched.Message = event.message
            logger.info("got message {}: {}", message.peer_id, message.message)
            await alert(event)
        except Exception as e:
            logger.exception(e)
    logger.info("Telegram ready")
    client.run_until_disconnected()
