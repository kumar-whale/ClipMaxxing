"""ClipMaxxing (formerly ClipMaxing, ClipX, and before that ClipKontrast).

Settings written for the older names (CLIPMAXING_*, CLIPX_* or CLIPKONTRAST_* in .env or the environment) keep working: each one
is copied to its CLIPMAXXING_* name, unless that name is set too."""
import os

LEGACY_PREFIXES = ("CLIPMAXING_", "CLIPX_", "CLIPKONTRAST_")


def legacy_env():
    for k, v in list(os.environ.items()):
        for old in LEGACY_PREFIXES:
            if k.startswith(old):
                os.environ.setdefault("CLIPMAXXING_" + k[len(old):], v)


legacy_env()
