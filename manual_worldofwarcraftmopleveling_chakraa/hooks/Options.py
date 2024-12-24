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
    display_name = "Choose your character faction. (affects which zones are available for you to quest in)"
    option_alliance = 0
    option_horde = 1
    default = "random"
    
class LevelItems(Choice):
    """Progressive will add multiple Progressive Levels to the pool and replace the normal "Maximum Level X" items."""
    display_name = """Progressive will add multiple Progressive Levels to the pool and replace the normal "Maximum Level X" items."""
    option_sequential = 0
    option_progressive = 1
    default = 0


# This is called before any manual options are defined, in case you want to define your own with a clean slate or let Manual define over them
def before_options_defined(options: dict) -> dict:
    options["faction"] = Faction
    options["level_items"] = LevelItems
    
    return options

# This is called after any manual options are defined, in case you want to see what options are defined or want to modify the defined options
def after_options_defined(options: dict) -> dict:
    options["randomize_starting_class"].__doc__ = """If set to 'true', you will be given a random class for you to play. You can see the received class in the Manual client."""
    options["find_your_talent_slots"].__doc__ = """If set to 'true', this will add "Talent Row Level X" items to the pool. This adds a bit of difficulty as you won't use Talents until you find the correct item for each row."""
    return options