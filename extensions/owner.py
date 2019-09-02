## NOTE: Import Standard Libraries
import discord
from discord.ext import commands

## NOTE: Import Required Libraries
import aiohttp
from os import environ
from json import dumps

## NOTE: Import Custom Libraries

## NOTE: Define Variables
mailgun_domain = environ["MAILGUN_DOMAIN"]
auth = aiohttp.BasicAuth("api", environ["MAILGUN_API_KEY"])

## NOTE: Define Functions
def create_email_embed(ctx, data, response):
    embed = ctx.bot._create_embed(ctx=ctx, description="")
    embed.add_field(name="Data:", value=f"```json\n{dumps(data, indent=2)}```", inline=False)
    embed.add_field(name="Response:", value=f"```json\n{response}```", inline=False)
    return(embed)

## NOTE: Define Cog
class owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cog_check(self, ctx):
        return(ctx.author.id == self.bot._settings["creator"])

    @commands.command(help="Restart the entire bot.", usage="restart")
    async def restart(self, ctx):
        embed = self.bot._create_embed(ctx=ctx, description=f"The bot is being restarted.")
        await self.bot.get_channel(self.bot._settings["logsChannel"]).send(embed=embed)
        await ctx.send(embed=embed)
        print("Restarting...")
        await self.bot.close()

    @commands.command(help="Send a message to every subscribed server.", usage="announce [*message]")
    async def announce(self, ctx, *, args=None):
        if args:
            embed = self.bot._create_embed(title="Announcement", description=args, footer=f"From '{ctx.author}'.")
            results = await self.bot.sql_conn.fetch("SELECT * FROM serverList;")
            for i in results:
                channel = self.bot.get_channel(int(i["subchannel"]))
                try:
                    await channel.send(embed=embed)
                except:
                    continue
            await self.bot._reply(ctx, "Done! :mailbox_with_mail:")
        else:
            await self.bot._reply(ctx, "Please specify the message to send! :warning:")

    @commands.command(help="Add a member to a mailing list.", usage="addmember|add [*list] [*email] [*user]", aliases=["add"])
    async def addmember(self, ctx, list, email, user: discord.User):
        data = {"address": email, "vars": '{"user": "%s"}' % (user)}
        async with aiohttp.ClientSession() as session:
            response = await session.post(f"https://api.mailgun.net/v3/lists/{list}@{mailgun_domain}/members", auth=auth, data=data)
            await ctx.send(embed=create_email_embed(ctx, data, await response.text()))

    @commands.command(help="Remove a member from a mailing list.", usage="removemember|remove [*list] [*email]", aliases=["remove"])
    async def removemember(self, ctx, list, email):
        async with aiohttp.ClientSession() as session:
            response = await session.delete(f"https://api.mailgun.net/v3/lists/{list}@{mailgun_domain}/members/{email}", auth=auth)
            await ctx.send(embed=create_email_embed(ctx, None, await response.text()))

    @commands.command(help="View a list of members.", usage="listmembers|list [*list]", aliases=["list"])
    async def listmembers(self, ctx, list):
        async with aiohttp.ClientSession() as session:
            response = await session.get(f"https://api.mailgun.net/v3/lists/{list}@{mailgun_domain}/members", auth=auth)
            await ctx.send(embed=create_email_embed(ctx, None, await response.text()))

    @commands.command(help="Displays this help message.", usage="sendemail [*email] [*subject] [*template]")
    async def sendemail(self, ctx, email, subject, template):
        data = {"from": f"News-Bot <noreply@{mailgun_domain}>", "to": email, "subject": subject, "template": template}
        async with aiohttp.ClientSession() as session:
            response = await session.post(f"https://api.mailgun.net/v3/{mailgun_domain}/messages", auth=auth, data=data)
            await ctx.send(embed=create_email_embed(ctx, None, await response.text()))

def setup(bot):
    bot.add_cog(owner(bot))
