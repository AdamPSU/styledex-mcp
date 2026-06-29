from __future__ import annotations

import json
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, List, Literal, NotRequired, TypedDict, cast
from uuid import uuid4

AliasStatus = Literal["initialized", "captured", "profiled", "invalid"]
Confidence = Literal["low", "medium", "high"]
PageType = Literal["seed", "supporting", "enrichment"]

ALIAS_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
ALIAS_STATUSES = {"initialized", "captured", "profiled", "invalid"}
CONFIDENCE_VALUES = {"low", "medium", "high"}
PATCHABLE_METADATA_FIELDS = {"status", "confidence", "caveats", "observedNoise"}
SCREENSHOT_PREFIX = "screenshots/"
EVIDENCE_PREFIX = "evidence/"
TYPEUI_DESIGN_HEADINGS = (
    "## Mission",
    "## Brand",
    "## Style Foundations",
    "## Accessibility",
    "## Writing Tone",
    "## Rules: Do",
    "## Rules: Don't",
    "## Guideline Authoring Workflow",
    "## Required Output Structure",
    "## Component Rule Expectations",
    "## Quality Gates",
)


class MetadataPage(TypedDict):
    type: PageType
    url: str
    name: NotRequired[str]
    reason: NotRequired[str]


class MetadataFiles(TypedDict):
    design: str
    tokens: str
    notes: str
    screenshots: list[str]
    evidence: list[str]


class CopycatMetadata(TypedDict):
    schemaVersion: Literal[1]
    alias: str
    sourceUrl: str
    createdAt: str
    lastUpdated: str
    status: AliasStatus
    confidence: NotRequired[Confidence]
    pages: list[MetadataPage]
    files: MetadataFiles
    caveats: list[str]
    observedNoise: list[str]


class AliasPaths(TypedDict):
    root: str
    design: str
    tokens: str
    metadata: str
    notes: str
    screenshotsDir: str
    evidenceDir: str
    pagesEvidenceDir: str


class StoreProfile(TypedDict):
    alias: str
    paths: AliasPaths
    validation: ValidationResult
    metadata: NotRequired[CopycatMetadata]
    design: NotRequired[str]
    tokens: NotRequired[Any]
    notes: NotRequired[str]


class ValidationIssue(TypedDict):
    code: str
    message: str
    path: NotRequired[str]


class ValidationResult(TypedDict):
    alias: str
    valid: bool
    issues: list[ValidationIssue]


