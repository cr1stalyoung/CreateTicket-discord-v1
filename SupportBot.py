import os
import sqlite3
import disnake
from disnake.ext import commands
from disnake import TextInputStyle
from datetime import datetime, timezone


bot = commands.Bot(
    command_prefix='!',
    help_command=None,
    intents=disnake.Intents.all()

)


@bot.event
async def on_ready():
    # start of adding embed "Support"
    id_channel = 1234567890 # id of the text channel to which the embed will be sent
    embedOne = disnake.Embed(title="", description="", color=disnake.Color(int("4e5058", 16)))
    file = disnake.File('name_file.jpg', filename='name_file.jpg')
    embedOne.set_image(url=f'attachment://name_file.jpg')
    em = disnake.Embed(title="```                            Support                            ```", description="", color=disnake.Color(int("4e5058", 16)))
    em.add_field(
        name="",
        value="**Got a problem? Want to suggest an idea\n for the server? We can help you!**\n"
              "**```Click on the button below to contact our server support ↓```**",
        inline=False
    )
    ticket = disnake.ui.Button(style=disnake.ButtonStyle.green, label="Get help from the Server Administration", custom_id="support")
    await bot.get_channel(id_channel).send(file=file)
    await bot.get_channel(id_channel).send(embed=em, components=ticket)
    # end of adding embed "Support"


@bot.event
async def on_error(event, *args, **kwargs):
    error = args[0]
    print(f"An error occurred during a {event}: {error}")


class SQLiteDatabase():
    def __init__(self, db_file):
        self.db_file = db_file
        self.connection = None
        self.cursor = None

    def connect(self):
        try:
            self.connection = sqlite3.connect(self.db_file)
            self.cursor = self.connection.cursor()
        except sqlite3.Error as e:
            print("Error connecting to the database:", e)

    def execute_query(self, query, params=None):
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            self.connection.commit()
        except sqlite3.Error as e:
            print("Error executing the query:", e)

    def fetch_one(self, query, params=None):
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            rows = self.cursor.fetchone()
            return rows
        except sqlite3.Error as e:
            print("Error fetching data from the database:", e)

    def fetch_all(self, query, params=None):
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            rows = self.cursor.fetchall()
            return rows
        except sqlite3.Error as e:
            print("Error fetching data from the database:", e)

    def close(self):
        try:
            self.connection.close()
        except sqlite3.Error as e:
            print("Error closing the database connection:", e)


class CloseSupport(disnake.ui.View):
    def __init__(self, db):
        self.db = db
        super().__init__()

    @disnake.ui.button(label='🔒 Close ticket')
    async def close_ticket(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):

        self.db.execute_query('DELETE FROM support_time WHERE messageID = ?', (interaction.channel.id,))
        await interaction.channel.delete()


class Application(disnake.ui.Modal):
    def __init__(self, db):
        self.db = db
        components = [
            disnake.ui.TextInput(
                label="Subject:",
                placeholder="Subject of the appeal",
                custom_id="subject",
                style=TextInputStyle.short,
                max_length=50,
            ),
            disnake.ui.TextInput(
                label="Description:",
                placeholder="Describe in detail the essence of the application.",
                custom_id="Description:",
                style=TextInputStyle.paragraph,
            ),
        ]
        super().__init__(
            title="Support",
            custom_id="create_tag",
            timeout=180,
            components=components,
        )

    async def callback(self, inter: disnake.ModalInteraction):
        await inter.response.defer(ephemeral=True)
        category = inter.guild.get_channel(id_category)
        overwrites = {
            inter.guild.default_role: disnake.PermissionOverwrite(read_messages=False),
            inter.user: disnake.PermissionOverwrite(read_messages=True),
        }
        channel = await category.create_text_channel(f'⭕│appeal', overwrites=overwrites)
        embedOne = disnake.Embed(title="", description="", color=disnake.Color(int("4e5058", 16)))
        file = disnake.File('name_file.jpg', filename='name_file.jpg')
        embedOne.set_image(url=f'attachment://name_file.jpg')
        em = disnake.Embed(title="```                       Support                       ```", description="", color=disnake.Color(int("4e5058", 16)))
        em.add_field(
            name="",
            value="**For advertising and cooperation: **\n"
                  "**```The server administration will reply soon.```**",
            inline=False
        )
        embed = disnake.Embed(title="Appeal:", description="", color=disnake.Color(int("4e5058", 16)))
        for key, value in inter.text_values.items():
            if len(value) < 50:
                value = value.ljust(50)
            new_text = ''
            for i in range(0, len(value), 50):
                new_text += value[i:i + 50] + '\n'
            embed.add_field(
                name=key.capitalize(),
                value=f"```{new_text}```",
                inline=False,
            )
        ticket = disnake.ui.Button(style=disnake.ButtonStyle.gray, label="🔒 Close appeal", custom_id=f"delTicket:{inter.user.id}")
        await channel.send(content=f"<@{inter.user.id}>", file=file, embeds=[embedOne, em, embed], components=ticket)
        self.db.execute_query("INSERT INTO support_time (userID, messageID) VALUES (?, ?)", (inter.user.id, channel.id))
        embed = disnake.Embed(
            title="",
            description=f"📩 Your appeal was created.\nClick on <#{channel.id}>, to pass.",
            color=disnake.Color(int("4e5058", 16)), timestamp=datetime.now(timezone.utc))
        await inter.edit_original_response(embed=embed)


@bot.event
async def on_button_click(interaction):
    db = SQLiteDatabase(os.path.join("name_folder", "name_file_db.db")) # sqlite is used in the code, it is required to specify the path to the database file
    db.connect()
    if interaction.component.custom_id == "support":
        data = db.fetch_one('SELECT userID, messageID FROM support_time WHERE userID = ?', (interaction.user.id,))
        if data is None:
            await interaction.response.send_modal(modal=Application(db))
        else:
            embed = disnake.Embed(
                title="",
                description=f"⚠️ You already have a previous open appeal.\nYour appeal - <#{data[1]}>",
                color=disnake.Color(int("ff3737", 16)), timestamp=datetime.now(timezone.utc))
            await interaction.response.send_message(embed=embed, ephemeral=True)
    elif interaction.component.custom_id.startswith("delTicket:"):
        split_msg_id = interaction.component.custom_id.split(":")[1]
        if interaction.user.id == int(split_msg_id):
            db.execute_query('DELETE FROM support_time WHERE messageID = ?', (interaction.channel.id,))
            await interaction.channel.delete()

bot.run("TOKEN")