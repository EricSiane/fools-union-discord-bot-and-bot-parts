import asyncio
import json
import pandas as pd
import argparse
import discord
from discord.ext import commands
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
import random
from collections import deque
import json
from datetime import datetime
from Defs import clan_import


# Lists needed for BOTW & SOTW
skill_of_the_week = ["Runecraft", "Construction", "Agility", "Herblore", "Thieving", "Crafting", "Fletching", "Slayer", "Hunter", "Mining", "Smithing", "Fishing", "Cooking", "Firemaking", "Woodcutting", "Farming"]


boss_of_the_week = ["Abyssal Sire", "Alchemical Hydra", "Araxxor", "Barrows", "Bryophyta", "Callisto", "Vet'ion", "Cerberus", "Chaos Elemental", "Chaos Fanatic", "Commander Zilyana", "Corporeal Beast", "Crazy Archaeologist", "Dagannoth Prime", "Dagannoth Rex", "Dagannoth Supreme",
 "Deranged Archaeologist", "Duke Sucellus", "General Graardor", "Giant Mole", "Grotesque Guardians",
 "Kalphite Queen", "King Black Dragon", "Kraken", "Kree'Arra", "K'ril Tsutsaroth", "Nex", "Nightmare", "Obor", "Phantom Muspah", "Sarachnis", "Scorpia", "Scurrius", "Skotizo", "Tempoross", "The Gauntlet", "The Leviathan", "The Whisperer", "Thermonuclear Smoke Devil", "TzTok-Jad", "Vardorvis", "Venenatis", "Vorkath", "Wintertodt", "Zalcano", "Zulrah"]


#Bot Init Start
intents = discord.Intents.default()
intents.members = True
intents.voice_states = True
intents.presences = True
intents.message_content = True

bot = discord.Client(intents=intents)
# Load env variables for bot and channel
load_dotenv()
bot_token = os.getenv("BOT_TOKEN")
#print(bot_token)
vc_id = os.getenv("CHANNEL_ID")
#print(vc_id)
#Bot Init End

#Defs
def handle_storedata_command(data_to_import):
    try:
        # 1. Parse the imported data
        imported_data = json.loads(data_to_import)

        # Remove trailing spaces from values in the imported data
        for entry in imported_data:
            for key, value in entry.items():
                if isinstance(value, str):
                    entry[key] = value.rstrip()

        # 2. (Optional) Read existing data from your JSON file
        try:
            with open('clan_member_data.json', 'r') as f:
                existing_data = json.load(f)

            # Remove trailing spaces from values in the existing data
            for entry in existing_data:
                for key, value in entry.items():
                    if isinstance(value, str):
                        entry[key] = value.rstrip()

        except FileNotFoundError:
            existing_data = []  # Start with an empty list if the file doesn't exist

        # 3. Combine or update data (choose one based on your needs)
        # Option 1: Append new data to existing data
        existing_data.extend(imported_data)

        # Option 2: Update existing data with new data (matching by 'rsn')
        # for new_entry in imported_data:
        #     for existing_entry in existing_data:
        #         if new_entry['rsn'] == existing_entry['rsn']:
        #             existing_entry.update(new_entry)  # Update existing entry
        #             break
        #     else:  # If no match found, append the new entry
        #         existing_data.append(new_entry)

        # 4. Write the updated data back to the JSON file
        with open('clan_member_data.json', 'w') as f:
            # Ensure no trailing whitespace when writing
            json_str = json.dumps(existing_data, indent=4)
            f.write(json_str.rstrip() + "\n")  # Add newline for clarity

        return "Data imported successfully!"

    except json.JSONDecodeError:
        return "Error: Invalid JSON data provided."

#Start Bot commands
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')


