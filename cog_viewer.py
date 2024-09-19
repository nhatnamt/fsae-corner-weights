import asyncio
from typing import Callable, Optional

from nicegui.element import Element


class CogViewer(Element, component='cog_viewer.js'):
    SCALE_FACTOR = 0.6

    def __init__(self, on_change: Optional[Callable] = None) -> None:
        super().__init__()
        self.update_cog(0.5, 0.5)

    def update_cog(self, f2r_ratio, l2r_ratio) -> None:
        self._props['f2r_ratio'] = f2r_ratio
        self._props['l2r_ratio'] = l2r_ratio
        self.update()
        self.run_method('update')

    @staticmethod
    def mm2px(mm: float) -> float:
        return mm * CogViewer.SCALE_FACTOR

    @staticmethod
    def px2mm(px: float) -> float:
        return px / CogViewer.SCALE_FACTOR
