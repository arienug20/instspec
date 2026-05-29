"""InstSpec Configuration Module"""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    """Application configuration"""

    # Project paths
    PROJECT_ROOT: Path = Path(__file__).parent.parent
    DATA_DIR: Path = PROJECT_ROOT / "src" / "data"
    TEMPLATES_DIR: Path = PROJECT_ROOT / "src" / "templates"

    # Database
    DATABASE_URL: str = "sqlite:///instspec.db"

    # Streamlit
    APP_TITLE: str = "InstSpec - Instrument Data Sheet Generator & Sizer"
    PAGE_ICON: str = "🔧"
    LAYOUT: str = "wide"

    # Units
    DEFAULT_PRESSURE_UNIT: str = "bar"
    DEFAULT_TEMPERATURE_UNIT: str = "°C"
    DEFAULT_FLOW_UNIT: str = "kg/h"

    # Paper sizes (in points, 1 pt = 1/72 inch)
    A4_WIDTH_PT: float = 595.28
    A4_HEIGHT_PT: float = 841.89
    LETTER_WIDTH_PT: float = 612.0
    LETTER_HEIGHT_PT: float = 792.0

    # Fonts
    DEFAULT_FONT: str = "Helvetica"
    FONT_SIZE_SMALL: int = 8
    FONT_SIZE_NORMAL: int = 10
    FONT_SIZE_LARGE: int = 12

    # Standards
    ORIFICE_MIN_BETA: float = 0.10
    ORIFICE_MAX_BETA: float = 0.75
    ORIFICE_PREFERRED_BETA_MIN: float = 0.20
    ORIFICE_PREFERRED_BETA_MAX: float = 0.60

    # Valve
    DEFAULT_VALVE_RANGEABILITY: float = 50.0

    # Thermowell
    THERMOWELL_SAFE_FREQUENCY_RATIO: float = 0.8
    THERMOWELL_CAUTION_FREQUENCY_RATIO: float = 0.9

# Global config instance
config = Config()