import discord
from discord.ext import commands
import requests
from bs4 import BeautifulSoup

class EmbedPoster(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.allowed_roles = ['Commanders', 'R5']

    def fetch_metadata(self, url: str) -> dict:
        try:
            resp = requests.get(url, timeout=5)
            soup = BeautifulSoup(resp.text, 'html.parser')
            og_desc = soup.find('meta', property='og:description')
            og_img  = soup.find('meta', property='og:image')
            return {
                'desc': og_desc['content'] if og_desc else None,
                'img' : og_img['content']  if og_img  else None
            }
        except:
            return {'desc': None, 'img': None}

    @commands.command(name='postguide')
    async def post_guide(self, ctx, title: str, url: str, *, description: str):
        """
        Usage:
          !postguide "Guide Title" https://example.com Your description
        """
        # delete invoker to suppress Discord auto-preview
        await ctx.message.delete()

        # permission check
        if not any(r.name in self.allowed_roles for r in ctx.author.roles):
            return await ctx.send("❌ You lack permission.")

        # fetch OG metadata
        data = self.fetch_metadata(url)

        # build embed
        embed = discord.Embed(
            title=title,
            description=f"**{description}**",
            color=discord.Color.blue()
        )

        embed.add_field(
            name='🔗 Guide Link',
            value=url,
            inline=False
        )

        if data['desc']:
            embed.add_field(
                name='📝 Preview',
                value=data['desc'],
                inline=False
            )

        if data['img']:
            embed.set_thumbnail(url=data['img'])

        await ctx.send(content='@everyone', embed=embed)

    @commands.command(name='setroles')
    @commands.has_permissions(administrator=True)
    async def set_embed_roles(self, ctx, *roles):
        """
        Usage:
          !setroles Commanders Moderator Helper
        """
        self.allowed_roles = roles
        await ctx.send(f"✅ Embed roles updated: {', '.join(roles)}")

async def setup(bot):
    await bot.add_cog(EmbedPoster(bot))