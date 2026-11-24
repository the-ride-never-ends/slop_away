"""Label external prose with an independent parser."""

from slop_away.markdown import parse_document
from slop_away.parsing import prose_text
from slop_away.text import split_sentences, word_matches
from tests.accuracy.setup_models import DIRECTORY, POLICY, verify_models
from tests.generation.documents import DOCUMENTS


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
        directive |= command or any(
            word.lemma.lower() == "you"
            and word.deprel == "nsubj"
            and any(
                aux.head == word.head
                and aux.lemma.lower() in {"must", "should", "shall", "need", "have"}
                for aux in words
            )
            for word in words
        )
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
