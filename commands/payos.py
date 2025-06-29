import discord
from discord.ext import commands, tasks
from payos import PayOS, PaymentData, ItemData
import os, qrcode, io, base64
from dotenv import load_dotenv

load_dotenv()
client_id = os.getenv('PAYOS_CLIENT_ID')
api_key = os.getenv('PAYOS_API_KEY')
checksum_key = os.getenv('PAYOS_CHECKSUM_KEY')
log_channel_id = int(os.getenv('LOG_PAYMENT_CHANNEL_ID', '0'))
delay = int(os.getenv('DELAY', '10'))

# Thêm bảng ánh xạ BIN sang tên ngân hàng
BIN_TO_BANK = {
    "970436": "Vietcombank",
    "970418": "Techcombank",
    "970407": "VietinBank",
    "970405": "BIDV",
    "970422": "MB Bank",
    # Thêm các mã khác nếu cần
}

class Payos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.payOS = PayOS(client_id=client_id, api_key=api_key, checksum_key=checksum_key)
        self.channel_id = log_channel_id
        self.poll_interval = delay
        self.active_orders = set()
        self.order_messages = {}  # Lưu order_code -> (user_msg, log_msg)
        self.check_payments.start()

    def cog_unload(self):
        self.check_payments.cancel()

    @commands.hybrid_command(name="pay", description="Thanh toán qua PayOS.")
    async def pay(self, ctx, mention: discord.Member = None, amount: int = None):
        """Thanh toán qua PayOS."""
        if amount is None or amount <= 0:
            await ctx.send("Vui lòng cung cấp số tiền hợp lệ!")
            return

        # Lấy user mention cho cả prefix và slash
        content = str(mention.id) if mention else str(ctx.author.id)
        # order_code: dùng interaction/message id cho unique
        order_code = int(str(ctx.interaction.id if hasattr(ctx, "interaction") and ctx.interaction else ctx.message.id)[:10])
        item = ItemData(name="Thanh toán qua Discord", quantity=1, price=amount)
        payment_data = PaymentData(
            orderCode=order_code,
            amount=amount,
            description=content,
            items=[item],
            cancelUrl="http://localhost:8000/cancel",
            returnUrl="http://localhost:8000/success"
        )

        try:
            result = self.payOS.createPaymentLink(payment_data)
            info = self.payOS.getPaymentLinkInformation(order_code)

            self.active_orders.add(order_code)

            bank_name = BIN_TO_BANK.get(str(result.bin), f"Mã ngân hàng: {result.bin}")

            embed = discord.Embed(
                title="THANH TOÁN",
                color=discord.Color.blue()
            )
            embed.add_field(name="", value=f"**Ngân hàng**: `{bank_name}`", inline=False)
            embed.add_field(name="Số tài khoản", value=f"```{result.accountNumber}```", inline=False)
            embed.add_field(name="Tên tài khoản", value=f"```{result.accountName}```", inline=False)
            embed.add_field(name="Số tiền", value=f"```{result.amount:,} VNĐ```", inline=False)
            embed.add_field(name="Nội dung", value=f"```{result.description}```", inline=False)
            embed.add_field(name="", value=f"**Link**: [Click here]({result.checkoutUrl})", inline=False)

            # Tạo QR code từ result.qrCode
            if hasattr(result, 'qrCode') and result.qrCode:
                img = qrcode.make(result.qrCode)
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                buf.seek(0)
                # Tùy chọn: Lấy base64 string nếu cần (ví dụ: lưu log)
                base64_string = base64.b64encode(buf.getvalue()).decode('utf-8')
                # Gửi file QR code cho Discord
                file = discord.File(fp=buf, filename="qr.png")
                embed.set_image(url="attachment://qr.png")
            else:
                await ctx.send("Lỗi: Không thể tạo mã QR.")
                return

            embed.add_field(name="", value=f"**Trạng thái**: `{info.status}`", inline=False)
            paid = getattr(info, 'amountPaid', None)
            if paid:
                embed.add_field(name="Đã thanh toán", value=f"`{paid:,}` **VNĐ**", inline=False)
            embed.set_footer(text="🛡️ Quét QR hoặc nhấn link để thanh toán.")

            user_msg = await ctx.send(file=file, embed=embed)

            log_channel = self.bot.get_channel(self.channel_id)
            log_msg = None
            if log_channel:
                # Gửi lại file QR code cho log channel
                buf.seek(0)  # Reset buffer để gửi lại
                log_file = discord.File(fp=buf, filename="qr.png")
                log_msg = await log_channel.send(
                    f"📝 Đơn mới từ **{ctx.author.mention}** (ID: `{order_code}`):",
                    file=log_file,
                    embed=embed
                )

            # Lưu lại message để sau này edit
            self.order_messages[order_code] = (user_msg, log_msg)

        except Exception as e:
            await ctx.send(f"Lỗi khi tạo link thanh toán: {e}")

    @tasks.loop(seconds=delay)
    async def check_payments(self):
        channel = self.bot.get_channel(self.channel_id)
        if channel is None:
            return

        to_remove = []
        for order in list(self.active_orders):
            try:
                info = self.payOS.getPaymentLinkInformation(order)
                msgs = self.order_messages.get(order)
                if not msgs:
                    continue
                user_msg, log_msg = msgs

                for msg in [user_msg, log_msg]:
                    if msg is None or not msg.embeds:
                        continue

                    old_embed = msg.embeds[0]
                    new_embed = old_embed.copy()

                    # Cập nhật trạng thái
                    for idx, field in enumerate(new_embed.fields):
                        if field.name == "Trạng thái" or field.value.startswith("**Trạng thái**:"):
                            state = (
                                "🟢 Đã thanh toán" if info.status == "PAID" else
                                "🔴 Đã hủy" if info.status == "CANCELLED" else
                                "🔴 Hết hạn" if info.status == "EXPIRED" else
                                f"`{info.status}`"
                            )
                            new_embed.set_field_at(idx, name="Trạng thái", value=state, inline=False)
                            break

                    # Nếu trạng thái là PAID, CANCELLED, hoặc EXPIRED, xóa ảnh QR
                    if info.status in ("PAID", "CANCELLED", "EXPIRED"):
                        new_embed.set_image(url=None)
                        try:
                            await msg.edit(embed=new_embed, attachments=[])
                        except TypeError:
                            await msg.edit(embed=new_embed)
                    else:
                        try:
                            await msg.edit(embed=new_embed, attachments=msg.attachments)
                        except TypeError:
                            await msg.edit(embed=new_embed)

                # Gửi thông báo nếu cần
                if info.status == "PAID":
                    await channel.send(f"🟢 Đơn `{order}` đã thanh toán: `{info.amountPaid:,}` **VNĐ**")
                    to_remove.append(order)
                elif info.status == "CANCELLED":
                    await channel.send(f"🔴 Đơn `{order}` đã hủy")
                    to_remove.append(order)
                elif info.status == "EXPIRED":
                    await channel.send(f"🔴 Đơn `{order}` đã hết hạn")
                    to_remove.append(order)

            except Exception as e:
                print(f"Lỗi khi kiểm tra đơn {order}: {e}")

        for o in to_remove:
            self.active_orders.discard(o)
            self.order_messages.pop(o, None)

    @check_payments.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(Payos(bot))