"""Questionary prompts with custom styling."""

from typing import Any, Callable

import questionary
from questionary import Style

# Custom style matching CLI theme
custom_style = Style(
    [
        ("qmark", "fg:cyan bold"),  # ? mark
        ("question", "bold"),  # Question text
        ("answer", "fg:green"),  # Selected answer
        ("pointer", "fg:cyan bold"),  # > pointer
        ("highlighted", "fg:cyan bold"),  # Highlighted choice
        ("selected", "fg:green"),  # Selected items
        ("separator", "fg:gray"),  # Separator
        ("instruction", "fg:gray italic"),  # Instructions
    ]
)


def select_from_list(
    message: str,
    choices: list[str],
    show_index: bool = True,
) -> str | None:
    """Select single item from list with index numbers.

    Args:
        message: Question to display.
        choices: List of choices.
        show_index: Whether to show index numbers.

    Returns:
        Selected choice or None if cancelled.
    """
    if not choices:
        return None

    if show_index:
        display_choices = [
            questionary.Choice(title=f"[{i + 1}] {c}", value=c)
            for i, c in enumerate(choices)
        ]
    else:
        display_choices = choices

    result = questionary.select(
        message,
        choices=display_choices,
        style=custom_style,
        use_shortcuts=False,
    ).ask()

    return result


def select_multiple(
    message: str,
    choices: list[str],
    show_index: bool = True,
) -> list[str]:
    """Select multiple items from list.

    Args:
        message: Question to display.
        choices: List of choices.
        show_index: Whether to show index numbers.

    Returns:
        List of selected choices.
    """
    if not choices:
        return []

    if show_index:
        display_choices = [
            questionary.Choice(title=f"[{i + 1}] {c}", value=c)
            for i, c in enumerate(choices)
        ]
    else:
        display_choices = choices

    result = questionary.checkbox(
        message,
        choices=display_choices,
        style=custom_style,
    ).ask()

    return result or []


def text_input(
    message: str,
    default: str = "",
    password: bool = False,
    validate: Callable[[str], bool | str] | None = None,
) -> str | None:
    """Get text input from user.

    Args:
        message: Question to display.
        default: Default value.
        password: Whether to hide input.
        validate: Optional validation function.

    Returns:
        User input or None if cancelled.
    """
    if password:
        result = questionary.password(
            message,
            style=custom_style,
            validate=validate,
        ).ask()
        return result.strip() if result else result

    result = questionary.text(
        message,
        default=default,
        style=custom_style,
        validate=validate,
    ).ask()
    return result.strip() if result else result


def confirm(message: str, default: bool = False) -> bool:
    """Yes/No confirmation.

    Args:
        message: Question to display.
        default: Default value.

    Returns:
        True if confirmed, False otherwise.
    """
    result = questionary.confirm(
        message,
        default=default,
        style=custom_style,
    ).ask()

    if result is None:
        raise KeyboardInterrupt
    return result


def fuzzy_select(
    message: str,
    choices: list[str],
    default: str = "",
) -> str | None:
    """Select from list with fuzzy/autocomplete search.

    User can type to filter choices. Useful for large lists.

    Args:
        message: Question to display.
        choices: List of choices.
        default: Default value pre-filled in the input.

    Returns:
        Selected choice or None if cancelled.
    """
    if not choices:
        return None

    result = questionary.autocomplete(
        message,
        choices=choices,
        default=default,
        style=custom_style,
        match_middle=True,
    ).ask()

    return result


def select_with_custom(
    message: str,
    choices: list[str],
    custom_label: str = "+ Enter custom value",
) -> str | None:
    """Select from list or enter custom value.

    Args:
        message: Question to display.
        choices: List of choices.
        custom_label: Label for custom option.

    Returns:
        Selected or custom value, None if cancelled.
    """
    all_choices = [
        questionary.Choice(title=f"[{i + 1}] {c}", value=c) for i, c in enumerate(choices)
    ]
    all_choices.append(questionary.Choice(title=custom_label, value="__custom__"))

    result = questionary.select(
        message,
        choices=all_choices,
        style=custom_style,
    ).ask()

    if result == "__custom__":
        return text_input("Enter value:")

    return result
