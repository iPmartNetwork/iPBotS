"""Panel services for managing VPN servers."""

from core.services.panel.base import BasePanelService
from core.services.panel.xui import XUIService
from core.services.panel.hiddify import HiddifyService
from core.services.panel.marzban import MarzbanService
from core.services.panel.marzneshin import MarzneshinService
from core.services.panel.ibsng import IBSngService
from core.services.panel.mikrotik import MikrotikService
from core.services.panel.wgdashboard import WGDashboardService

__all__ = [
    "BasePanelService",
    "XUIService",
    "HiddifyService",
    "MarzbanService",
    "MarzneshinService",
    "IBSngService",
    "MikrotikService",
    "WGDashboardService",
]
