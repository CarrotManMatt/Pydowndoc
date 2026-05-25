"""Project build script to convert this project's AsciiDoc README file to Markdown format."""

import inspect
import os
import re
import shutil
import subprocess
import sys
import warnings
from collections.abc import Collection, Iterable
from pathlib import Path
from typing import TYPE_CHECKING

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

from hatchling.metadata.plugin.interface import MetadataHookInterface

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from typing import Final

__all__: "Sequence[str]" = ("DowndocCustomReadmeMetadataHook",)


class DowndocCustomReadmeMetadataHook(MetadataHookInterface):
    """Hatchling metadata hook to convert this project's AsciiDoc file to Markdown format."""

    PLUGIN_NAME = "custom"

    @classmethod
    def _get_raw_readme_path(cls, config: "Mapping[str, object]") -> str:
        try:
            invalid_readme_path_key: object | str = config["path"]
        except KeyError:
            pass
        else:
            if isinstance(invalid_readme_path_key, str):
                INVALID_README_PATH_KEY_MESSAGE: str = (
                    f"Using {cls.PLUGIN_NAME}.path is not supported as a configuration key "
                    "to select the README file, "
                    "as it has ambiguity with selecting the path of this custom plugin. "
                )
                raise TypeError(INVALID_README_PATH_KEY_MESSAGE)

        try:
            raw_readme_path: object | str = config["readme-path"]
        except KeyError:
            return "README.adoc"

        if not isinstance(raw_readme_path, str):
            INVALID_PATH_TYPE_MESSAGE: str = f"{cls.PLUGIN_NAME}.readme-path must be a string."
            raise TypeError(INVALID_PATH_TYPE_MESSAGE)

        return raw_readme_path

    @classmethod
    def _get_readme_path(cls, config: "Mapping[str, object]", root: "Path") -> "Path":
        return root / cls._get_raw_readme_path(config)

    @classmethod
    def _is_project_misconfigured(cls, metadata: "Mapping[str, object]") -> bool:
        if "readme" in metadata:
            return True

        dynamic: object | Collection[object] = metadata.get("dynamic", [])
        if not isinstance(dynamic, Collection):
            INVALID_DYNAMIC_TYPE_MESSAGE: Final[str] = (
                "'dynamic' field within `[project]` must be an array."
            )
            raise TypeError(INVALID_DYNAMIC_TYPE_MESSAGE)

        return "readme" not in dynamic

    @override
    def update(self, metadata: dict[str, object]) -> None:
        if (
            ("update", __file__)
            in ((frame.function, frame.filename) for frame in inspect.stack()[1:])
        ):  # SOURCE: https://github.com/flying-sheep/hatch-docstring-description/blob/2dfbfba2c48e112825fdd0cb7c37035d5598224c/src/hatch_docstring_description/read_description.py#L21
            return

        project_name: object = metadata["name"]
        if not isinstance(project_name, str):
            INVALID_PROJECT_NAME_TYPE_MESSAGE: str = (
                f"Expected project name to be a string, not {type(project_name).__name__}."
            )
            raise TypeError(INVALID_PROJECT_NAME_TYPE_MESSAGE)

        if self._is_project_misconfigured(metadata):
            MISSING_DYNAMIC_MESSAGE: Final[str] = (
                "You must add 'readme' to your `dynamic` fields and not to `[project]`."
            )
            raise TypeError(MISSING_DYNAMIC_MESSAGE)

        readme_path: Path = self._get_readme_path(self.config, Path(self.root))

        if not readme_path.is_file():
            raise FileNotFoundError(str(readme_path))

        try:
            metadata["readme"] = {
                "content-type": "text/markdown",
                "text": _DowndocReadmeConverter(project_name).convert(readme_path),
            }
        except OSError as e:
            if (
                "/renovate/" not in os.environ["PWD"]
                and os.getenv("SKIP_MISSING_DOWNDOC", "False") != "True"
            ):
                raise e from e

            warnings.warn(
                (
                    f"{e} This package will be built without any README content, "
                    "it MUST NOT BE UPLOADED to any package distribution platform "
                    "(E.g. PyPI)."
                ),
                stacklevel=1,
            )
            metadata["readme"] = {
                "content-type": "text/plain",
                "text": (
                    "Missing README content. "
                    "DO NOT UPLOAD this package to any distribution platform (E.g. PyPI).\n\n"
                    "If you are seeing this message on a package distribution platform, "
                    "please contact the project's maintainer."
                ),
            }

        if isinstance(metadata["dynamic"], Iterable):
            metadata["dynamic"] = [value for value in metadata["dynamic"] if value != "readme"]


