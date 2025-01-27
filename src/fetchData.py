"""
        This is the file that contains utility methods for dealing with interactions between the Discord bot and MongoDB
        @author Kory Stennett
"""

import random

from string import ascii_letters

from src.items.torso_armor import TorsoArmor
from src.items.weapon import Weapon

ENCRYPTION_LENGTH = 6
ITEM_ENCRYPTION_LENGTH = 8


def scramble_attack_id(_id: int) -> str:
    """
    Creates a random ID using the Discord user ID combined with random letters from the alphabet and then scrambled.
    :param _id: Discord user ID
    :return: a randomized ID to attack players with
    """
    chars = random.choices(
        ascii_letters,
        k=ENCRYPTION_LENGTH
    )
    chars.extend(str(_id))
    random.shuffle(chars)
    return ''.join(chars)


def scramble_id(_id: int) -> str:
    """
    Creates a random ID using the Discord user ID combined with random letters from the alphabet and then scrambled.
    :param _id: Discord user ID
    :return: a randomized ID
    """
    chars = random.choices(
        ascii_letters,
        k=ITEM_ENCRYPTION_LENGTH
    )
    chars.extend(str(_id))
    random.shuffle(chars)
    return ''.join(chars)


async def update_attack_id(bot, _id):
    """
    Update the player's attack ID whenever they take certain actions. This is meant
    to be called throughout the project.
    :param bot: the Discord bot
    :param _id: Discord user ID to change
    :return: Nothing
    """
    db = bot.mongoConnect["DiscordBot"]
    collection = db["Economy"]
    data = await collection.find_one({"_id": _id})
    attack_id = scramble_attack_id(_id)
    data["attackID"] = attack_id
    await collection.replace_one({"_id": _id}, data)


async def find_by_attack_id(bot, attack_id: str):
    """
    Finds a player to attack by targeting their attack ID
    :param bot: the Discord bot from main.py
    :param attack_id: string
    :return: player data document from MongoDB
    """
    db = bot.mongoConnect["DiscordBot"]
    collection = db["Economy"]
    data = await collection.find_one({"attackID": attack_id})
    return data


async def fetch_player_map_info(bot, _id):
    db = bot.mongoConnect["DiscordBot"]
    #   automatically creates genre if not present
    collection = db["WorldMap"]
    data = {
        "_id": _id,
        "position": {"horizontal": 0, "vertical": 0},
        "steps": 0
    }
    if await collection.find_one({"_id": _id}) is None:
        await collection.insert_one(data)
        return data, collection
    data = await collection.find_one({"_id": _id})
    return data, collection


async def update_world_map(bot, _id, position, steps):
    """
    Updates the database of the player's coordinates on the world map
    which is relevant during exploration.
    :param steps: int
    :param bot: Discord bot
    :param _id: Discord user ID
    :param position: a dict, looking like this:
        position = {
            "horizontal": int, "vertical": int
        }
    :return: Nothing
    """
    db = bot.mongoConnect["DiscordBot"]
    #   automatically creates genre if not present
    collection = db["WorldMap"]
    data = {
        "_id": _id,
        "position": position,
        "steps": steps
    }
    if await collection.find_one({"_id": _id}) is None:
        await collection.insert_one(data)
    else:
        await collection.replace_one({"_id": _id}, data)


async def fetch_data(bot, _id):
    """
    The main way to get information about a user, and gather the entire user profile collection
        If a user doesn't get found by ID, they're created automatically.
    :param bot: discord bot
    :param _id: user ID to search for
    :return: userData, collection
    """
    db = bot.mongoConnect["DiscordBot"]
    attack_id = scramble_attack_id(_id)
    collection = db["Economy"]
    # BIG NOTE: This should definitely not exist on a massive scale, it would blow up the database. It's just here
    # while I figure out which variables I want to track on my profiles. It is a hacky way to put new variables on every
    # user profile in the database
    """
    More info on this method:
        It uses a pipeline to do something to a set of documents in a collection.
        In my case, the first parameter is query and it is blank because we're searching for everything 
        The second parameter is what we're actually doing with the documents, which is set a new variable to something
        The final parameter is necessary for update_many and doesn't really influence our situation 
    """
    # await collection.update_many(
    #   {},
    #   {"$set": {"position": {"horizontal": 0, "vertical": 0}}},

    #   upsert=False

    # )

    if await collection.find_one({"_id": _id}) is None:
        new_data = {
            "_id": _id,
            "coins": 0,
            "bank": 0,
            "cups": 0,
            "boxes": 1,
            "cardboard": 0,
            "binoculars": 0,
            "sunglasses": 0,
            "picUrl": "",
            "attackID": attack_id,
            "position": {"horizontal": 0, "vertical": 0},
            "watchLater": []
        }
        await collection.insert_one(new_data)
    return await collection.find_one({"_id": _id}), collection


