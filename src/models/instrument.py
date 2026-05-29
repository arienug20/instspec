"""Data models for InstSpec"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime


class InstrumentType(Enum):
    """Instrument types supported by InstSpec"""
    ORIFICE = "orifice"
    CONTROL_VALVE = "control_valve"
    FLOW_ELEMENT = "flow_element"
    DP_TRANSMITTER = "dp_transmitter"
    THERMOWELL = "thermowell"
    FLOW_TRANSMITTER = "flow_transmitter"
    PRESSURE_TRANSMITTER = "pressure_transmitter"
    TEMPERATURE_ELEMENT = "temperature_element"
    LEVEL_TRANSMITTER = "level_transmitter"


class FluidType(Enum):
    """Fluid types"""
    LIQUID = "liquid"
    GAS = "gas"
    STEAM = "steam"
    TWO_PHASE = "two_phase"


class TapType(Enum):
    """Orifice plate tap types"""
    CORNER = "corner"
    FLANGE = "flange"
    D_D2 = "d_d2"  # D and D/2 taps


class ValveStyle(Enum):
    """Control valve styles"""
    GLOBE_LINEAR = "globe_linear"
    GLOBE_EQUAL_PCT = "globe_equal_pct"
    BUTTERFLY_ECCENTRIC = "butterfly_eccentric"
    BUTTERFLY_CONCENTRIC = "butterfly_concentric"
    BALL_SEGMENTED = "ball_segmented"
    BALL_FULL_BORE = "ball_full_bore"
    PLUG_ECCENTRIC = "plug_eccentric"
    CAGE_BALANCED = "cage_balanced"


class ValveCharacteristic(Enum):
    """Control valve characteristic curves"""
    EQUAL_PERCENTAGE = "equal_percentage"
    LINEAR = "linear"
    QUICK_OPEN = "quick_open"
    MODIFIED_PARABOLIC = "modified_parabolic"


class FlowElementType(Enum):
    """Flow element types"""
    VENTURI = "venturi"
    FLOW_NOZZLE = "flow_nozzle"
    V_CONE = "v_cone"
    WEDGE = "wedge"


class ThermowellTipType(Enum):
    """Thermowell tip types"""
    STRAIGHT = "straight"
    TAPERED = "tapered"
    STEPPED = "stepped"


class ThermowellSupportType(Enum):
    """Thermowell support types"""
    FLANGED = "flanged"
    WELDED = "welded"
    THREADED = "threaded"


@dataclass
class FluidProperties:
    """Fluid properties at operating conditions"""
    density_kg_m3: float
    viscosity_Pa_s: float
    specific_heat_ratio: float  # Cp/Cv
    isentropic_exponent: float
    vapor_pressure_bar: float
    critical_pressure_bar: float
    molecular_weight_g_mol: float
    compressibility_factor: float = 1.0
    speed_of_sound_ms: float = 0.0


@dataclass
class FluidPreset:
    """Fluid preset for common fluids"""
    id: str
    name: str
    type: FluidType
    coolprop_name: Optional[str] = None
    default_properties: Optional[Dict[str, Any]] = None


@dataclass
class PipeSpec:
    """Pipe specification"""
    nominal_size: str
    schedule: str
    outside_diameter_mm: float
    wall_thickness_mm: float
    inside_diameter_mm: float
    internal_area_mm2: float
    weight_per_meter_kg: float
    material_standard: str  # "B36.10" or "B36.19"


@dataclass
class Project:
    """Project data"""
    id: str
    name: str
    description: Optional[str] = None
    client: Optional[str] = None
    location: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Revision:
    """Revision data for instrument datasheets"""
    revision_letter: str
    date: datetime
    description: str
    prepared_by: str
    checked_by: str
    approved_by: str
    changes: List[str] = field(default_factory=list)


@dataclass
class OrificeInput:
    """Input parameters for orifice plate sizing"""
    # Pipe
    pipe_id_mm: float
    pipe_schedule: str

    # Fluid
    fluid_type: FluidType
    fluid_name: str
    density_kg_m3: float
    viscosity_Pa_s: float
    isentropic_exponent: float

    # Flow conditions
    flow_unit: str
    normal_flow: float
    max_flow: float
    min_flow: float

    # Operating conditions
    operating_pressure_barg: float
    operating_temperature_C: float
    dp_transmitter_range_mbar: float

    # Tap configuration
    tap_type: TapType

    # Upstream fitting
    upstream_fitting: str


@dataclass
class OrificeResult:
    """Results from orifice plate sizing calculation"""
    # Primary results
    beta: float
    orifice_bore_mm: float
    discharge_coefficient: float
    expansibility_factor: float

    # Differential pressure
    dp_at_max_flow_mbar: float
    dp_at_normal_flow_mbar: float
    dp_at_min_flow_mbar: float

    # Reynolds
    reynolds_at_max: float
    reynolds_at_normal: float
    reynolds_at_min: float

    # Performance
    turndown_ratio: float
    permanent_pressure_loss_pct: float
    permanent_pressure_loss_bar: float

    # Straight run
    straight_run_upstream_D: float
    straight_run_upstream_mm: float
    straight_run_downstream_D: float
    straight_run_downstream_mm: float

    # Uncertainty
    total_uncertainty_pct: float
    uncertainty_breakdown: Dict[str, float]

    # Status
    beta_status: str
    dp_status: str
    reynolds_status: str
    recommendation: str
    warnings: List[str] = field(default_factory=list)


@dataclass
class CVInput:
    """Input parameters for control valve sizing"""
    # Fluid
    fluid_type: FluidType
    fluid_name: str
    density_kg_m3: float
    viscosity_Pa_s: float
    specific_heat_ratio: float
    molecular_weight: float
    critical_pressure_bar: float
    vapor_pressure_bar: float

    # Flow
    flow_unit: str
    normal_flow: float
    max_flow: float
    min_flow: float

    # Pressures
    inlet_pressure_barg: float
    outlet_pressure_barg: float

    # Temperature
    inlet_temperature_C: float

    # Valve
    valve_style: ValveStyle
    characteristic: ValveCharacteristic
    vendor: str

    # Pipe
    pipe_size_mm: float
    pipe_schedule: str


@dataclass
class CVResult:
    """Results from control valve sizing calculation"""
    # Cv
    cv_required_normal: float
    cv_required_max: float
    cv_rated_selected: float
    valve_size_selected: str

    # Opening
    percent_open_normal: float
    percent_open_max: float
    percent_open_min: float

    # Flow regime
    is_choked: bool
    is_cavitating: bool
    is_flashing: bool
    cavitation_index: float
    flash_fraction: float

    # Pressure
    velocity_at_vena_contracta_ms: float
    pressure_at_vena_contracta_bar: float
    pressure_drop_ratio_x: float

    # Noise
    noise_level_dBA: float
    noise_exceeds_limit: bool

    # Performance
    rangeability: float
    turndown: float

    # Status
    sizing_status: str
    warnings: List[str] = field(default_factory=list)
    recommendation: str = ""


@dataclass
class FlowElementInput:
    """Input parameters for flow element sizing"""
    element_type: FlowElementType
    pipe_id_mm: float
    fluid_type: FluidType
    density_kg_m3: float
    viscosity_Pa_s: float
    normal_flow: float
    max_flow: float
    min_flow: float
    operating_pressure_barg: float
    operating_temperature_C: float
    isentropic_exponent: float
    dp_transmitter_range_mbar: float


@dataclass
class FlowElementResult:
    """Results from flow element sizing calculation"""
    beta_or_ratio: float
    discharge_coefficient: float
    throat_diameter_mm: float
    dp_at_max_flow_mbar: float
    dp_at_normal_flow_mbar: float
    permanent_pressure_loss_pct: float
    straight_run_upstream_D: float
    straight_run_downstream_D: float
    reynolds_number: float
    uncertainty_pct: float
    turndown_ratio: float
    recommendation: str


@dataclass
class DPCheckResult:
    """Results from DP transmitter range check"""
    selected_range_mbar: float
    dp_max_pct_of_range: float
    dp_min_pct_of_range: float
    turndown_ratio: float
    accuracy_at_max_flow_pct: float
    accuracy_at_min_flow_pct: float
    signal_at_max_flow_mA: float
    signal_at_min_flow_mA: float
    overall_pass: bool
    warnings: List[str] = field(default_factory=list)
    recommendation: str = ""


@dataclass
class ThermowellInput:
    """Input parameters for thermowell sizing"""
    # Thermowell geometry
    insertion_length_mm: float
    bore_diameter_mm: float
    tip_diameter_mm: float
    root_diameter_mm: float
    tip_type: ThermowellTipType
    support_type: ThermowellSupportType

    # Material
    material: str

    # Process
    fluid_type: FluidType
    fluid_name: str
    velocity_ms: float
    density_kg_m3: float
    viscosity_Pa_s: float
    operating_pressure_barg: float
    operating_temperature_C: float

    # Sensor
    sensor_diameter_mm: float


@dataclass
class ThermowellResult:
    """Results from thermowell sizing calculation"""
    natural_frequency_Hz: float
    wake_frequency_Hz: float
    frequency_ratio: float
    inline_frequency_ratio: float
    ratio_status: str

    # Stress
    bending_stress_MPa: float
    pressure_stress_MPa: float
    total_stress_MPa: float
    allowable_stress_MPa: float
    stress_pass: bool

    # Fatigue
    fatigue_life_cycles: float
    fatigue_pass: bool

    # Material
    youngs_modulus_GPa: float
    material_at_temperature: str

    # Recommendations
    design_pass: bool
    recommendation: str
    warnings: List[str] = field(default_factory=list)
    suggested_max_velocity_ms: float


@dataclass
class Instrument:
    """Base instrument data"""
    id: str
    project_id: str
    tag_number: str
    instrument_type: InstrumentType
    service: Optional[str] = None
    line_number: Optional[str] = None
    fluid_type: Optional[FluidType] = None
    fluid_name: Optional[str] = None
    sizing_data: Optional[Dict[str, Any]] = None
    datasheet_data: Optional[Dict[str, Any]] = None
    status: str = "draft"
    revision: str = "A"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    revisions: List[Revision] = field(default_factory=list)