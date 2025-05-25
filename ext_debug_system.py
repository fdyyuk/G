import logging
import sys
import os
import traceback
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
import json
from discord.ext import commands
import discord

class DebugExtension(commands.Cog):
    """Extension untuk sistem debugging"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.debug_folder = Path("logs")
        self.debug_folder.mkdir(exist_ok=True)
        
        # Setup logger khusus debug
        self.logger = logging.getLogger("DebugSystem")
        self.logger.setLevel(logging.DEBUG)
        
        # Format log yang detail
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File handler untuk debug log
        debug_handler = logging.FileHandler(
            self.debug_folder / "debug.log",
            encoding='utf-8'
        )
        debug_handler.setFormatter(formatter)
        self.logger.addHandler(debug_handler)
        
        # Tracking untuk debugging
        self.command_history: List[Dict] = []
        self.error_count: Dict[str, int] = {}
        self.performance_metrics: Dict[str, float] = {}
        self.debug_mode = False

    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context):
        """Track setiap command yang dijalankan"""
        await self.log_command(ctx)
        await self.start_performance_tracking(ctx.command.name)

    @commands.Cog.listener()
    async def on_command_completion(self, ctx: commands.Context):
        """Track setelah command selesai"""
        await self.end_performance_tracking(ctx.command.name)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: Exception):
        """Track error yang terjadi"""
        await self.log_error(error, ctx)
    
    async def log_command(self, ctx: commands.Context):
        """Log penggunaan command dengan detail"""
        timestamp = datetime.utcnow().isoformat()
        command_data = {
            "timestamp": timestamp,
            "command": ctx.command.name,
            "author": str(ctx.author),
            "channel": str(ctx.channel),
            "guild": str(ctx.guild),
            "message": ctx.message.content,
            "success": True
        }
        
        self.command_history.append(command_data)
        self.logger.info(
            f"Command executed: {ctx.command.name} by {ctx.author} in {ctx.guild}"
        )
        
        # Simpan ke file JSON
        await self.save_command_history()
    
    async def log_error(self, error: Exception, ctx: Optional[commands.Context] = None):
        """Log error dengan detail lengkap"""
        timestamp = datetime.utcnow().isoformat()
        
        error_type = type(error).__name__
        self.error_count[error_type] = self.error_count.get(error_type, 0) + 1
        
        error_data = {
            "timestamp": timestamp,
            "error_type": error_type,
            "error_message": str(error),
            "traceback": traceback.format_exc()
        }
        
        if ctx:
            error_data.update({
                "command": ctx.command.name if ctx.command else "Unknown",
                "author": str(ctx.author),
                "channel": str(ctx.channel),
                "guild": str(ctx.guild),
                "message": ctx.message.content
            })
        
        self.logger.error(
            f"Error occurred: {error_type}\n"
            f"Message: {str(error)}\n"
            f"Traceback:\n{traceback.format_exc()}"
        )
        
        await self.save_error_report(error_data)
    
    async def save_command_history(self):
        """Simpan history command ke file"""
        history_file = self.debug_folder / "command_history.json"
        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.command_history[-1000:], f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save command history: {e}")
    
    async def save_error_report(self, error_data: Dict):
        """Simpan laporan error ke file"""
        error_file = self.debug_folder / "error_reports.json"
        try:
            existing_errors = []
            if error_file.exists():
                with open(error_file, 'r', encoding='utf-8') as f:
                    existing_errors = json.load(f)
            
            existing_errors.append(error_data)
            
            with open(error_file, 'w', encoding='utf-8') as f:
                json.dump(existing_errors[-1000:], f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save error report: {e}")
    
    async def start_performance_tracking(self, name: str):
        """Mulai tracking performa untuk suatu operasi"""
        self.performance_metrics[name] = datetime.utcnow().timestamp()
    
    async def end_performance_tracking(self, name: str):
        """Akhiri tracking performa dan hitung durasi"""
        if name in self.performance_metrics:
            start_time = self.performance_metrics[name]
            duration = datetime.utcnow().timestamp() - start_time
            self.performance_metrics[name] = duration
            self.logger.debug(f"Operation '{name}' took {duration:.2f} seconds")

    @commands.command()
    @commands.is_owner()
    async def debug(self, ctx: commands.Context):
        """Toggle mode debug"""
        self.debug_mode = not self.debug_mode
        await ctx.send(f"Debug mode {'enabled' if self.debug_mode else 'disabled'}")
        self.logger.info(f"Debug mode {'enabled' if self.debug_mode else 'disabled'}")

    @commands.command()
    @commands.is_owner()
    async def debugstats(self, ctx: commands.Context):
        """Tampilkan statistik debug"""
        embed = discord.Embed(
            title="Debug Statistics",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # Command stats
        embed.add_field(
            name="Commands Executed",
            value=str(len(self.command_history)),
            inline=False
        )
        
        # Error stats
        error_str = "\n".join(
            f"{error}: {count}" for error, count in self.error_count.items()
        ) or "No errors"
        embed.add_field(
            name="Error Frequency",
            value=error_str,
            inline=False
        )
        
        # Performance stats
        perf_str = "\n".join(
            f"{name}: {duration:.2f}s"
            for name, duration in self.performance_metrics.items()
            if isinstance(duration, float)
        ) or "No metrics"
        embed.add_field(
            name="Performance Metrics",
            value=perf_str,
            inline=False
        )
        
        embed.add_field(
            name="Debug Mode",
            value="Enabled" if self.debug_mode else "Disabled",
            inline=False
        )
        
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    """Setup function untuk loading extension"""
    await bot.add_cog(DebugExtension(bot))