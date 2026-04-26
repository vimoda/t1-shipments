from __future__ import annotations

import logging

_LOGGER_NAME = "t1envios"


def get_logger(name: str = _LOGGER_NAME) -> logging.Logger:
    return logging.getLogger(name)


def configure_logging(level: str | int) -> None:
    """Set up a handler and level on the root t1envios logger.

    Call this from CLI entry points or when using the SDK standalone.
    Applications that manage their own logging should NOT call this —
    just set the level on logging.getLogger("t1envios") themselves.
    """
    logger = logging.getLogger(_LOGGER_NAME)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
        logger.addHandler(handler)
    logger.setLevel(level)
