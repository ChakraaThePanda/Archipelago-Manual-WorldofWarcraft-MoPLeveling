# Object classes from AP that represent different types of options that you can create
from Options import FreeText, NumericOption, Toggle, DefaultOnToggle, Choice, TextChoice, Range, NamedRange

# These helper methods allow you to determine if an option has been set, or what its value is, for any player in the multiworld
from ..Helpers import is_option_enabled, get_option_value



####################################################################
# NOTE: At the time that options are created, Manual has no concept of the multiworld or its own world.
#       Options are defined before the world is even created.
#
# Example of creating your own option:
#
#   class MakeThePlayerOP(Toggle):
#       """Should the player be overpowered? Probably not, but you can choose for this to do... something!"""
#       display_name = "Make me OP"
#
#   options["make_op"] = MakeThePlayerOP
#
#
# Then, to see if the option is set, you can call is_option_enabled or get_option_value.
#####################################################################


# To add an option, use the before_options_defined hook below and something like this:
#   options["total_characters_to_win_with"] = TotalCharactersToWinWith
#
class Faction(Choice):
    """Choose your character faction. (affects which zones are available for you to quest in)"""
    display_name = """Character faction"""
    option_alliance = 0
    option_horde = 1
    default = "random"
    
class LevelItems(Choice):
    """Progressive will add multiple Progressive Levels to the pool and replace the normal "Maximum Level X" items."""
    display_name = """Progressive or Sequential"""
    option_sequential = 0
    option_progressive = 1
    default = 0

class XPRateItems(Range):
    """Choose how many "Progressive XP Rate" items you want added in the pool. 
    The value of the "XP Rate" is defined by you while you are playing, whether it be equipping an Heirloom gear piece, getting a temporary XP Buff like a potion, Darkmoon Faire buff, etc."""
    display_name = """Number of "Progressive XP Rate" items"""
    range_start = 0
    range_end = 10
    default = 0

class EasierExpansionTransition(Choice):
    """Setting it to true will make it that the logic will always expect the first zone of each expansion be received before allowing progression"""
    display_name = """Easier Expansion Transition"""
    option_false = 0
    option_true = 1
    default = 0

# This is called before any manual options are defined, in case you want to define your own with a clean slate or let Manual define over them
def before_options_defined(options: dict) -> dict:
    options["faction"] = Faction
    options["level_items"] = LevelItems
    options["xp_rate_items"] = XPRateItems
    options["easier_expansion_transition"] = EasierExpansionTransition
    return options

# This is called after any manual options are defined, in case you want to see what options are defined or want to modify the defined options
def after_options_defined(options: dict) -> dict:
    options["goal"].__doc__ =     """This will affect the items/locations in the randomizer to match what max level you want to reach.
    vanilla = Level 60
    the_burning_crusade = Level 70
    wrath_of_the_lich_king = Level 80
    cataclysm = Level 85
    mists_of_pandaria = Level 90"""    
    options["goal"].default = 4
    options["randomize_starting_class"].__doc__ = """If set to 'true', you will be given a random class for you to play. You can see the received class in the Manual client."""
    options["include_dungeons"].__doc__ = """If set to 'true', this will add all the various leveling dungeons as Filler items. This has no effect on logic; only Maximum Level and Zone Items do."""
    options["include_talent_slots"].__doc__ = """If set to 'true', this will add "Talent Row Level X" items to the pool. This adds a bit of difficulty as you won't use Talents until you find the correct item for each row."""
    options["include_equipment_rarity"].__doc__ = """If set to 'true', this will add "Progressive Equipement" items to the pool. You start as only being able to wear Gray & White items and finding a "Progressive Equipement" will then unlock Greens, then Blues and then Purples."""
    options["hardcore_mode"].__doc__ = """If set to 'true', this will add 3 "Ankh of Reincarnation" items into the pool. On Hardcore, if you die, you have to restart your character, unless you have an unused "Ankh of Reincarnation"."""
    return options