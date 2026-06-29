from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

from copycat.store import CopycatStore, MetadataPage


@pytest.fixture()
def store(tmp_path: Path) -> CopycatStore:
    return CopycatStore(tmp_path)


def test_creates_canonical_alias_layout_with_skeleton_metadata(store: CopycatStore, tmp_path: Path) -> None:
    result = store.create(alias="linear", source_url="https://linear.app/")

    assert result["alias"] == "linear"
    assert result["paths"]["design"] == str(tmp_path / "linear" / "DESIGN.md")
    assert result["paths"]["tokens"] == str(tmp_path / "linear" / "tokens.json")
    assert result["paths"]["notes"] == str(tmp_path / "linear" / "notes.md")
    assert result["paths"]["screenshotsDir"] == str(tmp_path / "linear" / "screenshots")
    assert result["suggestedScreenshotPaths"]["desktopFold"] == "screenshots/desktop-fold.png"
    assert result["suggestedPageScreenshotPaths"] == {
        "desktopFullPattern": "screenshots/{page}-desktop-full.png",
        "mobileFullPattern": "screenshots/{page}-mobile-full.png",
    }
    assert (tmp_path / "linear" / "screenshots").is_dir()
    assert (tmp_path / "linear" / "evidence" / "pages").is_dir()

    metadata = json.loads((tmp_path / "linear" / "metadata.json").read_text())
    assert metadata["schemaVersion"] == 1
    assert metadata["alias"] == "linear"
    assert metadata["sourceUrl"] == "https://linear.app/"
    assert metadata["status"] == "initialized"
    assert metadata["files"] == {
        "design": "DESIGN.md",
        "tokens": "tokens.json",
        "notes": "notes.md",
        "screenshots": [],
        "evidence": [],
    }


def test_refuses_invalid_aliases_and_path_traversal(store: CopycatStore) -> None:
    for alias in ["../linear", "Linear", "linear_app"]:
        with pytest.raises(ValueError, match="Invalid alias"):
            store.create(alias=alias, source_url="https://linear.app/")


def test_refuses_existing_aliases_unless_overwrite_mode_is_explicit(store: CopycatStore) -> None:
    store.create(alias="linear", source_url="https://linear.app/")

    with pytest.raises(FileExistsError, match="already exists"):
        store.create(alias="linear", source_url="https://linear.app/")

    overwritten = store.create(alias="linear", source_url="https://linear.app/", mode="overwrite")
    assert overwritten["metadata"]["status"] == "initialized"


