# Object classes from AP core, to represent an entire MultiWorld and this individual World that's part of it
from worlds.AutoWorld import World
from BaseClasses import MultiWorld, CollectionState, Item

# Object classes from Manual -- extending AP core -- representing items and locations that are used in generation
from ..Items import ManualItem
from ..Locations import ManualLocation
from .Options import LevelItems, Faction, XPRateItems

# Raw JSON data from the Manual apworld, respectively:
#          data/game.json, data/items.json, data/locations.json, data/regions.json
#
from ..Data import game_table, item_table, location_table, region_table

# These helper methods allow you to determine if an option has been set, or what its value is, for any player in the multiworld
from ..Helpers import is_option_enabled, get_option_value, format_state_prog_items_key, ProgItemsCat

# calling logging.info("message") anywhere below in this file will output the message to both console and log file
import logging, re

########################################################################################
## Order of method calls when the world generates:
##    1. create_regions - Creates regions and locations
##    2. create_items - Creates the item pool
##    3. set_rules - Creates rules for accessing regions and locations
##    4. generate_basic - Runs any post item pool options, like place item/category
##    5. pre_fill - Creates the victory location
##
## The create_item method is used by plando and start_inventory settings to create an item from an item name.
## The fill_slot_data method will be used to send data to the Manual client for later use, like deathlink.
########################################################################################



# Use this function to change the valid filler items to be created to replace item links or starting items.
# Default value is the `filler_item_name` from game.json
def hook_get_filler_item_name(world: World, multiworld: MultiWorld, player: int) -> str | bool:
    return False

# Called before regions and locations are created. Not clear why you'd want this, but it's here. Victory location is included, but Victory event is not placed yet.
def before_create_regions(world: World, multiworld: MultiWorld, player: int):
    pass

# Called after regions and locations are created, in case you want to see or modify that information. Victory location is included.
def after_create_regions(world: World, multiworld: MultiWorld, player: int):
    expansion = get_option_value(multiworld, player, "goal")

    # Map numeric values to expansion names and max levels
    expansion_map = {
        0: ("Vanilla", 60),
        1: ("The Burning Crusade", 70),
        2: ("Wrath of the Lich King", 80),
        3: ("Cataclysm", 85),
        4: ("Mists of Pandaria", 90),
    }

    if expansion not in expansion_map:
        raise ValueError(f"Invalid expansion value '{expansion}'.")

    _, max_level = expansion_map[expansion]  # Only unpack max_level since expansion_name is unused

    locations_to_remove = []

    for location_data in location_table:  # Iterate through all locations
        location_name = location_data["name"]

        # Extract level from location name
        level_match = re.search(r"Level (\d+)", location_name)
        if level_match:
            level = int(level_match.group(1))
            if level > max_level:
                locations_to_remove.append(location_name)

    # Remove locations from regions
    for region in multiworld.regions:
        if region.player == player:
            region.locations = [
                location for location in region.locations
                if location.name not in locations_to_remove
            ]

    # Clear location cache if applicable
    if hasattr(multiworld, "clear_location_cache"):
        multiworld.clear_location_cache()

# This hook allows you to access the item names & counts before the items are created. Use this to increase/decrease the amount of a specific item in the pool
# Valid item_config key/values:
# {"Item Name": 5} <- This will create qty 5 items using all the default settings
# {"Item Name": {"useful": 7}} <- This will create qty 7 items and force them to be classified as useful
# {"Item Name": {"progression": 2, "useful": 1}} <- This will create 3 items, with 2 classified as progression and 1 as useful
# {"Item Name": {0b0110: 5}} <- If you know the special flag for the item classes, you can also define non-standard options. This setup
#       will create 5 items that are the "useful trap" class
# {"Item Name": {ItemClassification.useful: 5}} <- You can also use the classification directly
def before_create_items_all(item_config: dict[str, int|dict], world: World, multiworld: MultiWorld, player: int) -> dict[str, int|dict]:
    return item_config

# The item pool before starting items are processed, in case you want to see the raw item pool at that stage
def before_create_items_starting(item_pool: list, world: World, multiworld: MultiWorld, player: int) -> list:
    return item_pool