async def remove_account(bot, _id):
    """
    A quick and dirty way to remove account and allow users to reset their profiles.
        It deletes the document if it exists, but the user can only delete their own account.
    :param bot: discord bot
    :param _id: user ID
    :return: Nothing
    """
    db = bot.mongoConnect["DiscordBot"]
    collection = db["Economy"]
    query = {"_id": _id}
    collection.delete_one(query)
    collection = db["Inventory"]
    query = {"_id": _id}
    collection.delete_one(query)
    collection = db["WorldMap"]
    query = {"_id": _id}
    collection.delete_one(query)


async def remove_meme(bot, url):
    """
    Removes memes from the reactions collection on MongoDB
    :param bot: discord bot
    :param url: image URL
    :return: Nothing
    """
    db = bot.mongoConnect["DiscordBot"]
    #   automatically creates genre if not present
    collection = db["reactions"]
    query = {"_id": url}
    collection.delete_one(query)


async def add_meme(bot, genre, url):
    """
    Add meme to the database (it is checked for authenticity beforehand)
        It follows the data scheme of { "_id": url, "genre": genre }
        That means the same image can only be uploaded once because it would recognize that URL
        and we are only accepting images and gifs from links/URLs.
    :param bot: discord bot
    :param genre: str
    :param url: str
    :return: Nothing
    """
    db = bot.mongoConnect["DiscordBot"]
    #   automatically creates genre if not present
    collection = db["reactions"]
    data = {
        "_id": url,
        "genre": genre
    }
    await collection.insert_one(data)


async def fetch_meme(bot, genre):
    """
    Grab a random meme from the database based on genre (like confused, happy, sad)
    :param bot: discord bot
    :param genre: str
    :return: meme = {
        "_id": url,
        "genre": genre
    }
    """
    db = bot.mongoConnect["DiscordBot"]
    #   automatically creates genre if not present
    collection = db["reactions"]
    meme = "No meme found"
    async for doc in collection.aggregate([
        {"$match": {"genre": genre}},
        {"$sample": {"size": 1}}
    ]):
        meme = doc
    return meme


async def fetch_inventory(bot, _id):
    """
    Grabs the player's inventory if it exists, otherwise creates one for them.
    :param bot: discord bot
    :param _id: user ID to search for
    :return: userInventory: list, collection
    """
    db = bot.mongoConnect["DiscordBot"]
    collection = db["Inventory"]

    if await collection.find_one({"_id": _id}) is None:
        new_data = {
            "_id": _id,
            "inventory_weapon": [],
            "inventory_torso": []
        }
        await collection.insert_one(new_data)
    return await collection.find_one({"_id": _id}), collection


async def update_banks(bot):
    """
    Updates the banks based on how much gold is in them. Going interest rate is 3%!
    :param bot:
    :return:
    """
    db = bot.mongoConnect["DiscordBot"]
    collection = db["Economy"]
    await collection.update_many(
        {},
        {"$mul": {"bank": 1.03}},
        upsert=False

    )


async def fetch_auction_items(bot):
    db = bot.mongoConnect["DiscordBot"]
    collection = db["AuctionHouse"]
    return collection


async def add_to_auction_house(bot, item: dict, price: int, user_id: int):
    db = bot.mongoConnect["DiscordBot"]
    collection = db["AuctionHouse"]
    if await collection.find_one({"_id": item["item_id"]}) is None:
        if price > 2000000000:
            price = 2000000000
        new_data = {
            "_id": item["item_id"],
            "item": item,
            "price": price,
            "owner_id": user_id,
        }
        await collection.insert_one(new_data)
        return True
    else:
        return False


def make_weapon_serializable(weapon: Weapon):
    weapon_dict ={
        "name":weapon.name,
        "dmg":weapon.damage,
        "description":weapon.description,
        "rarity":weapon.rarity.value,
        "item_id":weapon.item_id,
        "type":"weapon"
                  }
    return weapon_dict


def make_torso_serializable(armor: TorsoArmor):
    armor_dict ={
        "name":armor.name,
        "def":armor.defense,
        "description":armor.description,
        "rarity":armor.rarity.value,
        "item_id":armor.item_id,
        "type": "torso"
                  }
    return armor_dict
