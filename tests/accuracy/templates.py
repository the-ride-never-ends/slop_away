"""Build sentences with known grammar labels."""

from itertools import product

RULES = ("STE003", "STE005", "STE006", "MSG002", "INJ001", "INJ004", "procedure")


def templates():
    """Build positive and negative cases for each parser rule.

    Returns:
        Rule, text, and expected finding records.
    """
    cases = []
    actors = ("worker", "reader", "author", "operator")
    objects = ("file", "page", "report", "note")
    for actor, noun in product(actors, objects):
        pairs = {
            "STE003": (
                f"The {noun} is read by the {actor}.",
                f"The {actor} reads the {noun}.",
            ),
            "STE005": (
                f"The {actor} has read the {noun}.",
                f"The {actor} read the {noun}.",
            ),
            "MSG002": (f"The {actor} reads the {noun}", f"Read the {noun}"),
            "INJ001": (f"You must read the {noun}.", f"The {actor} reads the {noun}."),
            "INJ004": (
                f"<!-- You must read the {noun}. -->",
                f"<!-- The {actor} reads the {noun}. -->",
            ),
            "procedure": (
                f"Read the {noun} " + "now " * 18 + ".",
                f"The {noun} is " + "red " * 18 + ".",
            ),
        }
        for rule, (positive, negative) in pairs.items():
            cases.extend([(rule, positive, True), (rule, negative, False)])
    for nouns in product(
        ("data", "file"), ("cache", "server"), ("path", "name"), ("list", "map")
    ):
        positive = "The " + " ".join(nouns) + " changes."
        negative = f"The {nouns[0]} {nouns[1]} for the {nouns[2]} {nouns[3]} changes."
        cases.extend([("STE006", positive, True), ("STE006", negative, False)])
    return tuple(cases)
