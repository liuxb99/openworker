"""OPE-51 — ask_user upgrades: rich options ({label, description, recommended, preview}),
grouped questions (one call, a stepper, one round-trip), and the {answer}/{answers} result
shapes. Back-compat is load-bearing: plain-string options and old persisted items must be
untouched by all of it."""

import asyncio
import json

from coworker.inbox import InboxItem, InboxStore
from coworker.interactions import buttons_for, decode
from coworker.server.manager import SessionManager
from coworker.tools.ask import (
    MAX_GROUPED_QUESTIONS,
    answer_result,
    ask_user_tool,
    normalize_option,
    normalize_questions,
    option_label,
    question_item_fields,
)

from tests.test_durable_resume import ScriptedProvider, _run_until_pending, _text, _tool


# -- schema -------------------------------------------------------------------


def test_schema_advertises_rich_options_and_grouped_questions():
    fn = ask_user_tool().__coworker_schema__["function"]
    assert fn["name"] == "ask_user"
    props = fn["parameters"]["properties"]
    variants = props["options"]["items"]["anyOf"]
    assert {"type": "string"} in variants
    obj = next(v for v in variants if v.get("type") == "object")
    assert obj["required"] == ["label"]
    assert set(obj["properties"]) == {"label", "description", "recommended", "preview"}
    grouped = props["questions"]
    assert grouped["maxItems"] == MAX_GROUPED_QUESTIONS
    assert grouped["items"]["required"] == ["question"]


def test_normalize_option_and_label():
    assert normalize_option("Bar") == {
        "label": "Bar",
        "description": "",
        "recommended": False,
        "preview": "",
    }
    rich = normalize_option({"label": "Line", "recommended": True, "preview": "p"})
    assert rich["recommended"] is True and rich["preview"] == "p"
    assert option_label("Bar") == "Bar" and option_label({"label": "Line"}) == "Line"


def test_normalize_questions_caps_and_drops_blanks():
    entries = [{"question": f"Q{i}?"} for i in range(MAX_GROUPED_QUESTIONS + 2)]
    got = normalize_questions(entries)
    assert len(got) == MAX_GROUPED_QUESTIONS
    assert got[0]["question"] == "Q0?"


def test_question_item_fields_preserves_rich_options():
    question = {
        "question": "Choose",
        "options": [{"label": "A", "description": "desc", "recommended": True}],
        "allow_free_text": False,
    }
    fields = question_item_fields(question)
    assert fields["options"][0]["label"] == "A"
    assert fields["options"][0]["recommended"] is True
    assert fields["allow_free_text"] is False


def test_answer_result_supports_single_and_grouped_shapes():
    assert answer_result(["A"]) == {"answer": "A"}
    assert answer_result(["A", "B"]) == {"answers": ["A", "B"]}


# -- buttons/decode back-compat ----------------------------------------------


def test_buttons_for_rich_options_uses_labels():
    item = InboxItem(
        id="x",
        kind="ask_user",
        prompt="Pick",
        options=[{"label": "Fast", "description": "short"}, "Safe"],
    )
    buttons = buttons_for(item)
    labels = [button["text"] for row in buttons for button in row]
    assert "Fast" in labels and "Safe" in labels


def test_decode_accepts_rich_option_label():
    item = InboxItem(
        id="x",
        kind="ask_user",
        prompt="Pick",
        options=[{"label": "Fast", "description": "short"}],
    )
    payload = buttons_for(item)[0][0]["callback_data"]
    decoded = decode(payload)
    assert decoded["answer"] == "Fast"


# -- persistence --------------------------------------------------------------


def test_inbox_roundtrip_preserves_rich_options(tmp_path):
    store = InboxStore(tmp_path / "inbox.json")
    item = InboxItem(
        id="rich",
        kind="ask_user",
        prompt="Pick",
        options=[{"label": "Fast", "description": "short", "recommended": True}],
    )
    store.add(item)
    loaded = InboxStore(tmp_path / "inbox.json").get("rich")
    assert loaded is not None
    assert loaded.options[0]["label"] == "Fast"
    assert loaded.options[0]["recommended"] is True


# -- durable session integration --------------------------------------------


def test_grouped_ask_user_resumes_with_answers(tmp_path):
    async def run():
        provider = ScriptedProvider(
            [
                _tool(
                    "ask_user",
                    {
                        "questions": [
                            {"question": "Q1?", "options": ["A", "B"]},
                            {"question": "Q2?", "options": [{"label": "C", "recommended": True}]},
                        ]
                    },
                ),
                _text("done"),
            ]
        )
        manager = SessionManager(tmp_path, provider=provider)
        session = await manager.create_session("test")
        pending = await _run_until_pending(manager, session.id, "go")
        assert pending.kind == "ask_user"
        assert len(pending.questions) == 2
        await manager.answer_inbox_item(pending.id, answers=["A", "C"])
        resumed = await manager.resume_session(session.id)
        assert resumed is not None
        calls = [m for m in provider.messages if m.get("role") == "tool"]
        assert calls
        payload = json.loads(calls[-1]["content"])
        assert payload == {"answers": ["A", "C"]}

    asyncio.run(run())
