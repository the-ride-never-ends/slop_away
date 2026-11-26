from enum import StrEnum

RULES = {
    "INJ001": {
        "msg": "Directive addressed to the reader.\n {directive}",
        "hint": "Remove the directive or move it to an instruction file.",
    },
    "INJ002": {
        "msg": "Role marker in document text.\n {role_marker}",
        "hint": "Remove the role marker or put the example in a code block.",
    },
    "INJ003": {
        "msg": "Action item has no status or date.",
        "hint": "Add a status or a date to the action item.",
    },
    "INJ004": {
        "msg": "Hidden text in the document.",
        "hint": "Remove the invisible character or correct the HTML comment.",
    },
    "STE001": {
        "msg": "Sentence has {words} words, but the limit is {limit}.",
        "hint": "Divide the sentence into shorter sentences.",
    },
    "STE002": {
        "msg": "Paragraph has {sentence_count} sentences, but the limit is 6.",
        "hint": "Divide the paragraph into shorter paragraphs.",
    },
    "STE003": {
        "msg": "Passive voice in the sentence.\n {passive_sentence}",
        "hint": "Use active voice.",
    },
    "STE004": {
        "msg": "Contraction in prose.\n {contraction}",
        "hint": "Write the words in full.",
    },
    "STE005": {
        "msg": "Verb construction is not in a simple tense.\n {verb_construction}",
        "hint": "Use the present, past, or future simple tense.",
    },
    "STE006": {
        "msg": "Noun cluster has more than three nouns.\n {noun_cluster}",
        "hint": "Divide the noun cluster or add a preposition.",
    },
    "STE007": {
        "msg": "Term {synonym} is not the preferred term.",
        "hint": "Use {preferred} instead of {synonym}.",
    },
    "VRB001": {
        "msg": "Filler phrase in prose.\n {filler_phrase}",
        "hint": "Remove the filler phrase.",
    },
    "VRB002": {
        "msg": "Hedge phrase in prose.\n {hedge_phrase}",
        "hint": "State the supported fact directly.",
    },
    "VRB003": {
        "msg": "Word count {len_words} is above the budget.\n {word_budget}",
        "hint": "Remove text until the document is within its word budget.",
    },
    "VRB004": {
        "msg": "Sentence is repeated in this document.\n {repeat_sentence}",
        "hint": "Remove the repeated sentence.",
    },
    "VRB005": {
        "msg": "Sentence is also in {other_document}.",
        "hint": "Keep one copy of the sentence and use a link.",
    },
    "RDB001": {
        "msg": "Section grade {grade:.2f} is above the limit {max_grade}.",
        "hint": "Use shorter sentences and simpler words.",
    },
    "MSG004": {
        "msg": "Body has {len_words} words, but the limit is {word_budget}.",
        "hint": "Remove words from the message body.",
    },
}


class RuleSet(StrEnum):
    INJ001 = "INJ001"
    INJ002 = "INJ002"
    INJ003 = "INJ003"
    INJ004 = "INJ004"
    STE001 = "STE001"
    STE002 = "STE002"
    STE003 = "STE003"
    STE004 = "STE004"
    STE005 = "STE005"
    STE006 = "STE006"
    STE007 = "STE007"
    VRB001 = "VRB001"
    VRB002 = "VRB002"
    VRB003 = "VRB003"
    VRB004 = "VRB004"
    VRB005 = "VRB005"
    RDB001 = "RDB001"
    MSG004 = "MSG004"


for rule in RULES:
    if rule not in RuleSet.__members__:
        raise ValueError(f"Rule in RULES not in RuleSet Enum: {rule}")
for value in RuleSet.__members__.values():
    if value not in RULES:
        raise ValueError(f"Rule in RuleSet Enum not found in RULES: {value}")