def test_overwrite_preserves_existing_alias_when_replacement_setup_fails(
    store: CopycatStore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store.create(alias="linear", source_url="https://linear.app/")
    store.save(alias="linear", design="# Existing\n", tokens={"colors": {}})
    real_metadata_text = store._metadata_text

    def fail_new_metadata(value: Any) -> str:
        if isinstance(value, dict) and value.get("sourceUrl") == "https://new.example/":
            raise TypeError("metadata serialization failed")
        return real_metadata_text(value)

    monkeypatch.setattr(store, "_metadata_text", fail_new_metadata)

    with pytest.raises(TypeError, match="metadata serialization failed"):
        store.create(alias="linear", source_url="https://new.example/", mode="overwrite")

    profile = store.get("linear")
    assert profile["metadata"]["sourceUrl"] == "https://linear.app/"
    assert profile["design"] == "# Existing\n"


def test_save_writes_profile_metadata_evidence_and_returns_validation(store: CopycatStore, tmp_path: Path) -> None:
    store.create(alias="linear", source_url="https://linear.app/")
    (tmp_path / "linear" / "screenshots" / "desktop-fold.png").write_text("png-bytes")
    page_dir = tmp_path / "linear" / "evidence" / "pages" / "pricing"
    page_dir.mkdir(parents=True)
    (page_dir / "computed-styles.json").write_text("{}")

    result = store.save(
        alias="linear",
        design="# Linear\n\nUse the visual system, not the identity.\n",
        tokens={"colors": {"background": "#08090a"}},
        notes="# Notes\n",
        screenshots=["screenshots/desktop-fold.png"],
        evidence=["evidence/pages/pricing/computed-styles.json"],
        pages=[
            {
                "type": "supporting",
                "name": "pricing",
                "url": "https://linear.app/pricing",
                "reason": "Pricing tables and plan cards.",
            }
        ],
        metadata_patch={"status": "profiled", "confidence": "high", "caveats": ["Public pages only."]},
    )

    assert result["validation"] == {"alias": "linear", "valid": True, "issues": []}
    profile = store.get("linear")
    assert "Use the visual system" in profile["design"]
    assert profile["tokens"] == {"colors": {"background": "#08090a"}}
    assert profile["notes"] == "# Notes\n"
    assert profile["metadata"]["status"] == "profiled"
    assert profile["metadata"]["confidence"] == "high"
    assert profile["metadata"]["caveats"] == ["Public pages only."]
    assert profile["metadata"]["files"]["screenshots"] == ["screenshots/desktop-fold.png"]
    assert profile["metadata"]["files"]["evidence"] == ["evidence/pages/pricing/computed-styles.json"]
    assert len(profile["metadata"]["pages"]) == 1
    assert profile["validation"]["valid"] is True


def test_save_rejects_evidence_outside_or_missing_alias_directory(store: CopycatStore) -> None:
    store.create(alias="linear", source_url="https://linear.app/")

    with pytest.raises(ValueError, match="inside alias"):
        store.save(alias="linear", evidence=["../outside.json"])

    with pytest.raises(FileNotFoundError, match="does not exist"):
        store.save(alias="linear", evidence=["evidence/missing.json"])


def test_save_rejects_artifacts_in_wrong_directories(store: CopycatStore, tmp_path: Path) -> None:
    store.create(alias="linear", source_url="https://linear.app/")
    (tmp_path / "linear" / "screenshots" / "desktop-fold.png").write_text("png-bytes")
    (tmp_path / "linear" / "evidence" / "desktop-snapshot.json").write_text("{}")

    with pytest.raises(ValueError, match="screenshots/"):
        store.save(alias="linear", screenshots=["evidence/desktop-snapshot.json"])

    with pytest.raises(ValueError, match="evidence/"):
        store.save(alias="linear", evidence=["screenshots/desktop-fold.png"])


def test_save_rejects_invalid_pages_before_writing_profile_files(store: CopycatStore, tmp_path: Path) -> None:
    store.create(alias="linear", source_url="https://linear.app/")

    with pytest.raises(ValueError, match="pages"):
        store.save(
            alias="linear",
            design="# Should not write\n",
            pages=cast(Any, [{"type": "bad", "url": 123}]),
        )

    assert not (tmp_path / "linear" / "DESIGN.md").exists()


def test_save_deduplicates_pages(store: CopycatStore) -> None:
    store.create(alias="linear", source_url="https://linear.app/")
    page: MetadataPage = {
        "type": "supporting",
        "name": "pricing",
        "url": "https://linear.app/pricing",
        "reason": "Pricing tables and plan cards.",
    }

    store.save(alias="linear", pages=[page])
    store.save(alias="linear", pages=[page])

    assert store.get("linear")["metadata"]["pages"] == [page]


def test_save_rejects_unserializable_tokens_before_writing_profile_files(store: CopycatStore) -> None:
    store.create(alias="linear", source_url="https://linear.app/")
    store.save(alias="linear", design="# Existing\n", tokens={"colors": {}})

    with pytest.raises(TypeError):
        store.save(alias="linear", design="# New\n", tokens={"bad": object()})

    profile = store.get("linear")
    assert profile["design"] == "# Existing\n"
    assert profile["tokens"] == {"colors": {}}


def test_get_returns_validation_summary_for_complete_and_incomplete_aliases(store: CopycatStore) -> None:
    store.create(alias="linear", source_url="https://linear.app/")

    incomplete = store.get("linear")["validation"]
    assert incomplete["valid"] is False
    assert {issue["code"] for issue in incomplete["issues"]} >= {"missing_design", "missing_tokens"}

    store.save(
        alias="linear",
        design="# Linear\n",
        tokens={"colors": {}},
        notes="# Notes\n",
        metadata_patch={"status": "profiled"},
    )

    complete = store.get("linear")["validation"]
    assert complete == {"alias": "linear", "valid": True, "issues": []}


def test_get_returns_validation_summary_when_tokens_json_is_invalid(store: CopycatStore, tmp_path: Path) -> None:
    store.create(alias="linear", source_url="https://linear.app/")
    (tmp_path / "linear" / "DESIGN.md").write_text("# Linear\n")
    (tmp_path / "linear" / "tokens.json").write_text("not-json")

    profile = store.get("linear")

    assert profile["validation"]["valid"] is False
    assert {issue["code"] for issue in profile["validation"]["issues"]} == {"invalid_tokens"}
    assert "tokens" not in profile


def test_validate_reports_malformed_metadata_without_crashing(store: CopycatStore, tmp_path: Path) -> None:
    store.create(alias="linear", source_url="https://linear.app/")
    (tmp_path / "linear" / "metadata.json").write_text(json.dumps({"schemaVersion": 1}))

    validation = store.validate("linear")

    assert validation["valid"] is False
    assert {issue["code"] for issue in validation["issues"]} >= {"invalid_metadata"}


def test_save_rejects_invalid_metadata_patch_fields(store: CopycatStore) -> None:
    store.create(alias="linear", source_url="https://linear.app/")

    with pytest.raises(ValueError, match="metadata_patch.status"):
        store.save(alias="linear", metadata_patch={"status": "bogus"})

    with pytest.raises(ValueError, match="metadata_patch.pages"):
        store.save(alias="linear", metadata_patch={"pages": "not-a-list"})

    with pytest.raises(ValueError, match="metadata_patch.unknown"):
        store.save(alias="linear", metadata_patch={"unknown": True})


def test_save_rejects_invalid_metadata_patch_before_writing_profile_files(store: CopycatStore, tmp_path: Path) -> None:
    store.create(alias="linear", source_url="https://linear.app/")

    with pytest.raises(ValueError, match="metadata_patch.status"):
        store.save(alias="linear", design="# Should not write\n", metadata_patch={"status": "bogus"})

    assert not (tmp_path / "linear" / "DESIGN.md").exists()


def test_renames_alias_and_updates_metadata_without_overwriting_target(store: CopycatStore) -> None:
    store.create(alias="linear", source_url="https://linear.app/")
    store.create(alias="renamed-linear", source_url="https://example.com/")

    with pytest.raises(FileExistsError, match="already exists"):
        store.rename(old_alias="linear", new_alias="renamed-linear")

    store.delete("renamed-linear")
    result = store.rename(old_alias="linear", new_alias="renamed-linear")
    assert result["alias"] == "renamed-linear"

    with pytest.raises(FileNotFoundError, match="does not exist"):
        store.get("linear")
    assert store.get("renamed-linear")["metadata"]["alias"] == "renamed-linear"


def test_deletes_captured_alias_immediately(store: CopycatStore) -> None:
    store.create(alias="linear", source_url="https://linear.app/")
    assert store.delete("linear") == {"alias": "linear", "deleted": True}

    with pytest.raises(FileNotFoundError, match="does not exist"):
        store.get("linear")
