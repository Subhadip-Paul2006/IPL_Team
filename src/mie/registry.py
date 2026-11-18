"""Typed registry for the seven specialized MIE engine adapters."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from src.mie.adapters.base import EngineAdapter
from src.mie.adapters.cdcre_adapter import CDCREAdapter
from src.mie.adapters.cmie_adapter import CMIEAdapter
from src.mie.adapters.cppae_adapter import CPPAEAdapter
from src.mie.adapters.pire_adapter import PIREAdapter
from src.mie.adapters.pvre_adapter import PVREAdapter
from src.mie.adapters.sice_adapter import SICEAdapter
from src.mie.adapters.tmve_adapter import TMVEAdapter
from src.mie.contracts import EngineName


class MIEEngineRegistry:
    """Expose a read-only, engine-keyed view of MIE's typed adapters."""

    def __init__(
        self,
        *,
        pire: PIREAdapter,
        tmve: TMVEAdapter,
        cdcre: CDCREAdapter,
        cppae: CPPAEAdapter,
        cmie: CMIEAdapter,
        sice: SICEAdapter,
        pvre: PVREAdapter,
    ) -> None:
        """Register exactly one typed adapter for each specialized engine."""
        adapters: dict[EngineName, EngineAdapter] = {
            EngineName.PIRE: pire,
            EngineName.TMVE: tmve,
            EngineName.CDCRE: cdcre,
            EngineName.CPPAE: cppae,
            EngineName.CMIE: cmie,
            EngineName.SICE: sice,
            EngineName.PVRE: pvre,
        }
        if len(adapters) != 7:
            raise ValueError("MIE requires exactly seven specialized engine adapters")
        mismatches = [
            f"{key.value} registered with {adapter.engine_name.value} adapter"
            for key, adapter in adapters.items()
            if adapter.engine_name != key
        ]
        if mismatches:
            raise ValueError("MIE adapter identity mismatch: " + "; ".join(mismatches))
        self._adapters: Mapping[EngineName, EngineAdapter] = MappingProxyType(adapters)

    @property
    def adapters(self) -> Mapping[EngineName, EngineAdapter]:
        """Return the immutable engine-to-adapter mapping."""
        return self._adapters

    def get(self, engine: EngineName) -> EngineAdapter:
        """Return the adapter registered for an engine."""
        return self._adapters[engine]


__all__ = ["MIEEngineRegistry"]