class _DowndocReadmeConverter:
    @override
    def __init__(self, project_name: str) -> None:
        self.project_name: str = project_name

    def convert(self, readme_path: "Path") -> str:
        downdoc_executable: str | None = shutil.which("downdoc")
        if downdoc_executable is None:
            DOWNDOC_NOT_INSTALLED_MESSAGE: Final[str] = (
                "The downdoc executable could not be found. "
                "(It can be installed with `uv tool install Pydowndoc-bin`.)"
            )
            raise OSError(DOWNDOC_NOT_INSTALLED_MESSAGE)

        return self._post_process(
            subprocess.run(
                (downdoc_executable, "--output", "-", "--", "-"),
                capture_output=True,
                text=True,
                check=True,
                input=self._pre_process(readme_path.read_text()),
            ).stdout
        )

    @classmethod
    def _pre_process(cls, readme_content: str) -> str:
        readme_content = readme_content.replace("\n****\n", "\n____\n")
        readme_content = re.sub(
            r"(?<=\n\[source)([^]\n]*]\n)(.+)(?=\n)",
            (
                lambda match: (
                    match.group()
                    if (
                        re.search(r"\A(?:-{2,}|_{2,}|={2,}|\.{3,})(?=\n|\Z)", match.group(2))
                        is not None
                    )
                    else f"{match.group(1)}----\n{match.group(2)}\n----"
                )
            ),
            readme_content,
        )
        readme_content = re.sub(
            r"(\*{2})([^*\n]+)\1(?=[A-Za-z0-9])", r"***\2***", readme_content
        )
        return readme_content  # noqa: RET504

    @classmethod
    def _replace_summary_title(cls, match: re.Match[str]) -> str:
        replaced_summary_title: str = re.sub(
            r"`(\+?)(.*?)\1`", r"<code>\2</code>", match.group()
        )
        replaced_summary_title = re.sub(r"_(.*?)_", r"<em>\1</em>", replaced_summary_title)
        replaced_summary_title = re.sub(
            r"\*(.*?)\*", r"<strong>\1</strong>", replaced_summary_title
        )
        return replaced_summary_title  # noqa: RET504

    def _replace_pydowndoc_multiline_table_cell(self, match: re.Match[str]) -> str:
        if self.project_name != "Pydowndoc":
            INVALID_PROJECT_NAME_MESSAGE: Final[str] = (
                "Cannot replace multiline table cells for projects other than Pydowndoc."
            )
            raise ValueError(INVALID_PROJECT_NAME_MESSAGE)

        replaced_multiline_table_cell: str = re.sub(
            r"(?<=\.) \.(Supported Conversion Backends)(?= )", r"<br><br>**\1**", match.group()
        )
        replaced_multiline_table_cell = re.sub(
            r" +(`)(?=[a-z-]+`:+)", r"<br>\1", replaced_multiline_table_cell
        )
        replaced_multiline_table_cell = re.sub(
            r"(?<=[a-z-]`)::(?= [A-Z[h(])", r":", replaced_multiline_table_cell
        )
        return replaced_multiline_table_cell  # noqa: RET504

    def _post_process(self, converted_readme: str) -> str:
        post_processed_readme: str = re.sub(
            r"(?<=<summary>).*?(?=</summary>)", self._replace_summary_title, converted_readme
        )
        post_processed_readme = re.sub(
            r"([^>]\s+|\A)(\*\*)(?=[^\w\s!\"^*()_+='@#~;:.><,`-]\s*(?:TIP|NOTE|HINT|WARNING|INFO|INFORMATION|HAZARD|CAUTION|IMPORTANT)\s*:?\s*\*\*\\\n)",
            r"\1> \2",
            post_processed_readme,
        )
        if self.project_name == "Pydowndoc":
            post_processed_readme = re.sub(
                r"(?<= \| )[^|]+?(?= \|(?:\n|\Z))",
                self._replace_pydowndoc_multiline_table_cell,
                post_processed_readme,
            )
        post_processed_readme = post_processed_readme.replace("**\n\n```", "**\n```")
        post_processed_readme = re.sub(
            r"\[([^[]+)]\(\s*pass\s*:\s*[a-z]+\)\s*\[([^[]+)]",
            r"[\2](\1)",
            post_processed_readme,
        )
        post_processed_readme = re.sub(
            r"(\*{4})([^*\n]+)\1(?=[A-Za-z0-9])", r"**\2**", post_processed_readme
        )
        return post_processed_readme  # noqa: RET504
