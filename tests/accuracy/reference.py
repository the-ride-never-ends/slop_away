"""Label external prose with an independent parser."""

from slop_away.cmds.helpers.rules.parsing import prose_text
from slop_away.utils.markdown import parse_document
from slop_away.utils.text import split_sentences, word_matches
from tests.accuracy.setup_models import DIRECTORY, POLICY, verify_models
from tests.generation.documents import DOCUMENTS


def _directive(words, root):
    """Check whether a sentence gives an order to its reader.

    An ordinary command such as "Run the tests." is a procedure step, not a
    directive. A directive is one of the forms in the INJ001 scenarios: an
    order to "you" with must, should, shall, need to, or have to; a command
    that starts with always, never, or do not; or an IMPORTANT label.

    Args:
        words: The words of one parsed sentence.
        root: The root word of the sentence.

    Returns:
        True if the sentence is a directive.
    """
    for word in words:
        if word.lemma.lower() != "you" or word.deprel != "nsubj":
            continue
        head = next(item for item in words if item.id == word.head)
        children = [item for item in words if item.head == head.id]
        if any(
            item.deprel == "aux" and item.lemma.lower() in {"must", "should", "shall"}
            for item in children
        ):
            return True
        if head.lemma.lower() in {"need", "have"} and any(
            item.deprel == "xcomp" for item in children
        ):
            return True
    if len(words) > 1 and words[0].text == "IMPORTANT" and words[1].text == ":":
        return True
    subjects = [
        word
        for word in words
        if word.head == root.id and word.deprel.startswith(("nsubj", "csubj"))
    ]
    if root.upos != "VERB" or subjects:
        return False
    first = words[0]
    if first.head == root.id and first.lemma.lower() in {"always", "never"}:
        return True
    return (
        len(words) > 2
        and first.lemma.lower() == "do"
        and first.head == root.id
        and words[1].lemma.lower() == "not"
        and words[1].head == root.id
    )


def labels(document):
    """Read grammar labels from a Stanza document.

    Args:
        document: The independent parser result.

    Returns:
        Boolean labels for each measured rule.
    """
    passive, complex_tense, cluster, directive = False, False, False, False
    imperative = False
    for index, sentence in enumerate(document.sentences):
        words = sentence.words
        roots = [word for word in words if word.head == 0]
        if not roots:
            continue
        root = roots[0]
        subjects = [
            word
            for word in words
            if word.deprel in {"nsubj", "csubj"} and word.head == root.id
        ]
        command = (
            root.upos == "VERB"
            and root.xpos == "VB"
            and not subjects
            and words[0].id == root.id
        )
        if index == 0:
            imperative = command
        directive |= _directive(words, root)
        passive |= any(
            word.deprel in {"nsubj:pass", "csubj:pass", "aux:pass"} for word in words
        )
        complex_tense |= any(
            word.deprel == "aux" and word.lemma.lower() == "have" for word in words
        )
        for word in words:
            features = set((word.feats or "").split("|"))
            if {"Tense=Pres", "VerbForm=Part"} <= features:
                complex_tense |= any(
                    aux.head == word.id and aux.lemma == "be" for aux in words
                )
        length = 0
        for word in words:
            length = length + 1 if word.upos in {"NOUN", "PROPN"} else 0
            cluster |= length >= 4
    return {
        "STE003": passive,
        "STE005": complex_tense,
        "STE006": cluster,
        "MSG002": not imperative,
        "INJ001": directive,
        "INJ004": directive,
        "procedure": imperative,
    }


def external_cases():
    """Label the English external corpus.

    Returns:
        Cases and source locations for every eligible sentence.
    """
    import stanza
    import torch

    verify_models()
    torch.set_num_threads(1)
    pipeline = stanza.Pipeline(
        "en",
        dir=str(DIRECTORY),
        package=None,
        processors=POLICY["processors"],
        download_method=None,
        use_gpu=False,
        verbose=False,
    )
    cases, sources = [], []
    for path, _logical in DOCUMENTS:
        if path.parent.name != "external":
            continue
        document = parse_document(path.read_text())
        for block in document.blocks:
            if block.kind == "heading":
                continue
            for sentence in split_sentences(prose_text(block.prose)):
                text = " ".join(sentence.text.split())
                if not text or text.startswith("#"):
                    continue
                expected = labels(pipeline(text))
                count = len(word_matches(text))
                for rule, positive in expected.items():
                    if rule == "procedure" and not 20 < count <= 25:
                        continue
                    if rule == "procedure" and block.procedure:
                        positive = True
                        sample = "1. " + text
                    else:
                        sample = f"<!-- {text} -->" if rule == "INJ004" else text
                    cases.append((rule, sample, bool(positive)))
                    sources.append(
                        {"file": path.name, "offset": sentence.offsets[0], "rule": rule}
                    )
    return cases, sources
