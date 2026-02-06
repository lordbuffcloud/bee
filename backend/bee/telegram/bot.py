import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from bee.state import BEEState


class TelegramBot:
    def __init__(self, token: str, state: BEEState) -> None:
        self.bot = Bot(token=token)
        self.dp = Dispatcher()
        self.state = state
        self._wire_handlers()

    def _wire_handlers(self) -> None:
        @self.dp.message(CommandStart())
        async def start(message: Message) -> None:
            await message.answer("B.E.E. online. Use /status to check heartbeat and goals.")

        @self.dp.message(F.text == "/status")
        async def status(message: Message) -> None:
            goals = ", ".join(self.state.memory_goals.goals) or "none"
            await message.answer(f"Heartbeat: {self.state.heartbeat_running}. Goals: {goals}.")

    async def run(self) -> None:
        await self.dp.start_polling(self.bot)

    def run_in_background(self) -> asyncio.Task:
        return asyncio.create_task(self.run())