@bot.event
async def on_message(message):
    guild = message.guild
    content_lower = message.content.lower()

    # Checking for the '!rsn' command
    if content_lower.startswith('!rsn ') and not message.author.bot:
        rsn = content_lower[len('!rsn '):]

        csv_file = "fools_union_member_data.csv"
        df = pd.read_csv(csv_file)

        df['Discord'] = df['Discord'].astype(str)
        df['rsn_lower'] = df['rsn'].str.lower()
        fools = discord.utils.get(guild.roles, name="Fools")
        iron = discord.utils.get(guild.roles, name="Iron Bar")
        guest = discord.utils.get(guild.roles, name="Guest")

        if rsn in df['rsn_lower'].values:
            index = df.index[df['rsn_lower'] == rsn].tolist()[0]
            df.at[index, 'Discord'] = str(message.author.id)
            df.to_csv(csv_file, index=False)

            original_rsn = df.at[index, 'rsn']
            sent_message = await message.channel.send(
                f"Discord ID {message.author.mention} has been linked to RSN '{df.at[index, 'rsn']}'."
            )
            await message.author.add_roles(fools, iron)
            await message.author.remove_roles(guest)

            await asyncio.sleep(10)  # Wait for 10 seconds
            await sent_message.delete()
            await message.delete()

            try:
                await message.author.edit(nick=original_rsn)
            except discord.Forbidden:
                await message.channel.send("I don't have permission to change your nickname.")
        else:
            await message.channel.send(f"RSN '{rsn}' not found in the clan list. If you aren't in the clan, welcome as a guest!")
            await message.author.add_roles(guest)

    # Checking for the '!otwselect' command
    elif content_lower.startswith("!otwselect") and not message.author.bot:
        data_file_path = 'selection_data.json'

        # Load data if it exists for BOTW & SOTW
        if os.path.exists(data_file_path):
            with open(data_file_path, 'r') as f:
                data = json.load(f)
                last_3_bosses = deque(data['last_3_bosses'], maxlen=3)
                last_3_skills = deque(data['last_3_skills'], maxlen=3)
        else:
            last_3_bosses = deque(maxlen=3)
            last_3_skills = deque(maxlen=3)

        while True:
            boss_choice = random.choice(boss_of_the_week)
            if boss_choice not in last_3_bosses:
                break
        last_3_bosses.append(boss_choice)

        while True:
            skill_choice = random.choice(skill_of_the_week)
            if skill_choice not in last_3_skills:
                break
        last_3_skills.append(skill_choice)

        await message.channel.send(f"Boss of the Week: {boss_choice}\nSkill of the Week: {skill_choice}")

        # Save updated data
        with open(data_file_path, 'w') as f:
            data = {
                'last_3_bosses': list(last_3_bosses),
                'last_3_skills': list(last_3_skills)
            }
            json.dump(data, f)

        # Debug notifications (optional)
        print("DEBUG: Updated lists after selection:")
        print("Last 3 bosses:", list(last_3_bosses))
        print("Last 3 skills:", list(last_3_skills))
#End OTW Selection

