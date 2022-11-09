from firebase_admin import credentials
from firebase_admin import firestore
import firebase_admin
import discord
from datetime import datetime
import math
import random

import json
from discord.ui import Select, View, TextInput
from discord.ext import commands
from discord.ui import Button
import discord.utils
from discord import CategoryChannel, app_commands
from firebase_admin import credentials
from firebase_admin import firestore
import firebase_admin
import discord
from discord.ext.commands import has_permissions
from datetime import datetime

import json
from discord.ui import Select, View
from discord.ext import commands
from discord.ui import Button
from discord import app_commands

# Get token from config.json
with open('config.json') as f:
    data = json.load(f)
    TOKEN = data["TOKEN"]
    GUILD_ID = int(data["GUILD"])
    EVENTS_CATEGORY_ID = int(data["EVENTS_CATEGORY"])

# Firebase setup
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()


class aclient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        self.synced = False

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            await tree.sync(guild=discord.Object(id=GUILD_ID))
            self.synced = True
        print(f"We have logged in as {self.user}")


client = aclient()
tree = app_commands.CommandTree(client)


@tree.command(name='help', guild=discord.Object(id=GUILD_ID))
async def self(interaction: discord.Interaction):

    isAdmin = False
    if interaction.permissions.administrator:
        isAdmin = True

    if isAdmin:
        # Create embed for admins
        embed = discord.Embed(
            description=f'**Komendy:**\n`history`, `add_points`, `remove_points`', type='article')
        embed.set_author(name=f'Lista komend',
                         icon_url=client.application.icon.url)
    else:
        # Create embed for users
        embed = discord.Embed(
            description=f'**Komendy:**\n`history`', type='article')
        embed.set_author(name=f'Lista komend',
                         icon_url=client.application.icon.url)

    # Send interaction
    await interaction.response.send_message(embed=embed)


@tree.command(name="history", description="Pokazuje historię warnów", guild=discord.Object(id=GUILD_ID))
async def self(interaction: discord.Interaction, member: discord.User):

    if interaction.permissions.administrator == False and member.id is not interaction.user.id:
        embed = discord.Embed(
            description="Nie masz uprawnień do sprawdzenia historii kar innego użytkownika!", color=discord.Colour.red())
        embed.set_author(
            name=f"Historia użytkownika {member.name}", icon_url=member.avatar.url)
        await interaction.response.send_message(embed=embed)
        return

    embed = discord.Embed(type="article")
    sum_of_points = 0
    description = ""

    user_ref = db.collection("users").document(
        str(member.id))

    if user_ref.get().exists:
        history_ref = user_ref.collection("history")
        query = history_ref.order_by(
            "date", direction=firestore.Query.DESCENDING)
        history_results = query.stream()

        for idx, history_result in enumerate(history_results):
            history_item_dict = history_result.to_dict()

            key = history_result.id
            date = datetime.fromtimestamp(
                history_item_dict['date'].timestamp()).strftime('%d/%m/%Y, %H:%M:%S')
            reason = history_item_dict["reason"]
            added_points = history_item_dict["new_points"] - \
                history_item_dict["old_points"]

            if interaction.permissions.administrator:
                description += f"`Index: {idx + 1} | Key: {key}`\n**Date:** {date}\n**Powód:** {reason}\n**Punktacja:** {added_points}\n\n"
            else:
                description += f"`Index: {idx + 1}`\n**Date:** {date}\n**Powód:** {reason}\n**Punktacja:** {added_points}\n\n"

            sum_of_points += history_item_dict["new_points"] - \
                history_item_dict["old_points"]

        embed.description = description
        embed.set_author(
            name=f"Historia użytkownika {member.name}", icon_url=member.avatar.url)
        embed.set_footer(
            text=f"Suma punktów: {sum_of_points}")

        await interaction.response.send_message(embed=embed)

    else:
        embed = discord.Embed(
            description="Podany użytkownik nie posiada żadnych wprowadzonych warnów do bazy danych", color=discord.Colour.red())
        embed.set_author(
            name=f"Historia użytkownika {member.name}", icon_url=member.avatar.url)
        await interaction.response.send_message(embed=embed)


