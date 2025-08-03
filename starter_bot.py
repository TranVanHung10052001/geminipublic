import os
import requests
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Lấy các biến từ môi trường của Render
STARTER_BOT_TOKEN = os.environ.get('STARTER_BOT_TOKEN')
# URL Colab đặc biệt được cung cấp trên Render
ASSISTANT_NOTEBOOK_URL = os.environ.get('ASSISTANT_NOTEBOOK_URL') 
# ID của người dùng được phép ra lệnh (là bạn)
ADMIN_USER_ID = int(os.environ.get('ADMIN_USER_ID'))

async def wakeup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý lệnh /wakeup và gửi link khởi động."""
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("Bạn không có quyền thực hiện lệnh này.")
        return

    await update.message.reply_text(
        "Đây là link khởi động tự động của bạn.\n\n"
        "1. Nhấp vào link dưới đây.\n"
        "2. Colab sẽ mở ra, hãy vào menu 'Runtime' -> 'Run all'.\n\n"
        f"{ASSISTANT_NOTEBOOK_URL}"
    )

def main() -> None:
    """Chạy bot trực ban."""
    print("Bot trực ban 24/7 đang hoạt động...")
    application = Application.builder().token(STARTER_BOT_TOKEN).build()
    application.add_handler(CommandHandler("wakeup", wakeup))
    application.run_polling()

if __name__ == "__main__":
    main()