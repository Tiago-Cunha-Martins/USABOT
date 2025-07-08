# cogs/role_watcher.py

import discord
from discord.ext import commands
import json
import os

CONFIG_PATH = 'config.json'

def load_config():
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump({"token": "", "prefix": "", "guilds": {}}, f, indent=4)
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_config(cfg):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=4)

class RoleWatcher(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = load_config()

    def ensure_guild(self, guild_id):
        sid = str(guild_id)
        if sid not in self.config['guilds']:
            self.config['guilds'][sid] = {
                "channel_id": None,
                "watch_roles": [],
                "promote_message": "{user} was promoted to {role} by {mod}",
                "demote_message" : "{user} was demoted from {role} by {mod}"
            }
            save_config(self.config)
        return self.config['guilds'][sid]

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        guild_conf  = self.ensure_guild(after.guild.id)
        channel_id  = guild_conf['channel_id']
        watch_roles = set(guild_conf['watch_roles'])
        if not channel_id or not watch_roles:
            return

        before_ids = {r.id for r in before.roles}
        after_ids  = {r.id for r in after.roles}
        added      = after_ids - before_ids
        removed    = before_ids - after_ids

        promo = added & watch_roles
        demo  = removed & watch_roles
        if not (promo or demo):
            return

        # find moderator in audit log
        entry = None
        async for log in after.guild.audit_logs(limit=5, action=discord.AuditLogAction.member_role_update):
            if log.target.id == after.id:
                entry = log
                break
        mod_mention = entry.user.mention if entry else "Unknown"

        chan = after.guild.get_channel(channel_id)
        if not chan:
            return

        for rid in promo:
            role = after.guild.get_role(rid)
            msg  = guild_conf['promote_message'].format(
                user=after.mention, role=role.mention, mod=mod_mention
            )
            await chan.send(msg)

        for rid in demo:
            role = after.guild.get_role(rid)
            msg  = guild_conf['demote_message'].format(
                user=after.mention, role=role.mention, mod=mod_mention
            )
            await chan.send(msg)

    @commands.command(name="setchannel")
    @commands.has_permissions(administrator=True)
    async def set_channel(self, ctx, channel: discord.TextChannel):
        gc = self.ensure_guild(ctx.guild.id)
        gc['channel_id'] = channel.id
        save_config(self.config)
        await ctx.send(f"Announcement channel set to {channel.mention}")

    @commands.command(name="addrole")
    @commands.has_permissions(administrator=True)
    async def add_role(self, ctx, role: discord.Role):
        gc = self.ensure_guild(ctx.guild.id)
        if role.id in gc['watch_roles']:
            return await ctx.send("Already watching this role.")
        gc['watch_roles'].append(role.id)
        save_config(self.config)
        await ctx.send(f"Now watching role {role.name}")

    @commands.command(name="removerole")
    @commands.has_permissions(administrator=True)
    async def remove_role(self, ctx, role: discord.Role):
        gc = self.ensure_guild(ctx.guild.id)
        if role.id not in gc['watch_roles']:
            return await ctx.send("That role is not being watched.")
        gc['watch_roles'].remove(role.id)
        save_config(self.config)
        await ctx.send(f"Stopped watching role {role.name}")

    @commands.command(name="setpromote")
    @commands.has_permissions(administrator=True)
    async def set_promote(self, ctx, *, msg: str):
        gc = self.ensure_guild(ctx.guild.id)
        gc['promote_message'] = msg
        save_config(self.config)
        await ctx.send("Promotion message updated.")

    @commands.command(name="setdemote")
    @commands.has_permissions(administrator=True)
    async def set_demote(self, ctx, *, msg: str):
        gc = self.ensure_guild(ctx.guild.id)
        gc['demote_message'] = msg
        save_config(self.config)
        await ctx.send("Demotion message updated.")

    @commands.command(name="listconfig")
    @commands.has_permissions(administrator=True)
    async def list_config(self, ctx):
        gc    = self.ensure_guild(ctx.guild.id)
        ch    = ctx.guild.get_channel(gc['channel_id'])
        roles = [ctx.guild.get_role(r).name for r in gc['watch_roles']]
        embed = discord.Embed(title="Configuration", color=discord.Color.blue())
        embed.add_field(name="Channel",         value=ch.mention if ch else "None", inline=False)
        embed.add_field(name="Watched Roles",   value=", ".join(roles) or "None",     inline=False)
        embed.add_field(name="Promote Message", value=gc['promote_message'],         inline=False)
        embed.add_field(name="Demote Message",  value=gc['demote_message'],          inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(RoleWatcher(bot))