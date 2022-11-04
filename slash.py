from firebase_admin import credentials
from firebase_admin import firestore
import firebase_admin
import discord
from datetime import datetime

import json
from discord.ui import Select, View
from discord.ext import commands
from discord.ui import Button
from discord import app_commands
from firebase_admin import credentials
from firebase_admin import firestore
import firebase_admin
import discord
from datetime import datetime

import json
from discord.ui import Select, View
from discord.ext import commands
from discord.ui import Button
from discord import app_commands

# get token
with open('config.json') as f:
    data = json.load(f)
    TOKEN = data["TOKEN"]

# firebase_admin
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
            await tree.sync()
            self.synced = True
        print(f"We have logged in as {self.user}")


client = aclient()
tree = app_commands.CommandTree(client)


@tree.command(name="history", description="Get history of penalties of certain user")
async def self(interaction: discord.Interaction, member: discord.User):
    user_ref = db.collection("users").document(
        str(member.id))

    if user_ref.get().exists:
        data = []
        history_ref = user_ref.collection("history")
        query = history_ref.order_by(
            "date", direction=firestore.Query.DESCENDING)
        history_results = query.stream()
        count = 0
        sum_of_points = 0
        for history_result in history_results:
            count += 1
            history_item_dict = history_result.to_dict()
            data_item = {
                "key": history_result.id,
                "date": datetime.fromtimestamp(history_item_dict['date'].timestamp()).strftime('%d/%m/%Y, %H:%M:%S'),
                "reason": history_item_dict["reason"],
                "added_points": history_item_dict["new_points"] - history_item_dict["old_points"],
                "change_points": f"{history_item_dict['old_points']} -> {history_item_dict['new_points']}"
            }
            data.append(data_item)
            sum_of_points += history_item_dict["new_points"] - \
                history_item_dict["old_points"]

        btn_next = Button(
            label="Next", style=discord.ButtonStyle.gray, emoji="▶️")
        btn_back = Button(
            label="Back", style=discord.ButtonStyle.gray, emoji="◀️")

        index = 0
        embed = discord.Embed(
            description=f"**ID:** {data[index]['key']}\n**Data:** {data[index]['date']}\n**Powód kary:** {data[index]['reason']}\n**Punktacja:** {data[index]['added_points']}\n**Zmiana punktów:** {data[index]['change_points']}",
            type="article")
        embed.set_author(
            name=f"Historia użytkownika {member.name}", icon_url=member.avatar.url)
        embed.set_footer(
            text=f"Kara {len(data) - index} z {len(data)} | Suma punktów: {sum_of_points}")

        async def btn_next_callback(interaction):
            nonlocal index, embed
            if index + 1 < len(data):
                index += 1
            embed.description = f"**ID:** {data[index]['key']}\n**Data:** {data[index]['date']}\n**Powód kary:** {data[index]['reason']}\n**Punktacja:** {data[index]['added_points']}\n**Zmiana punktów:** {data[index]['change_points']}"
            embed.set_footer(
                text=f"Kara {len(data) - index} z {len(data)} | Suma punktów: {sum_of_points}")
            await interaction.response.edit_message(embed=embed)

        async def btn_back_callback(interaction):
            nonlocal index, embed
            if index - 1 >= 0:
                index -= 1
            embed.description = f"**ID:** {data[index]['key']}\n**Data:** {data[index]['date']}\n**Powód kary:** {data[index]['reason']}\n**Punktacja:** {data[index]['added_points']}\n**Zmiana punktów:** {data[index]['change_points']}"
            embed.set_footer(
                text=f"Kara {len(data) - index} z {len(data)} | Suma punktów: {sum_of_points}")
            await interaction.response.edit_message(embed=embed)

        btn_next.callback = btn_next_callback
        btn_back.callback = btn_back_callback

        view = View()
        view.add_item(btn_back)
        view.add_item(btn_next)

        await interaction.response.send_message(view=view, embed=embed)

    else:

        embed = discord.Embed(
            description="Podany użytkownik nie posiada żadnych wprowadzonych kar do bazy danych", color=discord.Colour.red())
        embed.set_author(
            name=f"Historia użytkownika {member.name}", icon_url=member.avatar.url)
        await interaction.response.send_message(embed=embed)


@tree.command(name="add_points")
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
        await interaction.response.send_message(embed=embed)

    async def btn_cancel_callback(interaction: discord.Interaction):
        await interaction.message.delete()
        await interaction.response.send_message("deleted")

    btn_confirm.callback = btn_confirm_callback
    btn_cancel.callback = btn_cancel_callback

    view = View()
    view.add_item(btn_confirm)
    view.add_item(btn_cancel)

    await interaction.response.send_message(view=view, embed=embed)


@tree.command(name="remove_points")
async def self(interaction: discord.Interaction, member: discord.User, key: str):
    await interaction.response.send_message(f"{member} {key}")


@tree.command(name="penalties")
async def self(interaction: discord.Interaction, member: discord.User, points: int, reason: str):
    await interaction.response.send_message(f"{member}")

client.run(TOKEN)