@tree.command(name="add_points", description="Dodaje warna użytkownikowi", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(administrator=True)
async def self(interaction: discord.Interaction, member: discord.User, points: int, reason: str):

    user_ref = db.collection("users").document(str(member.id))
    if user_ref.get().exists:
        actual_points = user_ref.get().to_dict()["points"]
    else:
        actual_points = 0

    embed = discord.Embed(
        description=f"**Powód:** {reason}\n**Punkty za warna:** {points}\n**Aktualne punkty:** {actual_points}", type="article")
    embed.set_author(
        name=f"Dodanie warna użytkownikowi {member.name}", icon_url=member.avatar.url)

    btn_confirm = Button(
        label="Confirm", style=discord.ButtonStyle.green, emoji="✔️")
    btn_cancel = Button(
        label="Cancel", style=discord.ButtonStyle.red, emoji="✖️")

    async def btn_confirm_callback(interaction: discord.Interaction):
        nonlocal embed
        user_ref = db.collection("users").document(str(member.id))
        user_data = user_ref.get()
        if user_data.exists:
            # set user's points
            user_points = user_data.to_dict()["points"]
            user_ref.set({
                "points": user_points + points
            })

            # add item to history
            user_ref.collection("history").add({
                "new_points": user_points + points,
                "old_points": user_points,
                "reason": reason,
                "date": datetime.now()
            })

        else:
            # create new user
            user_ref.set({"points": points})
            user_ref.collection("history").add({
                "new_points": points,
                "old_points": 0,
                "reason": reason,
                "date": datetime.now()
            })
        embed.description = f"Warn został dodany pomyślnie\n**Aktualne punkty:** {actual_points}"
        embed.color = discord.Colour.green()
        embed.set_author(
            name=f"Dodanie warna użytkownikowi {member.name}", icon_url=member.avatar.url)
        await interaction.response.edit_message(embed=embed, view=None)

    async def btn_cancel_callback(interaction: discord.Interaction):
        await interaction.response.edit_message(content="canceled", embed=None, view=None)

    btn_confirm.callback = btn_confirm_callback
    btn_cancel.callback = btn_cancel_callback

    view = View()
    view.add_item(btn_confirm)
    view.add_item(btn_cancel)

    await interaction.response.send_message(view=view, embed=embed)


@tree.command(name="remove_points", description="Usuwa warna użytkownikowi", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(administrator=True)
async def self(interaction: discord.Interaction, member: discord.User, key: str):

    history_ref = db.collection("users").document(
        str(member.id)).collection("history").document(str(key))
    if history_ref.get().exists:
        reason = history_ref.get().to_dict()["reason"]
        date = datetime.fromtimestamp(
            history_ref.get().to_dict()['date'].timestamp()).strftime('%d/%m/%Y, %H:%M:%S')
        points = history_ref.get().to_dict(
        )["new_points"] - history_ref.get().to_dict()["old_points"]

        embed = discord.Embed(
            description=f"**ID:** {key}\n**Data:** {date}\n**Powód kary:** {reason}\n**Punktacja:** {points}", type="article")
        embed.set_author(
            name=f"Usunięcie warna użytkownikowi {member.name}", icon_url=member.avatar.url)

        btn_confirm = Button(
            label="Confirm", style=discord.ButtonStyle.green, emoji="✔️")
        btn_cancel = Button(
            label="Cancel", style=discord.ButtonStyle.red, emoji="✖️")

        async def btn_confirm_callback(interaction):
            history_ref.delete()
            embed = discord.Embed(
                description=f"Pomyślnie usunięto warna użytkownika {member.name}", color=discord.Colour.green())
            embed.set_author(
                name=f"Usunięcie warna użytkownika {member.name}", icon_url=member.avatar.url)
            await interaction.response.edit_message(embed=embed, view=None)

        async def btn_cancel_callback(interaction):
            await interaction.response.edit_message(
                content="canceled", view=None, embed=None)

        btn_confirm.callback = btn_confirm_callback
        btn_cancel.callback = btn_cancel_callback

        view = View()
        view.add_item(btn_confirm)
        view.add_item(btn_cancel)

        await interaction.response.send_message(view=view, embed=embed)
    else:
        embed = discord.Embed(
            description="Podany użytkownik nie posiada warna o takim ID", color=discord.Colour.red())
        embed.set_author(
            name=f"Usunięcie warna użytkownikowi {member.name}", icon_url=member.avatar.url)
        await interaction.response.send_message(embed=embed)


@tree.command(name='team_gen', description='Generuje drużyny na podstawie podanych osób', guild=discord.Object(id=GUILD_ID))
async def self(interaction: discord.Interaction, members: str):
    # Create embed
    embed = discord.Embed(description=f'', type='article')
    embed.set_author(name=f'Tworzenie drużyn',
                     icon_url=interaction.user.avatar.url)

    # Create teams
    members = members.split(',')
    teams = [[], []]
    random.shuffle(members)
    for i in range(len(members)):
        teams[i % 2].append(members[i])

    # Add teams to embed
    embed.description = f'**Drużyna 1:** {", ".join(teams[0])}\n**Drużyna 2:** {", ".join(teams[1])}'

    # Send interaction
    await interaction.response.send_message(embed=embed)


@tree.command(name='create_event', description='Tworzy event, razem z kanałem', guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(administrator=True)
async def self(interaction: discord.Interaction, name: str, date: str, voice_channel: discord.VoiceChannel):

    async def create_new_embed(count_users):
        embed = discord.Embed(
            description=f'**Data:** {date}\n**Ilość osób:** {count_users}', type='article')
        embed.set_author(name=f'Event {name}',
                         icon_url=interaction.user.avatar.url)
        return embed

    start_time = discord.utils.snowflake_time(
        discord.utils.time_snowflake(datetime.strptime(date, '%d/%m/%Y %H:%M:%S')))

    event = await interaction.guild.create_scheduled_event(name=name, channel=voice_channel, start_time=start_time)

    events_ref = db.collection('events')
    events_ref.document(str(event.id)).set({
        "date": datetime.strptime(date, '%d/%m/%Y %H:%M:%S'),
        "image": "",
        "name": name,
    })
    category = discord.Object(id=EVENTS_CATEGORY_ID)
    channel = await interaction.guild.create_text_channel(name="chuj", category=category)
    count_users = 0

    btn_join = Button(label='Zapisz się',
                      style=discord.ButtonStyle.green, emoji='✅')

    async def btn_join_callback(interaction):
        nonlocal count_users
        if interaction.user.dm_channel is None:
            await interaction.user.create_dm()
        if events_ref.document(str(event.id)).collection("participants").document(str(interaction.user.id)).get().exists:
            await interaction.user.dm_channel.send("Już jesteś zapisany na tym evencie")
        else:
            count_users += 1
            events_ref.document(str(event.id)).collection(
                "participants").document(str(interaction.user.id)).set({})
            await interaction.user.dm_channel.send("Zostałeś zapisany na event!")
        await message.edit(embed=await create_new_embed(count_users), view=view)
        await interaction.response.defer()

    btn_join.callback = btn_join_callback

    view = View()
    view.add_item(btn_join)

    message = await channel.send(embed=await create_new_embed(count_users), view=view)

    await interaction.response.send_message(content='Creating event...')


# Run bot
client.run(TOKEN)
