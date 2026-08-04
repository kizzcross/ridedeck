from .base import BaseAdapter
from .fixture import FixtureAdapter
from .tcgcsv import TCGCSVAdapter

_ADAPTERS: dict[str, type[BaseAdapter]] = {
    FixtureAdapter.key: FixtureAdapter,
    TCGCSVAdapter.key: TCGCSVAdapter,
}


def get_adapter(key: str, config: dict | None = None) -> BaseAdapter:
    try:
        cls = _ADAPTERS[key]
    except KeyError as exc:
        raise ValueError(f"Unknown adapter '{key}'. Available: {list(_ADAPTERS)}") from exc
    return cls(config)


def available_adapters() -> list[str]:
    return list(_ADAPTERS)
