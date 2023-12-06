import asyncio
import datetime
import json
import os
from PIL import Image
import discord
from dotenv import load_dotenv
import requests
import requests.exceptions
from discord import Embed
from discord.ext import commands

load_dotenv()  # Load RIOT API key

# Error related to RIOT API usually are linked to the api key since the
# code itself is flawless and tested. So try to change your current api
# key to a different one by making a new account or wait a few hours.

riot_api = os.getenv('RIOT_API')  # RIOT API token


class Commands(commands.Cog):
    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        self.lock = asyncio.Lock()  # Create a lock

    @commands.command()
    async def pref(self, ctx):
        #
        # GETTERS FOR THE CONFIG FILE
        #
        set_prefix_msg = self.config['pref']['set_prefix_msg']
        timeout = self.config['pref']['timeout']
        cancel_parameter = self.config['pref']['cancel_parameter']
        cancel_msg = self.config['pref']['cancel_msg']
        timeout_msg = self.config['pref']['timeout_msg']

        await ctx.send(set_prefix_msg)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=timeout)
        except asyncio.TimeoutError:
            await ctx.send(timeout_msg)
        else:
            new_prefix = msg.content
            if new_prefix.lower() == cancel_parameter:
                await ctx.send(cancel_msg)
            else:
                guild_id = str(ctx.guild.id)  # Convert the guild ID to string
                self.bot.prefixes[guild_id] = new_prefix  # Update the prefix in memory
                async with self.lock:  # Acquire the lock before writing to the file
                    try:
                        with open('prefixes.json', 'w') as f:
                            json.dump(self.bot.prefixes, f)  # Update the prefix in the file
                        await ctx.send(f"Prefix changed to {new_prefix}")
                    except Exception as e:
                        await ctx.send(f"An error occurred while saving the prefix: {e}... Please try again.")

    @commands.command()
    async def clear(self, ctx, amount: str):
        #
        # GETTERS FOR THE CONFIG FILE
        #
        send_confirmation = self.config['clear']['send_confirmation']
        message_limit = self.config['clear']['message_limit']
        limit_text = self.config['clear']['limit_text']

        if amount.lower() == 'all':
            deleted = await ctx.channel.purge(limit=None)  # delete all messages
        else:
            try:
                amount = int(amount)
            except ValueError:
                await ctx.send("Invalid amount. Please enter a number or 'all'.")
                return

            if amount > message_limit:  # check if the amount is more than 100
                await ctx.send(limit_text)
                return
            else:
                deleted = await ctx.channel.purge(limit=amount)  # delete the messages

        await ctx.send(f"{len(deleted)} messages deleted successfully!",
                       delete_after=send_confirmation)  # send a confirmation message

    @commands.command()
    async def stats(self, ctx, name: str, region: str):
        #
        # GETTERS FOR THE CONFIG FILE
        #
        title = self.config['stats']['title']
        description_part_1 = self.config['stats']['description_part_1']

        # Get the current prefix
        current_prefix = await self.bot.command_prefix(self.bot, ctx.message)

        # Check if the region is valid
        try:
            response = requests.get(
                f"https://{region}.api.riotgames.com/lol/status/v4/platform-data",
                headers={"X-Riot-Token": riot_api})
        except requests.exceptions.ConnectionError:
            await ctx.send(
                f"The region '{region}' is not valid. To see all available regions, type `{current_prefix}regions`.")
            return

        # Fetch the summoner's data from the Riot API
        response = requests.get(
            f"https://{region}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{name}",
            headers={"X-Riot-Token": riot_api})

        data = response.json()

        # Check if the summoner name is valid
        if 'status' in data and data['status']['status_code'] == 404:
            await ctx.send(f"The summoner '{name}' does not exist in the region '{region}'.")
            return

        # Extract the summoner's name, level, and profile icon ID
        summoner_name = data['name']
        summoner_level = data['summonerLevel']
        profile_icon_id = data['profileIconId']

        # Fetch the summoner's league entries from the Riot API
        response = requests.get(
            f"https://{region}.api.riotgames.com/lol/league/v4/entries/by-summoner/{data['id']}",
            headers={"X-Riot-Token": riot_api})
        league_data = response.json()

        # Initialize wins, losses, and games played for each queue type
        solo_duo_wins = solo_duo_losses = solo_duo_games = flex_sr_wins = flex_sr_losses = flex_sr_games = flex_tt_wins = flex_tt_losses = flex_tt_games = total_games = 0

        # Extract the wins, losses, and games played for each queue type
        for entry in league_data:
            if entry['queueType'] == 'RANKED_SOLO_5x5':
                solo_duo_wins = entry['wins']
                solo_duo_losses = entry['losses']
                solo_duo_games = solo_duo_wins + solo_duo_losses
            elif entry['queueType'] == 'RANKED_FLEX_SR':
                flex_sr_wins = entry['wins']
                flex_sr_losses = entry['losses']
                flex_sr_games = flex_sr_wins + flex_sr_losses
            elif entry['queueType'] == 'RANKED_FLEX_TT':
                flex_tt_wins = entry['wins']
                flex_tt_losses = entry['losses']
                flex_tt_games = flex_tt_wins + flex_tt_losses

        # Calculate total games played in the current season
        total_games = solo_duo_games + flex_sr_games + flex_tt_games

        # Calculate win rates
        solo_duo_win_rate = (solo_duo_wins / solo_duo_games) * 100 if solo_duo_games > 0 else 0
        flex_sr_win_rate = (flex_sr_wins / flex_sr_games) * 100 if flex_sr_games > 0 else 0
        flex_tt_win_rate = (flex_tt_wins / flex_tt_games) * 100 if flex_tt_games > 0 else 0

        # Construct the URL to the profile icon
        profile_icon_url = f"http://ddragon.leagueoflegends.com/cdn/13.23.1/img/profileicon/{profile_icon_id}.png"

        # Create an embed object with a clean color (light blue)
        embed = Embed(title=title,
                      description=f"{description_part_1}\n\nFor a list of all available commands, type `{current_prefix}help`. To see all available regions, type `{current_prefix}regions`.\n\n",
                      color=0x87CEEB)

        # Add fields for user stats in a cool arrangement
        embed.add_field(name="Summoner Name", value=summoner_name, inline=True)
        embed.add_field(name="Summoner Level", value=summoner_level, inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)  # This is a blank field for better arrangement
        embed.add_field(name="Ranked Solo/Duo",
                        value=f"W: {solo_duo_wins} / L: {solo_duo_losses}\nWR: {solo_duo_win_rate:.2f}%", inline=True)
        embed.add_field(name="Ranked Flex SR",
                        value=f"W: {flex_sr_wins} / L: {flex_sr_losses}\nWR: {flex_sr_win_rate:.2f}%", inline=True)
        embed.add_field(name="Ranked Flex TT",
                        value=f"W: {flex_tt_wins} / L: {flex_tt_losses}\nWR: {flex_tt_win_rate:.2f}%", inline=True)
        embed.add_field(name="Total Games Played (Current Season)", value=total_games, inline=False)
        embed.add_field(name="Solo/Duo Games Played", value=solo_duo_games, inline=True)
        embed.add_field(name="Flex SR Games Played", value=flex_sr_games, inline=True)
        embed.add_field(name="Flex TT Games Played", value=flex_tt_games, inline=True)

        # Set thumbnail to profile icon
        embed.set_thumbnail(url=profile_icon_url)

        # Add footer with update time
        embed.set_footer(text="Last updated: " + str(datetime.datetime.now()))

        # Send the embed
        await ctx.send(embed=embed)

    @commands.command()
    async def help(self, ctx):
        #
        # GETTERS FOR THE CONFIG FILE
        #
        title = self.config['help']['title']
        description = self.config['help']['description']

        # Get the current prefix
        current_prefix = await self.bot.command_prefix(self.bot, ctx.message)

        # Create an embed object for the help command
        embed = Embed(title=title, description=description,
                      color=0x87CEEB)

        # Add fields for each command
        embed.add_field(name=f"{current_prefix}mmr <name> <region>",
                        value="Displays the MMR for the summoner with the given name in the given region.",
                        inline=False)
        embed.add_field(name=f"{current_prefix}stats <name> <region>",
                        value="Displays detailed statistics for the summoner with the given name in the given region.",
                        inline=False)
        embed.add_field(name=f"{current_prefix}clear <number>",
                        value="Clear the last <number> messages in the current chat.",
                        inline=False)
        embed.add_field(name=f"{current_prefix}clear all",
                        value="Clear all messages from the current chat.",
                        inline=False)
        embed.add_field(name=f"{current_prefix}pref",
                        value="Allow you to change to the desired prefix.",
                        inline=False)
        embed.add_field(name=f"{current_prefix}regions",
                        value="Display all regions to use in league of legends commands.",
                        inline=False)

        # Send the embed
        await ctx.send(embed=embed)

    @commands.command()
    async def regions(self, ctx):
        #
        # GETTERS FOR THE CONFIG FILE
        #
        title = self.config['regions']['title']
        description = self.config['regions']['description']

        # Create an embed object for the regions command
        embed = Embed(title=title,
                      description=description,
                      color=0x87CEEB)

        # Add a field with the list of regions
        regions = ["BR1", "EUN1", "EUW1", "JP1", "KR", "LA1", "LA2", "NA1", "OC1", "TR1", "RU"]
        embed.add_field(name="Regions", value="\n".join(regions), inline=False)

        # Send the embed
        await ctx.send(embed=embed)

    @commands.command()
    async def mmr(self, ctx, summoner_name: str, region: str):
        #
        # GETTERS FOR THE CONFIG FILE
        #
        description = self.config['mmr']['description']
        # Fetch the summoner's data
        summoner_data = requests.get(
            f"https://{region}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}",
            headers={"X-Riot-Token": riot_api}).json()

        # Fetch the summoner's league data
        league_data = requests.get(
            f"https://{region}.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_data['id']}",
            headers={"X-Riot-Token": riot_api}).json()

        # Filter out the solo/duo data
        solo_duo_data = next((data for data in league_data if data['queueType'] == 'RANKED_SOLO_5x5'), None)

        if solo_duo_data is None:
            await ctx.send(f"{summoner_name} has not played any ranked solo/duo games this season.")
            return

        # Calculate the win rate
        wins = solo_duo_data['wins']
        losses = solo_duo_data['losses']
        win_rate = wins / (wins + losses)

        # Calculate the number of games played
        games_played = wins + losses

        # Fetch the summoner's match history
        match_history = requests.get(
            f"https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{summoner_data['puuid']}/ids?start=0&count=20",
            headers={"X-Riot-Token": riot_api}).json()

        # Calculate the performance in recent games and check for win streaks
        recent_wins = 0
        streak = 0
        if match_history:
            for match_id in match_history:
                match_details = requests.get(
                    f"https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}",
                    headers={"X-Riot-Token": riot_api}).json()
                for participant in match_details['info']['participants']:
                    if participant['puuid'] == summoner_data['puuid']:
                        if participant['win']:
                            recent_wins += 1
                            streak += 1
                        else:
                            streak = 0
                        break

        # Calculate the recent win rate
        recent_win_rate = recent_wins / len(match_history) if match_history else 0

        # Calculate a basic MMR estimation based on the summoner's rank and LP
        rank_values = {'IRON': 0, 'BRONZE': 400, 'SILVER': 800, 'GOLD': 1200, 'PLATINUM': 1600, 'EMERALD': 2000,
                       'DIAMOND': 2400, 'MASTER': 2800, 'GRANDMASTER': 3200, 'CHALLENGER': 3600}
        division_values = {'IV': 0, 'III': 100, 'II': 200, 'I': 300}

        mmr = rank_values[solo_duo_data['tier']] + division_values[solo_duo_data['rank']] + solo_duo_data[
            'leaguePoints']
        mmr += round(win_rate * 220)  # Adjust MMR based on win rate
        mmr -= games_played * 0.3  # Adjust MMR based on number of games played
        mmr += round(recent_win_rate * 75)  # Adjust MMR based on recent win rate
        mmr += streak * 10  # Adjust MMR based on win streak
        mmr = round(mmr)  # Round the MMR to the nearest whole number

        # Determine the corresponding tier and division
        tier = None
        division = None
        for rank, rank_value in reversed(list(rank_values.items())):
            for div, div_value in reversed(list(division_values.items())):
                if mmr >= rank_value + div_value:
                    tier = rank
                    division = div
                    break
            if tier is not None:
                break

        if tier and division:
            # await ctx.send(f"{summoner_name}'s estimated MMR is {mmr}, which corresponds to {tier} {division}.")
            print("")
        else:
            # await ctx.send(f"{summoner_name}'s estimated MMR is {mmr}.")
            print("")

        # Fetch the summoner's data
        summoner_data = requests.get(
            f"https://{region}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}",
            headers={"X-Riot-Token": riot_api}).json()

        # Extract the profile icon ID from the summoner data
        profile_icon_id = summoner_data['profileIconId']

        # Create an embed to display the MMR information
        embed = discord.Embed(
            title=f"{summoner_name}'s estimated MMR",
            description=description,
            color=discord.Color.blue()
        )

        # Add the summoner icon to the embed
        summoner_icon_url = f"https://ddragon.leagueoflegends.com/cdn/13.23.1/img/profileicon/{profile_icon_id}.png"
        embed.set_thumbnail(url=summoner_icon_url)

        # Add the MMR and rank to the embed as fields
        embed.add_field(name="Estimated MMR", value=f"{mmr}", inline=False)
        embed.add_field(name="Corresponding Rank", value=f"{tier} {division}", inline=False)

        # Resize the rank icon
        with Image.open(f'./images/{tier.lower()}.png') as img:
            img = img.resize((118, 118), Image.LANCZOS)
            img.save(f'./images/resized_{tier.lower()}.png')

        # Add the rank icon to the embed
        rank_icon_path = f"./images/resized_{tier.lower()}.png"  # path to your resized rank images
        file = discord.File(rank_icon_path, filename="rank_icon.png")
        embed.set_image(url="attachment://rank_icon.png")

        await ctx.send(file=file, embed=embed)

    @commands.command()  # This command is reserved to the bot's owner so it won't appear in help list
    @commands.is_owner()
    async def shutdown(self, ctx):
        await ctx.send("Bot is shutting down...")
        await self.bot.close()


