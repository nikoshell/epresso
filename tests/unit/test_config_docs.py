"""``docs/guides/build/configuration.md`` must name every option the models declare.

The reference is hand-written and had drifted: 13 of the 46 options the models
declare were absent from it. This ties the two together so a new option cannot
land undocumented.

Scope: the option name must appear inside a fenced ``toml`` block, not merely
anywhere in the prose, so a passing mention in a sentence does not satisfy it.
It still proves a name is *present*, not that it is *explained* -- the value is
in catching an option that appears nowhere at all. ``markdown.toc_heading`` is
documented as "declared but not implemented" because this test would otherwise
demand a description of a no-op.
"""

from __future__ import annotations

import re
import typing
from pathlib import Path

from pydantic import BaseModel

from epresso.config import Config

DOC = Path(__file__).resolve().parents[2] / "docs" / "guides" / "build" / "configuration.md"
_TOML_BLOCK = re.compile(r"```toml\n(.*?)```", re.DOTALL)


def _section_models() -> dict[str, type[BaseModel]]:
    """Config sections that are their own model — the ones the reference documents.

    Handles both ``x: Model`` and ``x: Model | None`` / ``list[Model]``, and
    recurses because a bare annotation carries no ``__args__`` at all.
    """

    def resolve(ann: object) -> type[BaseModel] | None:
        if isinstance(ann, type) and issubclass(ann, BaseModel):
            return ann
        for arg in typing.get_args(ann):
            found = resolve(arg)
            if found is not None:
                return found
        return None

    models: dict[str, type[BaseModel]] = {}
    for name, field in Config.model_fields.items():
        model = resolve(field.annotation)
        if model is not None:
            models[name] = model
    return models


def test_config_reference_names_every_option() -> None:
    documented = "\n".join(_TOML_BLOCK.findall(DOC.read_text(encoding="utf-8")))
    assert documented, f"no ```toml blocks found in {DOC}"
    missing = [
        f"{section}.{option}"
        for section, model in _section_models().items()
        for option in model.model_fields
        if not re.search(rf"\b{re.escape(option)}\b", documented)
    ]
    assert not missing, (
        f"{DOC.name} does not show {len(missing)} config option(s) in a toml block: "
        f"{', '.join(missing)}. Document them, or remove the option from the model."
    )
