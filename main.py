import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()  # Tải biến môi trường từ file .env
token = os.getenv('TOKEN')

# Khởi tạo bot với prefix '!'
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Sự kiện khi bot sẵn sàng
@bot.event
async def on_ready():
    print(f'Bot đã đăng nhập với tên {bot.user}!')

# Load tất cả các lệnh từ thư mục commands
async def load_extensions():
    for filename in os.listdir('commands'):
        if filename.endswith('.py') and filename != '__init__.py':
            try:
                await bot.load_extension(f'commands.{filename[:-3]}')
                print(f'Loaded extension: commands.{filename[:-3]}')
            except Exception as e:
                print(f'Failed to load extension commands.{filename[:-3]}: {str(e)}')

# Hàm chính để chạy bot
async def main():
    async with bot:
        await load_extensions()
        await bot.start(token)

# Chạy bot
if __name__ == '__main__':
    asyncio.run(main())