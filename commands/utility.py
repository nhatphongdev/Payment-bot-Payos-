import discord
from discord.ext import commands
import psutil
import platform
from datetime import datetime
import asyncio

class UtilityCommands(commands.Cog):

    @commands.hybrid_command(name='orders')
    async def list_orders(self, ctx, page: int = 1):
        """
        Xem danh sách các đơn thanh toán 
        """
        # Lấy cog Payos
        payos_cog = self.bot.get_cog('Payos')
        if not payos_cog or not hasattr(payos_cog, 'active_orders'):
            await ctx.send("❌ Không tìm thấy dữ liệu đơn hàng!")
            return

        # Lấy danh sách order_code
        order_codes = list(payos_cog.active_orders)
        if not order_codes:
            await ctx.send("✅ Hiện không có đơn nào đang hoạt động!")
            return

        # Sắp xếp để dễ nhìn
        order_codes.sort(reverse=True)

        # Phân trang
        per_page = 10
        total = len(order_codes)
        max_page = (total - 1) // per_page + 1
        page = max(1, min(page, max_page))
        start = (page - 1) * per_page
        end = start + per_page
        orders_page = order_codes[start:end]

        embed = discord.Embed(
            title=f"📋 Danh sách đơn thanh toán (Trang {page}/{max_page})",
            color=0x0099ff,
            timestamp=datetime.now()
        )

        for order_code in orders_page:
            # Lấy thông tin đơn
            try:
                info = payos_cog.payOS.getPaymentLinkInformation(order_code)
                # Lấy user mention từ description (lưu user id ở description khi tạo đơn)
                user_id = None
                try:
                    user_id = int(info.description)
                except:
                    user_id = None
                user_mention = f'<@{user_id}>' if user_id else 'Unknown'
                money = f"{info.amount:,} VNĐ" if hasattr(info, 'amount') else 'N/A'
                status = info.status if hasattr(info, 'status') else 'N/A'
            except Exception as e:
                user_mention = 'Unknown'
                money = 'N/A'
                status = f'Lỗi: {e}'
            embed.add_field(
                name=f"ID: {order_code}",
                value=f"👤 {user_mention}\n💸 {money}\n📦 {status}",
                inline=False
            )

        # Footer hướng dẫn chuyển trang nếu có nhiều trang
        if max_page > 1:
            embed.set_footer(text=f"Dùng lệnh !orders <số_trang> để chuyển trang. Trang {page}/{max_page}")
        else:
            embed.set_footer(text="Danh sách đơn hàng hiện tại")

        await ctx.send(embed=embed)
    """
    General utility commands for the Discord bot
    
    This cog provides helpful administrative and informational commands
    that complement the main PayOS functionality. These commands help
    administrators monitor bot health and provide users with basic tools.
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.start_time = datetime.now()
    
    @commands.hybrid_command(name='ping')
    async def ping(self, ctx):
        """
        Xem độ trễ của bot và Discord WebSocket
        """
        # Calculate Discord WebSocket latency
        ws_latency = round(self.bot.latency * 1000, 2)
        
        # Measure message round-trip time
        start_time = datetime.now()
        message = await ctx.send("🏓 Pinging...")
        end_time = datetime.now()
        
        # Calculate message latency
        msg_latency = round((end_time - start_time).total_seconds() * 1000, 2)
        
        # Create response embed with latency information
        embed = discord.Embed(
            title="🏓 Pong!",
            color=0x00ff00 if ws_latency < 100 else 0xffaa00 if ws_latency < 200 else 0xff0000,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="📡 WebSocket Latency",
            value=f"`{ws_latency}ms`",
            inline=True
        )
        
        embed.add_field(
            name="💬 Message Latency",
            value=f"`{msg_latency}ms`",
            inline=True
        )
        
        # Add connection quality indicator
        if ws_latency < 100:
            quality = "🟢 Excellent"
        elif ws_latency < 200:
            quality = "🟡 Good"
        elif ws_latency < 300:
            quality = "🟠 Fair"
        else:
            quality = "🔴 Poor"
        
        embed.add_field(
            name="📊 Connection Quality",
            value=quality,
            inline=True
        )
        
        # Update the original message with detailed information
        await message.edit(content=None, embed=embed)
    
    @commands.hybrid_command(name='uptime')
    async def uptime(self, ctx):
        """
        Xem bot uptime
        """
        # Calculate uptime duration
        uptime_duration = datetime.now() - self.start_time
        
        # Break down the duration into readable components
        days = uptime_duration.days
        hours, remainder = divmod(uptime_duration.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # Format uptime string
        uptime_parts = []
        if days > 0:
            uptime_parts.append(f"{days} ngày")
        if hours > 0:
            uptime_parts.append(f"{hours} giờ")
        if minutes > 0:
            uptime_parts.append(f"{minutes} phút")
        if seconds > 0 or not uptime_parts:  # Show seconds if it's the only unit
            uptime_parts.append(f"{seconds} giây")
        
        uptime_string = ", ".join(uptime_parts)
        
        # Create uptime embed
        embed = discord.Embed(
            title="⏰ Bot Uptime",
            description=f"Bot đã hoạt động trong: **{uptime_string}**",
            color=0x0099ff,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="🚀 Khởi động lúc",
            value=self.start_time.strftime("%d/%m/%Y %H:%M:%S"),
            inline=True
        )
        
        embed.add_field(
            name="📊 Trạng thái",
            value="🟢 Hoạt động bình thường",
            inline=True
        )
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command()
    async def stats(self, ctx):
        """
        Xem thống kê chi tiết về bot và hệ thống
        """
        # Gather system information
        try:
            # CPU and memory usage
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_used = round(memory.used / 1024 / 1024 / 1024, 2)  # Convert to GB
            memory_total = round(memory.total / 1024 / 1024 / 1024, 2)  # Convert to GB
            memory_percent = memory.percent
            
            # System information
            system_info = {
                'platform': platform.system(),
                'version': platform.version(),
                'python': platform.python_version()
            }
            
        except Exception as e:
            # If system info gathering fails, use placeholder values
            cpu_percent = "N/A"
            memory_used = memory_total = memory_percent = "N/A"
            system_info = {'platform': 'Unknown', 'version': 'Unknown', 'python': 'Unknown'}
        
        # Calculate bot uptime
        uptime_duration = datetime.now() - self.start_time
        uptime_hours = round(uptime_duration.total_seconds() / 3600, 1)
        
        # Create comprehensive stats embed
        embed = discord.Embed(
            title="📊 Bot Statistics",
            description="Thông tin chi tiết về bot và hệ thống",
            color=0x0099ff,
            timestamp=datetime.now()
        )
        
        # Discord-related statistics
        embed.add_field(
            name="🌐 Discord Stats",
            value=f"Servers: **{len(self.bot.guilds)}**\n"
                  f"Users: **{len(self.bot.users)}**\n"
                  f"Commands: **{len(self.bot.commands)}**\n"
                  f"Latency: **{round(self.bot.latency * 1000, 2)}ms**",
            inline=True
        )
        
        # System performance statistics
        embed.add_field(
            name="💻 System Stats",
            value=f"CPU: **{cpu_percent}%**\n"
                  f"RAM: **{memory_used}/{memory_total} GB** ({memory_percent}%)\n"
                  f"Uptime: **{uptime_hours}h**",
            inline=True
        )
        
        # System information
        embed.add_field(
            name="🔧 System Info",
            value=f"OS: **{system_info['platform']}**\n"
                  f"Python: **{system_info['python']}**\n"
                  f"discord.py: **{discord.__version__}**",
            inline=True
        )
        
        # Bot activity statistics
        embed.add_field(
            name="📈 Activity",
            value=f"Started: **{self.start_time.strftime('%d/%m/%Y %H:%M')}**\n"
                  f"Cogs Loaded: **{len(self.bot.cogs)}**\n"
                  f"Extensions: **{len(self.bot.extensions)}**",
            inline=False
        )
        
        # Add footer with additional info
        embed.set_footer(
            text=f"Bot ID: {self.bot.user.id} | Requested by {ctx.author.display_name}",
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None
        )
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name='serverinfo')
    async def server_info(self, ctx):
        """
        Xem thông tin chi tiết về server hiện tại
        """
        guild = ctx.guild
        
        if not guild:
            await ctx.send("❌ Lệnh này chỉ có thể sử dụng trong server!")
            return
        
        # Calculate member statistics
        total_members = guild.member_count
        online_members = sum(1 for member in guild.members if member.status != discord.Status.offline)
        bot_count = sum(1 for member in guild.members if member.bot)
        human_count = total_members - bot_count
        
        # Channel statistics
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        
        # Create server info embed
        embed = discord.Embed(
            title=f"🏛️ {guild.name}",
            description=f"Thông tin chi tiết về server",
            color=0x0099ff,
            timestamp=datetime.now()
        )
        
        # Add server icon if available
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        # Basic server information
        embed.add_field(
            name="👑 Owner",
            value=guild.owner.mention if guild.owner else "Unknown",
            inline=True
        )
        
        embed.add_field(
            name="📅 Created",
            value=guild.created_at.strftime("%d/%m/%Y"),
            inline=True
        )
        
        embed.add_field(
            name="🆔 Server ID",
            value=f"`{guild.id}`",
            inline=True
        )
        
        # Member statistics
        embed.add_field(
            name="👥 Members",
            value=f"Total: **{total_members}**\n"
                  f"Online: **{online_members}**\n"
                  f"Humans: **{human_count}**\n"
                  f"Bots: **{bot_count}**",
            inline=True
        )
        
        # Channel statistics
        embed.add_field(
            name="📺 Channels",
            value=f"Text: **{text_channels}**\n"
                  f"Voice: **{voice_channels}**\n"
                  f"Categories: **{categories}**\n"
                  f"Total: **{text_channels + voice_channels}**",
            inline=True
        )
        
        # Role and boost information
        embed.add_field(
            name="🎭 Other Info",
            value=f"Roles: **{len(guild.roles)}**\n"
                  f"Boosts: **{guild.premium_subscription_count}**\n"
                  f"Boost Level: **{guild.premium_tier}**\n"
                  f"Emojis: **{len(guild.emojis)}**",
            inline=True
        )
        
        # Server features
        if guild.features:
            features = []
            feature_names = {
                'COMMUNITY': 'Community Server',
                'PARTNERED': 'Discord Partner',
                'VERIFIED': 'Verified',
                'VANITY_URL': 'Custom Invite Link',
                'INVITE_SPLASH': 'Invite Splash',
                'BANNER': 'Server Banner',
                'ANIMATED_ICON': 'Animated Icon'
            }
            
            for feature in guild.features:
                if feature in feature_names:
                    features.append(feature_names[feature])
            
            if features:
                embed.add_field(
                    name="✨ Features",
                    value="\n".join(f"• {feature}" for feature in features[:5]),  # Limit to 5 features
                    inline=False
                )
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name='userinfo')
    async def user_info(self, ctx, member: discord.Member = None):
        """
        Xem thông tin chi tiết về người dùng
        """
        # Use command author if no member specified
        if member is None:
            member = ctx.author
        
        # Create user info embed
        embed = discord.Embed(
            title=f"👤 {member.display_name}",
            description=f"Thông tin về {member.mention}",
            color=member.color if member.color != discord.Color.default() else 0x0099ff,
            timestamp=datetime.now()
        )
        
        # Add user avatar
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        
        # Basic user information
        embed.add_field(
            name="🏷️ Username",
            value=f"{member.name}#{member.discriminator}" if member.discriminator != "0" else member.name,
            inline=True
        )
        
        embed.add_field(
            name="🆔 User ID",
            value=f"`{member.id}`",
            inline=True
        )
        
        embed.add_field(
            name="🤖 Bot",
            value="Yes" if member.bot else "No",
            inline=True
        )
        
        # Account and server join dates
        embed.add_field(
            name="📅 Account Created",
            value=member.created_at.strftime("%d/%m/%Y %H:%M"),
            inline=True
        )
        
        if isinstance(member, discord.Member):
            embed.add_field(
                name="📥 Joined Server",
                value=member.joined_at.strftime("%d/%m/%Y %H:%M") if member.joined_at else "Unknown",
                inline=True
            )
            
            # Status information
            status_emoji = {
                discord.Status.online: "🟢 Online",
                discord.Status.idle: "🟡 Idle",
                discord.Status.dnd: "🔴 Do Not Disturb",
                discord.Status.offline: "⚫ Offline"
            }
            
            embed.add_field(
                name="📊 Status",
                value=status_emoji.get(member.status, "❓ Unknown"),
                inline=True
            )
            
            # Role information (limit to avoid embed size issues)
            if member.roles[1:]:  # Exclude @everyone role
                roles = [role.mention for role in reversed(member.roles[1:])]
                role_list = ", ".join(roles[:10])  # Limit to 10 roles
                if len(member.roles) > 11:
                    role_list += f" and {len(member.roles) - 11} more..."
                
                embed.add_field(
                    name=f"🎭 Roles ({len(member.roles) - 1})",
                    value=role_list,
                    inline=False
                )
            
            # Permissions (show only if user has significant permissions)
            if member.guild_permissions.administrator:
                embed.add_field(
                    name="🔐 Key Permissions",
                    value="👑 Administrator",
                    inline=False
                )
            else:
                key_perms = []
                if member.guild_permissions.manage_guild:
                    key_perms.append("Manage Server")
                if member.guild_permissions.manage_channels:
                    key_perms.append("Manage Channels")
                if member.guild_permissions.manage_messages:
                    key_perms.append("Manage Messages")
                if member.guild_permissions.kick_members:
                    key_perms.append("Kick Members")
                if member.guild_permissions.ban_members:
                    key_perms.append("Ban Members")
                
                if key_perms:
                    embed.add_field(
                        name="🔐 Key Permissions",
                        value=", ".join(key_perms),
                        inline=False
                    )
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name='clear')
    @commands.has_permissions(manage_messages=True)
    async def clear_messages(self, ctx, amount: int = 10):
        """
        Xem và xóa một số lượng tin nhắn nhất định
        """
        # Validate amount
        if amount < 1:
            await ctx.send("❌ Số lượng tin nhắn phải lớn hơn 0!")
            return
        
        if amount > 100:
            await ctx.send("❌ Không thể xóa quá 100 tin nhắn một lúc!")
            return
        
        try:
            # Delete messages (including the command message)
            deleted = await ctx.channel.purge(limit=amount + 1)
            
            # Send confirmation (will auto-delete after 5 seconds)
            confirmation = await ctx.send(
                f"✅ Đã xóa {len(deleted) - 1} tin nhắn!",
                delete_after=5
            )
            
        except discord.Forbidden:
            await ctx.send("❌ Bot không có quyền xóa tin nhắn!")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Lỗi khi xóa tin nhắn: {e}")
    
    @commands.hybrid_command(name='say')
    @commands.has_permissions(manage_messages=True)
    async def say(self, ctx, *, message):
        """
        Xem và gửi một tin nhắn tùy chỉnh
        """
        try:
            # Delete the original command
            await ctx.message.delete()
            
            # Send the message
            await ctx.send(message)
            
        except discord.Forbidden:
            await ctx.send("❌ Bot không có quyền xóa tin nhắn!")
        except Exception as e:
            await ctx.send(f"❌ Lỗi: {e}")
    
    @commands.hybrid_command(name='embed')
    @commands.has_permissions(manage_messages=True)
    async def create_embed(self, ctx, title, *, description):
        """
        Xem và tạo một embed tùy chỉnh
        """
        try:
            # Delete the original command
            await ctx.message.delete()
            
            # Create and send embed
            embed = discord.Embed(
                title=title,
                description=description,
                color=0x0099ff,
                timestamp=datetime.now()
            )
            
            embed.set_footer(
                text=f"Created by {ctx.author.display_name}",
                icon_url=ctx.author.avatar.url if ctx.author.avatar else None
            )
            
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            await ctx.send("❌ Bot không có quyền xóa tin nhắn!")
        except Exception as e:
            await ctx.send(f"❌ Lỗi: {e}")

# Required function for cog loading
async def setup(bot):
    """Function called when loading this cog"""
    await bot.add_cog(UtilityCommands(bot))