# The item pool after starting items are processed but before filler is added, in case you want to see the raw item pool at that stage
def before_create_items_filler(item_pool: list, world: World, multiworld: MultiWorld, player: int) -> list:
    # Get player options
    level_items = get_option_value(multiworld, player, "level_items")
    faction_items = get_option_value(multiworld, player, "faction")
    expansion = get_option_value(multiworld, player, "goal")
    xpitems = get_option_value(multiworld, player, "xp_rate_items")

    # Map numeric values to expansion names and max levels
    expansion_map = {
        0: ("Vanilla", 60),
        1: ("The Burning Crusade", 70),
        2: ("Wrath of the Lich King", 80),
        3: ("Cataclysm", 85),
        4: ("Mists of Pandaria", 90),
    }

    if expansion not in expansion_map:
        raise ValueError(f"Invalid expansion value '{expansion}'.")

    allowed_expansions = [name for name, _ in list(expansion_map.values())[:expansion + 1]]
    skipped_expansions = len(expansion_map) - len(allowed_expansions)

    # Initialize counters and lists
    progressive_levels_removed = 0
    xp_rate_items_kept = 0
    items_to_keep = []
    faction_item_precollected = False

    for item in item_pool:
        item_table_element = next((i for i in item_table if i["name"] == item.name), None)
        if not item_table_element:
            continue

        item_categories = item_table_element.get("category", [])

        # Handle "Class" and "Faction" items
        if "Class" in item_categories:
            continue
        if faction_items == Faction.option_alliance and "Horde" in item_categories:
            continue
        if faction_items == Faction.option_horde and "Alliance" in item_categories:
            continue
        if not faction_item_precollected:  # Precollect faction-specific item
            if (faction_items == Faction.option_alliance and item.name == "Alliance") or (
                faction_items == Faction.option_horde and item.name == "Horde"
            ):
                multiworld.push_precollected(item)
                faction_item_precollected = True
                continue

        # Combined handling for "Progressive Levels" and "Sequential Levels"
        if "Progressive Levels" in item_categories:
            if level_items == LevelItems.option_sequential:
                continue
            elif progressive_levels_removed < skipped_expansions:
                progressive_levels_removed += 1
                continue
        elif "Sequential Levels" in item_categories:
            if level_items == LevelItems.option_progressive:
                continue

        # Remove unwanted "XP Rate" items
        if "XP Rate" in item_categories:
            if xp_rate_items_kept >= xpitems:  # Remove items beyond the allowed count
                continue
            xp_rate_items_kept += 1  # Increment the count of kept items

        # Remove items not in allowed expansions (for expansion-affected categories)
        if any(category in item_categories for category in ["Sequential Levels", "Zones", "Dungeons", "Talents"]):
            if not any(expansion in item_categories for expansion in allowed_expansions):
                continue

        # Keep the item if no removal condition is met
        items_to_keep.append(item)

    # Replace the item_pool with the filtered items
    item_pool = items_to_keep

    # Add filler items if needed
    item_pool = world.adjust_filler_items(item_pool, [])

    return item_pool

    # Some other useful hook options:

    ## Place an item at a specific location
    # location = next(l for l in multiworld.get_unfilled_locations(player=player) if l.name == "Location Name")
    # item_to_place = next(i for i in item_pool if i.name == "Item Name")
    # location.place_locked_item(item_to_place)
    # item_pool.remove(item_to_place)

# The complete item pool prior to being set for generation is provided here, in case you want to make changes to it
def after_create_items(item_pool: list, world: World, multiworld: MultiWorld, player: int) -> list:
    return item_pool

# Called before rules for accessing regions and locations are created. Not clear why you'd want this, but it's here.
def before_set_rules(world: World, multiworld: MultiWorld, player: int):
    pass

# Called after rules for accessing regions and locations are created, in case you want to see or modify that information.
def after_set_rules(world: World, multiworld: MultiWorld, player: int):
    # Use this hook to modify the access rules for a given location

    def Example_Rule(state: CollectionState) -> bool:
        # Calculated rules take a CollectionState object and return a boolean
        # True if the player can access the location
        # CollectionState is defined in BaseClasses
        return True

    ## Common functions:
    # location = world.get_location(location_name, player)
    # location.access_rule = Example_Rule

    ## Combine rules:
    # old_rule = location.access_rule
    # location.access_rule = lambda state: old_rule(state) and Example_Rule(state)
    # OR
    # location.access_rule = lambda state: old_rule(state) or Example_Rule(state)

# The item name to create is provided before the item is created, in case you want to make changes to it
def before_create_item(item_name: str, world: World, multiworld: MultiWorld, player: int) -> str:
    return item_name

# The item that was created is provided after creation, in case you want to modify the item
def after_create_item(item: ManualItem, world: World, multiworld: MultiWorld, player: int) -> ManualItem:
    return item

# This method is run towards the end of pre-generation, before the place_item options have been handled and before AP generation occurs
def before_generate_basic(world: World, multiworld: MultiWorld, player: int):
    pass

# This method is run at the very end of pre-generation, once the place_item options have been handled and before AP generation occurs
def after_generate_basic(world: World, multiworld: MultiWorld, player: int):
    pass

# This method is run every time an item is added to the state, can be used to modify the value of an item.
# IMPORTANT! Any changes made in this hook must be cancelled/undone in after_remove_item
def after_collect_item(world: World, state: CollectionState, Changed: bool, item: Item):
    # the following let you add to the Potato Item Value count
    # if item.name == "Cooked Potato":
    #     state.prog_items[item.player][format_state_prog_items_key(ProgItemsCat.VALUE, "Potato")] += 1
    pass

# This method is run every time an item is removed from the state, can be used to modify the value of an item.
# IMPORTANT! Any changes made in this hook must be first done in after_collect_item
def after_remove_item(world: World, state: CollectionState, Changed: bool, item: Item):
    # the following let you undo the addition to the Potato Item Value count
    # if item.name == "Cooked Potato":
    #     state.prog_items[item.player][format_state_prog_items_key(ProgItemsCat.VALUE, "Potato")] -= 1
    pass


# This is called before slot data is set and provides an empty dict ({}), in case you want to modify it before Manual does
def before_fill_slot_data(slot_data: dict, world: World, multiworld: MultiWorld, player: int) -> dict:
    return slot_data

# This is called after slot data is set and provides the slot data at the time, in case you want to check and modify it after Manual is done with it
def after_fill_slot_data(slot_data: dict, world: World, multiworld: MultiWorld, player: int) -> dict:
    return slot_data

# This is called right at the end, in case you want to write stuff to the spoiler log
def before_write_spoiler(world: World, multiworld: MultiWorld, spoiler_handle) -> None:
    pass

# This is called when you want to add information to the hint text
def before_extend_hint_information(hint_data: dict[int, dict[int, str]], world: World, multiworld: MultiWorld, player: int) -> None:

    ### Example way to use this hook:
    # if player not in hint_data:
    #     hint_data.update({player: {}})
    # for location in multiworld.get_locations(player):
    #     if not location.address:
    #         continue
    #
    #     use this section to calculate the hint string
    #
    #     hint_data[player][location.address] = hint_string

    pass

def after_extend_hint_information(hint_data: dict[int, dict[int, str]], world: World, multiworld: MultiWorld, player: int) -> None:
    pass