class CopycatStore:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).expanduser().resolve()

    def list(self) -> dict[str, List[dict[str, Any]]]:
        self.root.mkdir(parents=True, exist_ok=True)
        aliases: List[dict[str, Any]] = []
        for child in sorted(self.root.iterdir()):
            if not child.is_dir() or not ALIAS_PATTERN.fullmatch(child.name):
                continue
            entry: dict[str, Any] = {"alias": child.name, "path": str(child)}
            try:
                entry["metadata"] = self._read_metadata(child.name)
            except Exception:
                pass
            aliases.append(entry)
        return {"aliases": aliases}

    def create(
        self,
        *,
        alias: str,
        source_url: str,
        mode: Literal["create", "overwrite"] = "create",
    ) -> dict[str, Any]:
        alias = self._assert_alias(alias)
        alias_dir = self._alias_dir(alias)
        if alias_dir.exists():
            if mode != "overwrite":
                raise FileExistsError(f'Alias "{alias}" already exists')

        paths = self.paths(alias)
        now = _now_iso()
        metadata: CopycatMetadata = {
            "schemaVersion": 1,
            "alias": alias,
            "sourceUrl": source_url,
            "createdAt": now,
            "lastUpdated": now,
            "status": "initialized",
            "pages": [],
            "files": {
                "design": "DESIGN.md",
                "tokens": "tokens.json",
                "notes": "notes.md",
                "screenshots": [],
                "evidence": [],
            },
            "caveats": [],
            "observedNoise": [],
        }
        if alias_dir.exists():
            self._replace_alias_dir(alias, metadata)
        else:
            self._initialize_alias_dir(alias_dir, metadata)

        return {
            "alias": alias,
            "paths": paths,
            "metadata": metadata,
            "suggestedScreenshotPaths": {
                "desktopFold": "screenshots/desktop-fold.png",
                "desktopFull": "screenshots/desktop-full.png",
                "mobileFold": "screenshots/mobile-fold.png",
                "mobileFull": "screenshots/mobile-full.png",
            },
            "suggestedPageScreenshotPaths": {
                "desktopFullPattern": "screenshots/{page}-desktop-full.png",
                "mobileFullPattern": "screenshots/{page}-mobile-full.png",
            },
        }

    def get(self, alias: str) -> StoreProfile:
        alias = self._assert_alias(alias)
        self._assert_alias_exists(alias)
        paths = self.paths(alias)
        profile: StoreProfile = {
            "alias": alias,
            "paths": paths,
            "validation": self.validate(alias),
        }
        try:
            profile["metadata"] = self._read_metadata(alias)
        except Exception:
            pass
        design = self._read_optional_text(Path(paths["design"]))
        notes = self._read_optional_text(Path(paths["notes"]))
        tokens = self._read_optional_text(Path(paths["tokens"]))
        if design is not None:
            profile["design"] = design
        if notes is not None:
            profile["notes"] = notes
        if tokens is not None:
            try:
                profile["tokens"] = json.loads(tokens)
            except json.JSONDecodeError:
                pass
        return profile

    def save(
        self,
        *,
        alias: str,
        design: str | None = None,
        tokens: Any | None = None,
        notes: str | None = None,
        screenshots: List[str] | None = None,
        evidence: List[str] | None = None,
        pages: List[MetadataPage] | None = None,
        metadata_patch: dict[str, Any] | None = None,
    ) -> StoreProfile:
        alias = self._assert_alias(alias)
        self._assert_alias_exists(alias)
        paths = self.paths(alias)
        self._assert_metadata_patch(metadata_patch or {})

        screenshot_paths = self._validate_relative_files(
            alias,
            screenshots or [],
            expected_prefix=SCREENSHOT_PREFIX,
            label="Screenshot path",
        )
        evidence_paths = self._validate_relative_files(
            alias,
            evidence or [],
            expected_prefix=EVIDENCE_PREFIX,
            label="Evidence path",
        )
        page_entries = self._validate_pages(pages or [])
        tokens_text = f"{json.dumps(tokens, indent=2)}\n" if tokens is not None else None

        metadata = self._read_metadata(alias)
        metadata["files"]["screenshots"] = _unique([*metadata["files"]["screenshots"], *screenshot_paths])
        metadata["files"]["evidence"] = _unique([*metadata["files"]["evidence"], *evidence_paths])
        metadata["pages"] = _unique_pages([*metadata["pages"], *page_entries])
        metadata = self._merge_metadata(metadata, metadata_patch or {})

        writes: dict[Path, str] = {Path(paths["metadata"]): self._metadata_text(metadata)}
        if design is not None:
            writes[Path(paths["design"])] = _format_design_document(alias=alias, design=design, metadata=metadata)
        if tokens_text is not None:
            writes[Path(paths["tokens"])] = tokens_text
        if notes is not None:
            writes[Path(paths["notes"])] = notes
        self._write_files_atomically(writes)
        return self.get(alias)

    def validate(self, alias: str) -> ValidationResult:
        alias = self._assert_alias(alias)
        paths = self.paths(alias)
        issues: List[ValidationIssue] = []

        if not Path(paths["root"]).exists():
            return {
                "alias": alias,
                "valid": False,
                "issues": [{"code": "missing_alias", "message": f'Alias "{alias}" does not exist', "path": paths["root"]}],
            }

        metadata: CopycatMetadata | None = None
        try:
            metadata = self._read_metadata(alias)
            issues.extend(self._metadata_shape_issues(metadata, paths["metadata"]))
        except Exception as exc:
            issues.append({"code": "invalid_metadata", "message": str(exc), "path": paths["metadata"]})

        if not Path(paths["design"]).exists():
            issues.append({"code": "missing_design", "message": "DESIGN.md is missing", "path": paths["design"]})
        if not Path(paths["tokens"]).exists():
            issues.append({"code": "missing_tokens", "message": "tokens.json is missing", "path": paths["tokens"]})
        else:
            try:
                json.loads(Path(paths["tokens"]).read_text(encoding="utf-8"))
            except Exception as exc:
                issues.append({"code": "invalid_tokens", "message": str(exc), "path": paths["tokens"]})

        if metadata is not None and not any(issue["code"] == "invalid_metadata" for issue in issues):
            if metadata["alias"] != alias:
                issues.append({"code": "alias_mismatch", "message": f'metadata alias is "{metadata["alias"]}"', "path": paths["metadata"]})
            for file_path in metadata["files"]["screenshots"]:
                try:
                    self._validate_relative_files(
                        alias,
                        [file_path],
                        expected_prefix=SCREENSHOT_PREFIX,
                        label="Screenshot path",
                    )
                except Exception as exc:
                    issues.append({"code": "missing_referenced_file", "message": str(exc), "path": file_path})
            for file_path in metadata["files"]["evidence"]:
                try:
                    self._validate_relative_files(
                        alias,
                        [file_path],
                        expected_prefix=EVIDENCE_PREFIX,
                        label="Evidence path",
                    )
                except Exception as exc:
                    issues.append({"code": "missing_referenced_file", "message": str(exc), "path": file_path})

        return {"alias": alias, "valid": not issues, "issues": issues}

    def rename(self, *, old_alias: str, new_alias: str) -> StoreProfile:
        old_alias = self._assert_alias(old_alias)
        new_alias = self._assert_alias(new_alias)
        self._assert_alias_exists(old_alias)
        old_dir = self._alias_dir(old_alias)
        new_dir = self._alias_dir(new_alias)
        if new_dir.exists():
            raise FileExistsError(f'Alias "{new_alias}" already exists')
        self._assert_not_symlink(old_dir)
        old_dir.rename(new_dir)
        metadata = self._read_metadata(new_alias)
        metadata["alias"] = new_alias
        metadata["lastUpdated"] = _now_iso()
        self._write_metadata(new_alias, metadata)
        return self.get(new_alias)

    def delete(self, alias: str) -> dict[str, Any]:
        alias = self._assert_alias(alias)
        if not self._alias_dir(alias).exists():
            raise FileNotFoundError(f'Alias "{alias}" does not exist')
        self._remove_alias_dir(alias)
        return {"alias": alias, "deleted": True}

    def paths(self, alias: str) -> AliasPaths:
        alias = self._assert_alias(alias)
        root = self._alias_dir(alias)
        return {
            "root": str(root),
            "design": str(root / "DESIGN.md"),
            "tokens": str(root / "tokens.json"),
            "metadata": str(root / "metadata.json"),
            "notes": str(root / "notes.md"),
            "screenshotsDir": str(root / "screenshots"),
            "evidenceDir": str(root / "evidence"),
            "pagesEvidenceDir": str(root / "evidence" / "pages"),
        }

    def artifact_path(self, *, alias: str, path: str) -> tuple[Path, str]:
        alias = self._assert_alias(alias)
        self._assert_alias_exists(alias)
        relative_path = Path(path)
        if relative_path.is_absolute():
            raise ValueError(f'Artifact path "{path}" must be relative and inside alias "{alias}"')
        alias_root = self._alias_dir(alias)
        resolved = (alias_root / relative_path).resolve()
        if not _is_inside(alias_root, resolved):
            raise ValueError(f'Artifact path "{path}" must be inside alias "{alias}"')
        return resolved, resolved.relative_to(alias_root).as_posix()

    def _initialize_alias_dir(self, alias_dir: Path, metadata: CopycatMetadata) -> None:
        (alias_dir / "screenshots").mkdir(parents=True, exist_ok=True)
        (alias_dir / "evidence" / "pages").mkdir(parents=True, exist_ok=True)
        self._write_text_file_atomically(alias_dir / "metadata.json", self._metadata_text(metadata))

    def _replace_alias_dir(self, alias: str, metadata: CopycatMetadata) -> None:
        alias_dir = self._alias_dir(alias)
        self._assert_not_symlink(alias_dir)
        self.root.mkdir(parents=True, exist_ok=True)
        temp_dir = self.root / f".{alias}.tmp-{uuid4().hex}"
        backup_dir = self.root / f".{alias}.bak-{uuid4().hex}"
        try:
            self._initialize_alias_dir(temp_dir, metadata)
            alias_dir.rename(backup_dir)
            try:
                temp_dir.rename(alias_dir)
            except BaseException:
                if not alias_dir.exists() and backup_dir.exists():
                    backup_dir.rename(alias_dir)
                raise
            shutil.rmtree(backup_dir)
        finally:
            if temp_dir.exists():
                self._remove_tree(temp_dir)

    def _remove_alias_dir(self, alias: str) -> None:
        alias_dir = self._alias_dir(alias)
        self._assert_not_symlink(alias_dir)
        self._remove_tree(alias_dir)

    def _remove_tree(self, path: Path) -> None:
        self._assert_not_symlink(path)
        shutil.rmtree(path)

    def _validate_relative_files(
        self,
        alias: str,
        files: List[str],
        *,
        expected_prefix: str | None = None,
        label: str = "Evidence path",
    ) -> List[str]:
        alias_root = self._alias_dir(alias)
        validated: List[str] = []
        for file_path in files:
            path = Path(file_path)
            if path.is_absolute():
                raise ValueError(f'{label} "{file_path}" must be relative and inside alias "{alias}"')
            resolved = (alias_root / path).resolve()
            if not _is_inside(alias_root, resolved):
                raise ValueError(f'{label} "{file_path}" must be inside alias "{alias}"')
            if not resolved.exists():
                raise FileNotFoundError(f'{label} "{file_path}" does not exist')
            relative = resolved.relative_to(alias_root).as_posix()
            if expected_prefix is not None and not relative.startswith(expected_prefix):
                raise ValueError(f'{label} "{file_path}" must be under {expected_prefix}')
            validated.append(relative)
        return validated

    def _validate_pages(self, pages: List[MetadataPage]) -> List[MetadataPage]:
        if not _is_metadata_pages(pages):
            raise ValueError("pages must be a list of page objects")
        return pages

    def _merge_metadata(self, metadata: CopycatMetadata, patch: dict[str, Any]) -> CopycatMetadata:
        self._assert_metadata_patch(patch)
        next_metadata = cast(CopycatMetadata, {**metadata, **patch})
        next_metadata["schemaVersion"] = 1
        next_metadata["alias"] = metadata["alias"]
        next_metadata["createdAt"] = metadata["createdAt"]
        next_metadata["files"] = metadata["files"]
        next_metadata["lastUpdated"] = _now_iso()
        return next_metadata

    def _assert_metadata_patch(self, patch: dict[str, Any]) -> None:
        for key, value in patch.items():
            if key not in PATCHABLE_METADATA_FIELDS:
                raise ValueError(f"metadata_patch.{key} is not supported")
            if key == "status" and value not in ALIAS_STATUSES:
                raise ValueError(f"metadata_patch.status must be one of {sorted(ALIAS_STATUSES)}")
            if key == "confidence" and value not in CONFIDENCE_VALUES:
                raise ValueError(f"metadata_patch.confidence must be one of {sorted(CONFIDENCE_VALUES)}")
            if key in {"caveats", "observedNoise"} and not _is_str_list(value):
                raise ValueError(f"metadata_patch.{key} must be a list of strings")

    def _metadata_shape_issues(self, metadata: Any, path: str) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []

        def invalid(message: str) -> None:
            issues.append({"code": "invalid_metadata", "message": message, "path": path})

        if not isinstance(metadata, dict):
            invalid("metadata.json must contain an object")
            return issues

        if metadata.get("schemaVersion") != 1:
            invalid("metadata.schemaVersion must be 1")
        if not isinstance(metadata.get("alias"), str):
            invalid("metadata.alias must be a string")
        if not isinstance(metadata.get("sourceUrl"), str):
            invalid("metadata.sourceUrl must be a string")
        if not isinstance(metadata.get("createdAt"), str):
            invalid("metadata.createdAt must be a string")
        if not isinstance(metadata.get("lastUpdated"), str):
            invalid("metadata.lastUpdated must be a string")
        if metadata.get("status") not in ALIAS_STATUSES:
            invalid(f"metadata.status must be one of {sorted(ALIAS_STATUSES)}")
        if "confidence" in metadata and metadata.get("confidence") not in CONFIDENCE_VALUES:
            invalid(f"metadata.confidence must be one of {sorted(CONFIDENCE_VALUES)}")
        if not _is_metadata_pages(metadata.get("pages")):
            invalid("metadata.pages must be a list of page objects")
        if not _is_metadata_files(metadata.get("files")):
            invalid("metadata.files has an invalid shape")
        if not _is_str_list(metadata.get("caveats")):
            invalid("metadata.caveats must be a list of strings")
        if not _is_str_list(metadata.get("observedNoise")):
            invalid("metadata.observedNoise must be a list of strings")

        return issues

    def _read_metadata(self, alias: str) -> CopycatMetadata:
        metadata_path = Path(self.paths(alias)["metadata"])
        if not metadata_path.exists():
            raise FileNotFoundError(f'Alias "{alias}" does not exist or metadata.json is missing')
        return cast(CopycatMetadata, json.loads(metadata_path.read_text(encoding="utf-8")))

    def _write_metadata(self, alias: str, metadata: CopycatMetadata) -> None:
        self._write_text_file_atomically(Path(self.paths(alias)["metadata"]), self._metadata_text(metadata))

    def _metadata_text(self, metadata: CopycatMetadata) -> str:
        return f"{json.dumps(metadata, indent=2)}\n"

    def _write_files_atomically(self, writes: dict[Path, str]) -> None:
        staged: list[tuple[Path, Path]] = []
        backups: dict[Path, bytes | None] = {}
        try:
            for path, text in writes.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                temp_path = self._temp_sibling(path)
                temp_path.write_text(text, encoding="utf-8")
                staged.append((path, temp_path))
            for path, temp_path in staged:
                backups[path] = path.read_bytes() if path.exists() else None
                temp_path.replace(path)
        except BaseException:
            for path, backup in backups.items():
                if backup is None:
                    try:
                        path.unlink()
                    except FileNotFoundError:
                        pass
                else:
                    self._write_bytes_file_atomically(path, backup)
            raise
        finally:
            for _, temp_path in staged:
                try:
                    temp_path.unlink()
                except FileNotFoundError:
                    pass

    def _write_text_file_atomically(self, path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self._temp_sibling(path)
        try:
            temp_path.write_text(text, encoding="utf-8")
            temp_path.replace(path)
        finally:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass

    def _write_bytes_file_atomically(self, path: Path, payload: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self._temp_sibling(path)
        try:
            temp_path.write_bytes(payload)
            temp_path.replace(path)
        finally:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass

    def _temp_sibling(self, path: Path) -> Path:
        return path.with_name(f".{path.name}.tmp-{uuid4().hex}")

    def _read_optional_text(self, path: Path) -> str | None:
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    def _assert_alias_exists(self, alias: str) -> None:
        if not self._alias_dir(alias).exists():
            raise FileNotFoundError(f'Alias "{alias}" does not exist')

    def _assert_alias(self, alias: str) -> str:
        if not ALIAS_PATTERN.fullmatch(alias):
            raise ValueError(f'Invalid alias "{alias}". Use lowercase slug format: {ALIAS_PATTERN.pattern}')
        return alias

    def _alias_dir(self, alias: str) -> Path:
        alias_dir = (self.root / alias).resolve()
        if not _is_inside(self.root, alias_dir):
            raise ValueError(f'Alias path for "{alias}" escapes Copycat root')
        return alias_dir

    def _assert_not_symlink(self, path: Path) -> None:
        if path.is_symlink():
            raise ValueError(f"Refusing to modify symlinked alias directory: {path}")


def _now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _is_inside(root: Path, path: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _is_str_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _is_metadata_pages(value: Any) -> bool:
    if not isinstance(value, list):
        return False
    for page in value:
        if not isinstance(page, dict):
            return False
        if set(page) - {"type", "url", "name", "reason"}:
            return False
        if page.get("type") not in {"seed", "supporting", "enrichment"}:
            return False
        if not isinstance(page.get("url"), str):
            return False
        if "name" in page and not isinstance(page.get("name"), str):
            return False
        if "reason" in page and not isinstance(page.get("reason"), str):
            return False
    return True


def _is_metadata_files(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    return (
        value.get("design") == "DESIGN.md"
        and value.get("tokens") == "tokens.json"
        and value.get("notes") == "notes.md"
        and _is_str_list(value.get("screenshots"))
        and _is_str_list(value.get("evidence"))
    )


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _unique_pages(values: list[MetadataPage]) -> list[MetadataPage]:
    seen: set[tuple[str, str, str, str]] = set()
    unique: list[MetadataPage] = []
    for page in values:
        key = (page["type"], page["url"], page.get("name", ""), page.get("reason", ""))
        if key in seen:
            continue
        seen.add(key)
        unique.append(page)
    return unique


def _format_design_document(*, alias: str, design: str, metadata: CopycatMetadata) -> str:
    if _is_typeui_design(design):
        return _ensure_trailing_newline(design)

    source_url = metadata["sourceUrl"]
    title = _title_from_alias(alias)
    details = _demote_markdown_headings(design.strip()) or "No detailed capture notes were provided."
    caveats = _sentence_list(metadata["caveats"]) or "None recorded."
    observed_noise = _sentence_list(metadata["observedNoise"]) or "None recorded."
    confidence = metadata["confidence"] if "confidence" in metadata else "not recorded"

    return _ensure_trailing_newline(
        f"""---
name: copycat-style-{alias}
description: {_yaml_quote(f"Implementation-ready Copycat design-system guidance captured from {source_url}.")}
---

# {title} Design System

## Mission

Replicate the captured site's visual system with implementation-ready, evidence-backed guidance. Use this profile as visual direction; do not copy protected brand assets, logos, or source content unless the project has rights to use them.

## Brand

- Product/brand: {title}
- Source: {source_url}
- Product surface: {_product_surface(metadata)}
- Confidence: {confidence}
- Caveats: {caveats}
- Observed noise: {observed_noise}

## Style Foundations

- Visual style: must follow the captured mood, density, hierarchy, interaction rhythm, and component language described below.
- Typography scale: must use the captured font families, weights, sizes, line heights, and letter spacing when available; otherwise derive the closest consistent scale from `tokens.json` and evidence.
- Color palette: must map raw captured values into semantic roles before component guidance; prefer `tokens.json` over repeating raw hex values.
- Spacing scale: must reuse repeated spacing, grid, and container measurements from the capture instead of inventing one-off gaps.
- Radius, shadow, and motion tokens: must preserve repeated shape, elevation, transition, and easing patterns from the capture.

### Captured Details

{details}

## Accessibility

- Target: WCAG 2.2 AA.
- Keyboard-first interactions required for every interactive component.
- Focus-visible rules required; do not hide focus indicators.
- Contrast constraints required for text, icons, borders, charts, and state changes.
- Motion must respect `prefers-reduced-motion` while keeping state changes understandable.

## Writing Tone

Concise, confident, and implementation-focused. Use specific values, states, and layout rules; avoid vague aesthetic labels unless they are tied to captured evidence.

## Rules: Do

- Use semantic tokens in implementation guidance, not raw values, when a token exists.
- Define required states for interactive UI: default, hover, focus-visible, active, disabled, loading, and error.
- Specify responsive behavior, density changes, overflow handling, and edge-case behavior.
- Preserve component anatomy, hierarchy, and spacing relationships from the captured site.
- Ground visual claims in screenshots, CSS variables, computed styles, DOM snapshots, notes, or `tokens.json`.

## Rules: Don't

- Do not copy logos, proprietary illustrations, brand names, or marketing text into new products unless explicitly allowed.
- Do not introduce low-contrast text, hidden focus indicators, or pointer-only interactions.
- Do not create one-off spacing, type, color, radius, shadow, or motion exceptions without a captured precedent.
- Do not flatten distinctive layout rhythm into generic SaaS cards when the capture shows stronger structure.
- Do not omit mobile behavior, long-content handling, empty states, or error states for reusable components.

## Guideline Authoring Workflow

1. Restate the design intent in one sentence before implementing.
2. Map foundations to semantic tokens from `tokens.json`.
3. Define component anatomy, variants, states, and interactions.
4. Add accessibility acceptance criteria for each reusable component.
5. Add anti-patterns and migration notes when adapting the style to a different product.
6. End with a QA checklist tied to the captured evidence.

## Required Output Structure

- Context and goals.
- Design tokens and foundations.
- Component-level rules: anatomy, variants, states, responsive behavior.
- Accessibility requirements and testable acceptance criteria.
- Content and tone standards with examples.
- Anti-patterns and prohibited implementations.
- QA checklist.

## Component Rule Expectations

- Include keyboard, pointer, and touch behavior.
- Include spacing and typography token requirements.
- Include long-content, overflow, empty-state, loading-state, and error-state handling.
- Include responsive rules for desktop, tablet, and mobile when the evidence supports them.
- Include implementation notes that distinguish must-have captured patterns from optional stylistic flourishes.

## Quality Gates

- Every non-negotiable rule uses "must".
- Every recommendation uses "should".
- Every accessibility rule is testable in implementation.
- Every repeated visual pattern is represented as a token or reusable component rule.
- Prefer system consistency over local visual exceptions.

## QA Checklist

- [ ] The implementation uses the semantic tokens from `tokens.json` or clearly maps captured values into project tokens.
- [ ] Primary layouts match captured spacing, density, hierarchy, and responsive behavior.
- [ ] Interactive components include default, hover, focus-visible, active, disabled, loading, and error states.
- [ ] Text and non-text contrast meet WCAG 2.2 AA.
- [ ] Focus order, keyboard operation, and reduced-motion behavior are verified.
- [ ] The UI follows the captured style without copying protected content or assets.
"""
    )


def _is_typeui_design(design: str) -> bool:
    stripped = design.lstrip()
    return stripped.startswith("---") and all(heading in design for heading in TYPEUI_DESIGN_HEADINGS)


def _ensure_trailing_newline(value: str) -> str:
    return value if value.endswith("\n") else f"{value}\n"


def _title_from_alias(alias: str) -> str:
    return " ".join(word.capitalize() for word in alias.split("-"))


def _product_surface(metadata: CopycatMetadata) -> str:
    if not metadata["pages"]:
        return f"web page captured from {metadata['sourceUrl']}"

    surfaces: list[str] = []
    for page in metadata["pages"]:
        name = page["name"] if "name" in page else page["type"]
        reason = f" ({page['reason']})" if "reason" in page else ""
        surfaces.append(f"{page['type']} {name}: {page['url']}{reason}")
    return "; ".join(surfaces)


def _sentence_list(values: list[str]) -> str:
    return "; ".join(value.strip() for value in values if value.strip())


def _demote_markdown_headings(markdown: str) -> str:
    lines: list[str] = []
    for line in markdown.splitlines():
        match = re.match(r"^(#{1,6})(\s+.*)$", line)
        if match is None:
            lines.append(line)
            continue
        hashes, text = match.groups()
        lines.append(f"{'#' * min(len(hashes) + 3, 6)}{text}")
    return "\n".join(lines)


def _yaml_quote(value: str) -> str:
    escaped = value.replace("'", "''")
    return f"'{escaped}'"
