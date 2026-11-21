"""UI-automation fallback — ISOLATED adapter, used only for operations
the documented Local API does not support, and only with the user's
explicit confirmation. No UI automation is implemented yet: this module
is a clearly-marked placeholder so no silent fallback can happen.

Do NOT implement pyautogui / clicks here without a confirmed operation
and a screenshot + error record for every attempt.
"""


class UiFallbackNotImplemented(NotImplementedError):
    pass


def launch_via_ui(profile_name: str) -> None:
    raise UiFallbackNotImplemented(
        "UI-automation fallback is not implemented for launching "
        f"profile {profile_name!r}. Use the Local API (runProfile) instead, "
        "or confirm the manual steps first.")
