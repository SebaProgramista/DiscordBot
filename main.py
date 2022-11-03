from tokenize import Number
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

# prefix
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

# firebase_admin
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()


@bot.event
async def on_ready():
    print("Discord bot is online and ready!")


@bot.command()
async def ping(ctx):
    await ctx.send(f"PONG! {round(bot.latency * 1000)} ms")


@bot.command()
async def add_points(ctx, member: discord.User, penalty_id):

    embed = discord.Embed(title=f"Dodawanie punktów dla {member.name}")

    penalty_ref = db.collection("penalties").document(penalty_id)
    penalty_data = penalty_ref.get()
    if penalty_data.exists == False:
        await ctx.send("Kara o takim id nie istnieje")
        return 0

    user_ref = db.collection("users").document(str(member.id))
    user_data = user_ref.get()
    if user_data.exists:
        # set user's points
        user_points = user_data.to_dict()["points"]
        user_ref.set({
            "points": user_points + penalty_data.to_dict()["points"]
        })

        # add item to history
        user_ref.collection("history").add({
            "new_points": user_points + penalty_data.to_dict()["points"],
            "old_points": user_points,
            "reason": penalty_data.to_dict()["reason"],
            "date": datetime.now()
        })

        # add fields to embed
        embed.add_field(name="Powód kary", value=penalty_data.to_dict()[
                        "reason"], inline=False)
        embed.add_field(name="Punktacja kary", value=penalty_data.to_dict()[
                        "points"], inline=False)
        embed.add_field(name="Aktualne punkty", value=user_points +
                        penalty_data.to_dict()["points"], inline=False)

    else:
        # create new user
        user_ref.set({"points": penalty_data.to_dict()["points"]})
        user_ref.collection("history").add({
            "new_points": penalty_data.to_dict()["points"],
            "old_points": 0,
            "reason": penalty_data.to_dict()["reason"],
            "date": datetime.now()
        })

        # add fields to embed
        embed.add_field(name="Powód kary", value=penalty_data.to_dict()[
                        "reason"], inline=False)
        embed.add_field(name="Punktacja kary", value=penalty_data.to_dict()[
                        "points"], inline=False)
        embed.add_field(name="Aktualne punkty", value=penalty_data.to_dict()[
                        "points"], inline=False)

    await ctx.send(embed=embed)


@bot.command()
async def add_penalty(ctx, id, points: int, *reason):
    reason = " ".join(reason)

    penalty_ref = db.collection("penalties").document(str(id))
    penalty_data = penalty_ref.get()
    if penalty_data.exists == False:
        await ctx.send("Kara o takim id nie istnieje")
        penalty_ref.set({
            "points": points,
            "reason": reason
        })
    else:
        await ctx.send("Kara o takim id istnieje")


@bot.command()
async def penalties(ctx):
    # embed = discord.Embed(title="Przewinienia i ich punktacja")

    # select = Select(placeholder="Wybierz przewinienie")

    # get penalties from firebase
    # penalty_data = db.collection("penalties").stream()
    # for penalty in penalty_data:
    #     select.add_option(
    #         label=f"punkty: {penalty.to_dict()['points']}", description=penalty.to_dict()["reason"], value=penalty.id)
    # view = View()
    # view.add_item(select)
    # await ctx.send(view=view)

    with open('Assets/punktacja_kar.jpg', 'rb') as f:
        picture = discord.File(f)
        await ctx.send(file=picture)


@bot.command()
async def get_history(ctx, member: discord.User):

    user_ref = db.collection("users").document(
        str(member.id))

    if user_ref.get().exists:
        history_ref = user_ref.collection("history")
        query = history_ref.order_by(
            "date", direction=firestore.Query.DESCENDING)
        history_results = query.stream()
        count = 0
        sum_of_points = 0
        for history_result in history_results:
            count += 1
            history_item_dict = history_result.to_dict()
            await ctx.send(f"""`Index: {count}`
        **Data:** {datetime.fromtimestamp(history_item_dict['date'].timestamp()).strftime('%m/%d/%Y, %H:%M:%S')}
        **Powód kary:** {history_item_dict["reason"]}
        **Punktacja kary:** {history_item_dict["new_points"] - history_item_dict["old_points"]}""")
            sum_of_points += history_item_dict["new_points"] - \
                history_item_dict["old_points"]
        await ctx.send(f"`Suma punktów: {sum_of_points}`")

tree = app_commands.CommandTree(client=discord)


@tree.command(name="Test ui", description="Testing new UI")
async def test_ui(interaction: discord.Interaction):
    btn_next = Button(label="Next",
                      style=discord.ButtonStyle.gray,
                      emoji="▶️")

    btn_back = Button(label="Back", style=discord.ButtonStyle.gray, emoji="◀️")

    async def button_callback(interaction):
        await interaction.response.send_message("Hi!")

    btn_next.callback = button_callback

    view = View()
    view.add_item(btn_next)
    await interaction.response.send_message("Hi!", view=view)

bot.run(TOKEN)
