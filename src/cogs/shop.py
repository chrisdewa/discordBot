import asyncio.exceptions

from discord.ext import commands
from discord.ui import Select, View
import discord
from src.items.drink import Drink
from src.items.randomizeItem import randomize_food, randomize_drink, randomize_weapon, randomize_armor
from src.fetchData import fetch_inventory, make_weapon_serializable, make_torso_serializable


class FoodCourtSelectMenu(Select):
    def __init__(self,_id):
        self.food = randomize_food(_id)
        self.food_description = f"{self.food.name}: Heal: {self.food.healing}, Stam: {self.food.stamina}" \
                                f" Cost: {self.food.cost}"

        self.drink = randomize_drink(_id)
        self.drink_description = f"{self.drink.name}: Heal: {self.drink.healing}, Stam: {self.drink.stamina}" \
                                 f"Cost: {self.drink.cost}"
        print(self.food.name)
        print(self.food.healing)
        print(self.food.stamina)
        print(self.food.cost)
        super(FoodCourtSelectMenu, self).__init__(
            placeholder="Consumables",
            max_values=1,
            options=[
                # label is required
                discord.SelectOption(label="Food",
                                     emoji="🍖",
                                     description=self.food_description),
                discord.SelectOption(label="Drink",
                                     emoji="🍺",
                                     description=self.drink_description),
            ]

        )

    async def callback(self, interaction: discord.Interaction):
        description = ""
        # user = interaction.user
        if self.values[0] == "Food":
            description = f"Ate {self.food.name}. {self.food.description}\nHealed for {self.food.healing}\n" \
                          f"Stamina regenerated by {self.food.stamina}\n" \
                          f"Cost: {self.food.cost}\n" \
                          f"Rarity: {self.food.rarity}"
        elif self.values[0] == "Drink":
            description = f"Drank {self.drink.name}. {self.drink.description}\nHealed for {self.drink.healing}\n" \
                          f"Stamina regenerated by {self.drink.stamina}\n" \
                          f"Cost: {self.drink.cost}\n" \
                          f"Rarity: {self.drink.rarity}"
        self.view.remove_item(self)
        await interaction.response.edit_message(content=f"{description}",view=self.view)


class GambleItemSelectMenu(Select):
    def __init__(self,bot,_id):
        self.bot = bot
        self.weapon = randomize_weapon(_id)
        self.armor = randomize_armor(_id)
        self.placeholderText = "Items"
        if self.weapon.rarity.value == 5 or self.armor.rarity.value == 5:
            self.placeholderText += " * Legendary Appeared *"
        self.weapon_description = f"{self.weapon.name}\n" \
                                  f"Dmg: {self.weapon.damage}\n" \
                                  f"Cost: {self.weapon.cost}"
        if len(self.weapon_description) > 80:
            self.weapon_description = f"Dmg: {self.weapon.damage}\n" \
                                      f"Cost: {self.weapon.cost}\n" \
                                      f"{self.weapon.rarity}"
        self.armor_description = f"{self.armor.name}\n" \
                                 f"Def: {self.armor.defense}\n" \
                                 f"Cost: {self.armor.cost}"
        if len(self.armor_description) > 80:
            self.armor_description = f"Def: {self.armor.defense}\n" \
                                      f"Cost: {self.armor.cost}\n" \
                                      f"{self.armor.rarity}"

        super(GambleItemSelectMenu, self).__init__(
            placeholder=self.placeholderText,
            options=[
                # label is required
                discord.SelectOption(label="Gamble Weapon",
                                     emoji="⚔",
                                     description=self.weapon_description),

                discord.SelectOption(label="Gamble Armor",
                                     emoji="🛡",
                                     description=self.armor_description)
            ]
        )

    async def callback(self, interaction):
        description = ""
        inventory, collection = await fetch_inventory(self.bot, interaction.user.id)
        if self.values[0] == "Gamble Weapon":
            description = f"Bought a {self.weapon.name}. \n{self.weapon.description}\nDamage: {self.weapon.damage}\n" \
                          f"Cost: {self.weapon.cost}\n" \
                          f"Rarity: {self.weapon.rarity}"
            inventory["inventory_weapon"].append(make_weapon_serializable(self.weapon))

        elif self.values[0] == "Gamble Armor":
            description = f"Bought a {self.armor.name}. \n{self.armor.description}\nDefense: {self.armor.defense}\n" \
                          f"Cost: {self.armor.cost}\n" \
                          f"Rarity: {self.armor.rarity}"
            inventory["inventory_torso"].append(make_torso_serializable(self.armor))

        self.view.remove_item(self)
        """if len(inv) > 10:
            description = "Can't buy because your inventory is full. Replace lowest damage item?"
            await interaction.response.edit_message(content=f"{description}", view=self.view)
            try:
                choice = await self.bot.wait_for('message', timeout=30)
            except asyncio.exceptions.TimeoutError:
                await interaction.followup.edit_message(content=f"Manually delete an item before trying to buy next time.", view=self.view, message_id=interaction.id)
                return
            if choice.content == "yes":
                await interaction.followup.edit_message(content=f"Replaced!", view=self.view, message_id=interaction.message.id)
            else:
        """       # return
        #else:
        await collection.replace_one({"_id": interaction.user.id}, inventory)
        await interaction.response.edit_message(content=f"{description}", view=self.view)


class ShopView(View):
    def __init__(self, bot, ctx):
        self.bot = bot
        self.ctx = ctx

        super(ShopView, self).__init__()
        self.food_shop = FoodCourtSelectMenu(ctx.author.id)
        self.add_item(self.food_shop)
        self.item_shop = GambleItemSelectMenu(self.bot,ctx.author.id)
        self.add_item(self.item_shop)


class Shop(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.cooldown(3, 10, commands.BucketType.user)
    @commands.command(name="shop", help="Buy from the random item shop.")
    async def shop(self, ctx: commands.Context):
        """
        Buy from the random item shop.
        """
        view = ShopView(self.bot, ctx)
        await ctx.send("Shop:", view=view)


async def setup(bot: commands.Bot):

    await bot.add_cog(
        Shop(bot)
    )