#Import Clan JSON Data Start
    elif message.content.startswith("!importjson") and not message.author.bot:
        json_data = message.content[len("!importjson") + 1:].strip()

        try:
            result = handle_storedata_command(json_data)  # Use your existing function
            await message.channel.send(result)
        except Exception as e:
            await message.channel.send(f"An error occurred during import: {e}")
    # Import Clan JSON Data End

   #Clan Updater from @Bobness Start
    elif message.content.startswith("!updateclan") and not message.author.bot:
        # Define the file paths directly here
        JSON_FILE = "clan_member_data.json"
        CSV_FILE = "fools_union_member_data.csv"

        def load_data(json_file):
            """Loads member data from a JSON file."""
            with open(json_file, 'r') as f:
                data = json.load(f)
            return data

        def calculate_member_stats(members):
            """Calculates additional stats for each member."""
            today = datetime.today()
            for member in members:
                joined_date = datetime.strptime(member["joinedDate"], "%d-%b-%Y")
                days_elapsed = (today - joined_date).days
                member["days in clan"] = days_elapsed
                member["points from time in clan"] = (days_elapsed // 5)
                member["joinedDate"] = joined_date.strftime("%#m/%#d/%Y")  # Format date
            return members

        def update_clan_csv(clan_csv, members):
            """Updates the clan CSV with member data."""
            for member in members:
                # Check if member exists in CSV
                existing_member = clan_csv[clan_csv['rsn'].str.rstrip() == member['rsn'].rstrip()]

                if not existing_member.empty:
                    # Update existing member
                    index = existing_member.index[0]
                    clan_csv.at[index, 'Points From Time in Clan'] = member["points from time in clan"]
                    clan_csv.at[index, 'Days in Clan'] = member["days in clan"]
                else:
                    # Add new member
                    clan_csv.loc[len(clan_csv)] = [
                        member['rsn'],
                        member["joinedDate"],
                        "Bronze Bar",
                        "",
                        member["days in clan"],
                        member["points from time in clan"],
                        0,
                        member["points from time in clan"],
                        [],
                        [],
                    ]
            return clan_csv

        def update_ranks(clan_csv):
            """Updates ranks based on total points."""

            def get_new_rank(total_points):
                """Determines the new rank based on total points."""
                rank_thresholds = [
                    (10, "Bronze Bar"),
                    (30, "Iron Bar"),
                    (50, "Steel Bar"),
                    (75, "Gold Bar"),
                    (100, "Mithril Bar"),
                    (125, "Adamant Bar"),
                    (150, "Rune Bar"),
                    (200, "Dragon Bar"),
                    (250, "Onyx"),
                ]
                for threshold, rank in rank_thresholds:
                    if total_points < threshold:
                        return rank
                return "Zenyte"

            # Calculate total points and update ranks efficiently using pandas apply
            clan_csv['Total Points'] = clan_csv['Points From Time in Clan'] + clan_csv['Other Points']
            clan_csv['new_rank'] = clan_csv['Total Points'].apply(get_new_rank)

            # Identify and print rank changes
            rank_changed = clan_csv['rank'] != clan_csv['new_rank']
            for _, row in clan_csv[rank_changed].iterrows():
                print(f"{row['rsn']} rank has changed to: {row['new_rank']}")

            # Update the 'rank' column
            clan_csv['rank'] = clan_csv['new_rank']
            clan_csv.drop(columns=['new_rank'], inplace=True)  # Remove temporary column

            print("Updated!")
            return clan_csv

        def main():
            # Load data directly from the files
            members = load_data(JSON_FILE)
            members = calculate_member_stats(members)
            clan_csv = pd.read_csv(CSV_FILE)
            clan_csv['rsn'] = clan_csv['rsn'].astype(str)

            # Update CSV and ranks
            clan_csv = update_clan_csv(clan_csv, members)
            clan_csv = update_ranks(clan_csv)

            # Save updated CSV
            clan_csv.to_csv(CSV_FILE, index=False)

        if __name__ == "__main__":
            main()
        await message.channel.send(f"Clan has been updated!")
        #Clan Updater End

    #Export Clan CSV to Discord Start
    elif content_lower.startswith('!export') and not message.author.bot:
        try:
            file = discord.File("fools_union_member_data.csv")
            await message.channel.send("Here is the file you requested:", file=file)
        except Exception as e:
            await message.channel.send(f"Failed to send file: {e}")
                #Expoert Clan CSV to Discord end

    #Add Joker Points Start
    elif content_lower.startswith('!jpadd') and not message.author.bot:
        csv_file = "fools_union_member_data.csv"
        df = pd.read_csv(csv_file)
        try:
            # Parse the command and extract the RSN name
            rsn = content_lower[len('!jpadd '):].strip()

            # Convert RSN in DataFrame to lowercase for comparison
            df['rsn_lower'] = df['rsn'].str.lower()

            if rsn in df['rsn_lower'].values:
                index = df.index[df['rsn_lower'] == rsn].tolist()[0]

                # Add 5 points to "Other Points"
                df.at[index, 'Other Points'] += 5

                # Calculate total points (Points From Time in Clan + Other Points)
                df.at[index, 'Total Points'] = df.at[index, 'Points From Time in Clan'] + df.at[index, 'Other Points']

                # Save the DataFrame back to the CSV
                df.to_csv(csv_file, index=False)

                await message.channel.send(f"Added 5 points to '{df.at[index, 'rsn']}'. New total: {df.at[index, 'Total Points']}")
            else:
                await message.channel.send(f"RSN '{rsn}' not found in the clan list.")
        except Exception as e:
            await message.channel.send(f"An error occurred: {str(e)}")

            #Add Joker Points End


#Start MakeAVC
TARGET_VOICE_CHANNEL_ID = int(vc_id)

# Dictionary to store created channels for each user
created_channels = {}

# Path to store JSON data
json_file_path = "created_channels.json"


# Function to load created channels from JSON
def load_channels_from_json():
    global created_channels
    if os.path.exists(json_file_path):
        with open(json_file_path, "r") as f:
            created_channels = json.load(f)


# Function to save created channels to JSON
def save_channels_to_json():
    with open(json_file_path, "w") as f:
        json.dump(created_channels, f)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')

    # Load the created channels from the JSON file when the bot starts
    load_channels_from_json()

    # Check if the channels still exist and delete the ones that don't
    guild = discord.utils.get(bot.guilds, id=int(vc_id))
    if guild:
        for user_id, channel_id in list(created_channels.items()):
            channel = guild.get_channel(channel_id)
            if not channel:  # If the channel doesn't exist, remove it from the dictionary
                del created_channels[user_id]
        save_channels_to_json()


@bot.event
async def on_voice_state_update(member, before, after):
    if after.channel and after.channel.id == TARGET_VOICE_CHANNEL_ID:
        # User joined the target voice channel

        # Get the user's nickname or username
        channel_name = member.nick if member.nick else member.name

        # Check if the user is currently playing a game
        game_name = ""
        if member.activity and member.activity.type == discord.ActivityType.playing:
            game_name = f" - {member.activity.name}"

        # Create an overwrite for the member with full permissions
        overwrites = {
            member: discord.PermissionOverwrite(
                manage_channels=True,
                manage_permissions=True,
                view_channel=True,
                connect=True,
                speak=True,
                mute_members=True,
                deafen_members=True,
                move_members=True,
            )
        }

        new_channel = await after.channel.guild.create_voice_channel(
            name=f"{channel_name}'s VC{game_name}",  # Include game_name if available
            category=after.channel.category,
            overwrites=overwrites
        )
        await member.move_to(new_channel)
        created_channels[member.id] = new_channel.id  # Save the channel ID instead of the object
        save_channels_to_json()
        print(f"Created channel for {member.name}: {new_channel.name}")

    elif before.channel:  # User left a voice channel
        if len(before.channel.members) == 0 and before.channel.id in created_channels.values():
            print(f"Deleting channel: {before.channel.name}")
            # Find the ID of the user who created this channel
            creator_id = next(
                (user_id for user_id, channel_id in created_channels.items() if channel_id == before.channel.id), None)
            await before.channel.delete()
            if creator_id:  # Only delete from the dictionary if we found the creator
                del created_channels[creator_id]
                save_channels_to_json()

#End MakeAVC
#Data Import



bot.run(bot_token)