"""Control Valve Sizer Module

ISA-75.01 / IEC 60534-2-1 compliant control valve sizing calculations.
"""

import math
from typing import Tuple, Optional, Dict, List
from dataclasses import dataclass, field

from ..models import (
    CVInput, CVResult, ValveStyle, ValveCharacteristic, FluidType
)
from ..utils.validators import Validators


class ControlValveSizer:
    """Control valve sizer per ISA-75.01.01-2012 (IEC 60534-2-1)"""

    # Valve-specific parameters
    VALVE_PARAMETERS = {
        ValveStyle.GLOBE_LINEAR: {
            'FL': 0.90,
            'xT': 0.72,
            'Fd': 0.46,
            'rangeability': 50.0
        },
        ValveStyle.GLOBE_EQUAL_PCT: {
            'FL': 0.90,
            'xT': 0.72,
            'Fd': 0.46,
            'rangeability': 50.0
        },
        ValveStyle.BUTTERFLY_ECCENTRIC: {
            'FL': 0.66,
            'xT': 0.40,
            'Fd': 0.50,
            'rangeability': 50.0
        },
        ValveStyle.BUTTERFLY_CONCENTRIC: {
            'FL': 0.55,
            'xT': 0.30,
            'Fd': 0.70,
            'rangeability': 50.0
        },
        ValveStyle.BALL_SEGMENTED: {
            'FL': 0.60,
            'xT': 0.42,
            'Fd': 0.98,
            'rangeability': 50.0
        },
        ValveStyle.BALL_FULL_BORE: {
            'FL': 0.55,
            'xT': 0.30,
            'Fd': 0.20,
            'rangeability': 50.0
        },
        ValveStyle.PLUG_ECCENTRIC: {
            'FL': 0.85,
            'xT': 0.60,
            'Fd': 0.46,
            'rangeability': 50.0
        },
        ValveStyle.CAGE_BALANCED: {
            'FL': 0.90,
            'xT': 0.72,
            'Fd': 0.46,
            'rangeability': 50.0
        },
    }

    # Cv table for common valve sizes (example data - should be loaded from JSON)
    CV_TABLE = {
        '1/2': 3.0,
        '3/4': 5.0,
        '1': 10.0,
        '1.5': 25.0,
        '2': 45.0,
        '3': 100.0,
        '4': 165.0,
        '6': 400.0,
        '8': 650.0,
        '10': 1000.0,
        '12': 1500.0,
    }

    def __init__(self, input_params: CVInput):
        """Initialize control valve sizer with input parameters

        Args:
            input_params: CVInput dataclass with all input parameters
        """
        self.input = input_params
        self.validator = Validators()

        # Get valve parameters
        valve_params = self.VALVE_PARAMETERS.get(
            self.input.valve_style,
            self.VALVE_PARAMETERS[ValveStyle.GLOBE_EQUAL_PCT]
        )
        self.FL = valve_params['FL']
        self.xT = valve_params['xT']
        self.Fd = valve_params['Fd']
        self.rangeability = valve_params['rangeability']

        # Convert pressures to bar (if needed)
        self.P1 = self.input.inlet_pressure_barg
        self.P2 = self.input.outlet_pressure_barg
        self.delta_P = self.P1 - self.P2

        # Temperature to K
        self.T = self.input.inlet_temperature_C + 273.15

        # Fluid properties
        self.rho = self.input.density_kg_m3
        self.mu = self.input.viscosity_Pa_s
        self.k = self.input.specific_heat_ratio
        self.Pc = self.input.critical_pressure_bar
        self.Pv = self.input.vapor_pressure_bar

        # Convert flow to m³/h (for Cv calculation)
        self.Q_normal = self._convert_flow_to_m3_h(self.input.normal_flow, self.input.flow_unit)
        self.Q_max = self._convert_flow_to_m3_h(self.input.max_flow, self.input.flow_unit)
        self.Q_min = self._convert_flow_to_m3_h(self.input.min_flow, self.input.flow_unit)

        # Calculate pressure drop ratio
        self.x = self.delta_P / self.P1 if self.P1 > 0 else 0

        # Calculate Fk (specific heat ratio factor)
        self.Fk = self.k / 1.4

    def _convert_flow_to_m3_h(self, flow: float, unit: str) -> float:
        """Convert flow to m³/h

        Args:
            flow: Flow value
            unit: Flow unit

        Returns:
            Flow in m³/h
        """
        if unit == 'm³/h':
            return flow
        elif unit == 'kg/h':
            return flow / self.rho
        elif unit == 'kg/s':
            return flow * 3600.0 / self.rho
        elif unit == 'GPM':
            # 1 GPM = 3.78541 L/min = 0.227124 m³/h
            return flow * 0.227124
        elif unit == 'BPD':
            # 1 BPD = 0.158987 m³/day = 0.006624 m³/h
            return flow * 0.006624
        else:
            raise ValueError(f"Unknown flow unit: {unit}")

    def _cv_liquid(self, Q: float, P1: float, P2: float) -> float:
        """Calculate Cv for liquid flow

        ISA-75.01.01-2012 / IEC 60534-2-1 Equation 1

        Non-choked: Cv = Q / (N1 × √(ΔP / Gf))

        Args:
            Q: Flow rate [m³/h]
            P1: Inlet pressure [bar]
            P2: Outlet pressure [bar]

        Returns:
            Cv value
        """
        delta_P = P1 - P2
        Gf = self.rho / 997.0  # Specific gravity (water = 997 kg/m³)

        # Calculate FF (critical pressure ratio factor)
        FF = 0.96 - 0.28 * math.sqrt(self.Pv / self.Pc)

        # Check for choked flow
        delta_P_choked = (self.FL**2) * (P1 - FF * self.Pv)

        effective_delta_P = min(delta_P, delta_P_choked)

        # N1 = 0.0865 for m³/h and bar
        N1 = 0.0865

        Cv = Q / (N1 * math.sqrt(effective_delta_P / Gf))

        return Cv

    def _cv_gas(self, w: float, P1: float, P2: float) -> float:
        """Calculate Cv for gas/vapor flow

        ISA-75.01.01-2012 / IEC 60534-2-1 Equations 6-11

        Args:
            w: Mass flow rate [kg/h]
            P1: Inlet pressure [bar]
            P2: Outlet pressure [bar]

        Returns:
            Cv value
        """
        delta_P = P1 - P2
        x = delta_P / P1

        # Check for choked flow
        x_choked = self.Fk * self.xT

        if x >= x_choked:
            # Choked flow
            x_effective = x_choked
            Y = 2.0 / 3.0
        else:
            # Non-choked flow
            x_effective = x
            Y = 1 - x_effective / (3 * self.Fk * self.xT)

        # N8 = 94.8 for kg/h, bar, K
        N8 = 94.8

        # Specific weight at inlet [N/m³]
        gamma1 = self.rho * 9.81

        # Fp = 1.0 (no reducer)
        Fp = 1.0

        Cv = w / (N8 * Fp * Y * math.sqrt(x_effective * P1 * gamma1))

        return Cv

    def _cv_twophase(self, wL: float, wG: float, P1: float, P2: float) -> float:
        """Calculate Cv for two-phase flow

        ISA-75.01.01-2012 Annex B

        Args:
            wL: Liquid mass flow [kg/h]
            wG: Gas mass flow [kg/h]
            P1: Inlet pressure [bar]
            P2: Outlet pressure [bar]

        Returns:
            Cv value
        """
        # Calculate Cv for each phase separately
        # This is a simplified approach
        Cv_liquid = self._cv_liquid(wL / self.rho, P1, P2)
        Cv_gas = self._cv_gas(wG, P1, P2)

        # Combine (simplified)
        Cv_total = Cv_liquid + Cv_gas

        return Cv_total

    def _cavitation_index(self, P1: float, P2: float) -> float:
        """Calculate cavitation index

        σ = (P1 - Pv) / (P1 - P2)

        Args:
            P1: Inlet pressure [bar]
            P2: Outlet pressure [bar]

        Returns:
            Cavitation index σ
        """
        sigma = (P1 - self.Pv) / (P1 - P2) if (P1 - P2) > 0 else float('inf')
        return sigma

    def _check_cavitation(self, P1: float, P2: float) -> Tuple[bool, float]:
        """Check for cavitation

        Args:
            P1: Inlet pressure [bar]
            P2: Outlet pressure [bar]

        Returns:
            Tuple of (is_cavitating, cavitation_index)
        """
        sigma = self._cavitation_index(P1, P2)

        is_cavitating = sigma <= 2.0  # Incipient cavitation

        return is_cavitating, sigma

    def _check_flashing(self, P2: float) -> bool:
        """Check for flashing

        Args:
            P2: Outlet pressure [bar]

        Returns:
            True if flashing occurs
        """
        return P2 < self.Pv

    def _check_choked_gas(self, x: float) -> bool:
        """Check for choked gas flow

        Args:
            x: Pressure drop ratio

        Returns:
            True if flow is choked
        """
        x_choked = self.Fk * self.xT
        return x >= x_choked

    def _noise_prediction_liquid(self, Cv: float) -> float:
        """Predict noise level for liquid flow

        Simplified ISA-75.01.01-2012 noise prediction

        Args:
            Cv: Valve Cv

        Returns:
            Noise level in dBA at 1m
        """
        # Simplified correlation
        noise_dBA = 10 * math.log10(Cv) + 60
        return noise_dBA

    def _noise_prediction_gas(self, Cv: float) -> float:
        """Predict noise level for gas flow

        Simplified ISA-75.01.01-2012 noise prediction

        Args:
            Cv: Valve Cv

        Returns:
            Noise level in dBA at 1m
        """
        # Simplified correlation including Fd
        noise_dBA = 10 * math.log10(Cv * self.Fd * self.P1) + 50
        return noise_dBA

    def _calculate_opening_percentage(self, Cv_actual: float, Cv_rated: float,
                                       characteristic: ValveCharacteristic) -> float:
        """Calculate valve opening percentage

        Args:
            Cv_actual: Actual Cv at operating condition
            Cv_rated: Rated Cv of valve
            characteristic: Valve characteristic curve

        Returns:
            Opening percentage (0-100%)
        """
        ratio = Cv_actual / Cv_rated

        if characteristic == ValveCharacteristic.LINEAR:
            opening = ratio
        elif characteristic == ValveCharacteristic.EQUAL_PERCENTAGE:
            # Cv_actual = Cv_rated × R^(travel - 1)
            # travel = 1 + log(Cv_actual/Cv_rated) / log(R)
            opening = 1 + math.log(ratio) / math.log(self.rangeability)
        elif characteristic == ValveCharacteristic.QUICK_OPEN:
            opening = ratio**2
        elif characteristic == ValveCharacteristic.MODIFIED_PARABOLIC:
            # Cv/Cv_rated = (travel² + travel) / 2
            # Solve quadratic: travel² + travel - 2*ratio = 0
            opening = (-1 + math.sqrt(1 + 8 * ratio)) / 2
        else:
            opening = ratio

        # Clamp to 0-1 range
        opening = max(0.0, min(1.0, opening))

        return opening * 100.0

    def _select_valve(self, Cv_required: float) -> Tuple[float, str]:
        """Select appropriate valve size

        Args:
            Cv_required: Required Cv at max flow

        Returns:
            Tuple of (Cv_rated, valve_size)
        """
        # Find smallest valve with Cv >= required * 1.2 (20% margin)
        Cv_min = Cv_required * 1.2

        selected_Cv = None
        selected_size = None

        for size, Cv_rated in sorted(self.CV_TABLE.items(), key=lambda x: float(x[0])):
            if Cv_rated >= Cv_min:
                selected_Cv = Cv_rated
                selected_size = size
                break

        # If no suitable valve found, use largest
        if selected_Cv is None:
            selected_Cv = max(self.CV_TABLE.values())
            selected_size = max(self.CV_TABLE.keys(), key=lambda x: float(x[0]))

        return selected_Cv, selected_size

    def _calculate_pressure_at_vena_contracta(self) -> Tuple[float, float]:
        """Calculate pressure and velocity at vena contracta

        Args:
            None

        Returns:
            Tuple of (pressure_bar, velocity_ms)
        """
        # Pressure at vena contracta
        P_vc = self.P1 - (self.FL**2) * self.delta_P

        # Velocity at vena contracta (simplified)
        # Use area ratio approximation
        velocity = math.sqrt(2 * self.delta_P * 1e5 / self.rho)  # m/s

        return max(0.0, P_vc), velocity

    def size_valve(self) -> CVResult:
        """Perform complete valve sizing

        Returns:
            CVResult with all calculations
        """
        warnings = []
        sizing_status = "ok"

        # Calculate required Cv based on fluid type
        if self.input.fluid_type == FluidType.LIQUID:
            Cv_required_normal = self._cv_liquid(self.Q_normal, self.P1, self.P2)
            Cv_required_max = self._cv_liquid(self.Q_max, self.P1, self.P2)

            # Check for cavitation
            is_cavitating, cavitation_index = self._check_cavitation(self.P1, self.P2)

            if cavitation_index <= 1.0:
                warnings.append(f"⚠️ Full cavitation expected (σ = {cavitation_index:.2f})")
                sizing_status = "choked_warning"
            elif cavitation_index <= 2.0:
                warnings.append(f"⚠️ Incipient cavitation (σ = {cavitation_index:.2f})")

            # Check for flashing
            is_flashing = self._check_flashing(self.P2)
            if is_flashing:
                warnings.append("⚠️ Flashing expected downstream")
                sizing_status = "choked_warning"

            is_choked = False
            flash_fraction = 0.0

        elif self.input.fluid_type in [FluidType.GAS, FluidType.STEAM]:
            # Convert volumetric to mass flow for gas
            w_normal = self.Q_normal * self.rho
            w_max = self.Q_max * self.rho

            Cv_required_normal = self._cv_gas(w_normal, self.P1, self.P2)
            Cv_required_max = self._cv_gas(w_max, self.P1, self.P2)

            # Check for choked flow
            is_choked = self._check_choked_gas(self.x)

            if is_choked:
                warnings.append("⚠️ Choked flow detected")
                sizing_status = "choked_warning"

            is_cavitating = False
            cavitation_index = 0.0
            is_flashing = False
            flash_fraction = 0.0

        else:  # TWO_PHASE
            # Simplified two-phase
            wL = self.Q_normal * self.rho * 0.5  # Assume 50% liquid
            wG = self.Q_normal * self.rho * 0.5  # Assume 50% gas

            Cv_required_normal = self._cv_twophase(wL, wG, self.P1, self.P2)
            Cv_required_max = Cv_required_normal * (self.Q_max / self.Q_normal)

            is_choked = False
            is_cavitating = False
            cavitation_index = 0.0
            is_flashing = False
            flash_fraction = 0.5

        # Select valve
        Cv_rated, valve_size = self._select_valve(Cv_required_max)

        # Check if valve is undersized
        if Cv_rated < Cv_required_max:
            warnings.append(f"✗ Valve undersized: Required Cv={Cv_required_max:.2f}, Rated Cv={Cv_rated:.2f}")
            sizing_status = "undersized"

        # Calculate opening percentages
        if self.input.fluid_type == FluidType.LIQUID:
            Cv_min = self._cv_liquid(self.Q_min, self.P1, self.P2)
        elif self.input.fluid_type in [FluidType.GAS, FluidType.STEAM]:
            Cv_min = self._cv_gas(self.Q_min * self.rho, self.P1, self.P2)
        else:
            Cv_min = Cv_required_min = self._cv_twophase(
                self.Q_min * self.rho * 0.5,
                self.Q_min * self.rho * 0.5,
                self.P1, self.P2
            )

        percent_open_normal = self._calculate_opening_percentage(
            Cv_required_normal, Cv_rated, self.input.characteristic
        )
        percent_open_max = self._calculate_opening_percentage(
            Cv_required_max, Cv_rated, self.input.characteristic
        )
        percent_open_min = self._calculate_opening_percentage(
            Cv_min, Cv_rated, self.input.characteristic
        )

        # Check opening constraints
        if percent_open_max > 90:
            warnings.append(f"⚠️ Opening at max flow: {percent_open_max:.1f}% (limit: 90%)")
            sizing_status = "undersized"

        if percent_open_normal < 50 or percent_open_normal > 80:
            warnings.append(f"⚠️ Opening at normal flow: {percent_open_normal:.1f}% (target: 50-80%)")

        if percent_open_min < 20:
            warnings.append(f"⚠️ Opening at min flow: {percent_open_min:.1f}% (limit: 20%)")

        if percent_open_normal < 30 and percent_open_normal > 0:
            sizing_status = "oversized"

        # Pressure at vena contracta
        P_vc, velocity_vc = self._calculate_pressure_at_vena_contracta()

        # Noise prediction
        if self.input.fluid_type == FluidType.LIQUID:
            noise_level = self._noise_prediction_liquid(Cv_rated)
        else:
            noise_level = self._noise_prediction_gas(Cv_rated)

        noise_exceeds_limit = noise_level > 85.0

        if noise_exceeds_limit:
            warnings.append(f"⚠️ Noise level {noise_level:.1f} dBA exceeds 85 dBA limit")

        # Performance metrics
        turndown = self.input.max_flow / self.input.min_flow if self.input.min_flow > 0 else float('inf')

        # Generate recommendation
        recommendation = self._generate_recommendation(
            Cv_required_max, Cv_rated, percent_open_normal, percent_open_max,
            is_choked, is_cavitating, cavitation_index
        )

        return CVResult(
            cv_required_normal=Cv_required_normal,
            cv_required_max=Cv_required_max,
            cv_rated_selected=Cv_rated,
            valve_size_selected=valve_size,
            percent_open_normal=percent_open_normal,
            percent_open_max=percent_open_max,
            percent_open_min=percent_open_min,
            is_choked=is_choked,
            is_cavitating=is_cavitating,
            is_flashing=is_flashing,
            cavitation_index=cavitation_index,
            flash_fraction=flash_fraction,
            velocity_at_vena_contracta_ms=velocity_vc,
            pressure_at_vena_contracta_bar=P_vc,
            pressure_drop_ratio_x=self.x,
            noise_level_dBA=noise_level,
            noise_exceeds_limit=noise_exceeds_limit,
            rangeability=self.rangeability,
            turndown=turndown,
            sizing_status=sizing_status,
            warnings=warnings,
            recommendation=recommendation
        )

    def _generate_recommendation(self, Cv_required: float, Cv_rated: float,
                                   opening_normal: float, opening_max: float,
                                   is_choked: bool, is_cavitating: bool,
                                   cavitation_index: float) -> str:
        """Generate human-readable recommendation

        Args:
            Cv_required: Required Cv at max flow
            Cv_rated: Rated Cv of selected valve
            opening_normal: Opening at normal flow [%]
            opening_max: Opening at max flow [%]
            is_choked: Is flow choked
            is_cavitating: Is cavitation expected
            cavitation_index: Cavitation index

        Returns:
            Recommendation string
        """
        parts = []

        margin = (Cv_rated / Cv_required - 1) * 100
        parts.append(f"✓ Cv margin: {margin:.1f}% (Rated: {Cv_rated:.1f}, Required: {Cv_required:.1f})")
        parts.append(f"✓ Valve size: {self.valve_size_selected}\"")

        if 50 <= opening_normal <= 80:
            parts.append(f"✓ Opening at normal flow: {opening_normal:.1f}% (optimal)")
        elif opening_normal < 50:
            parts.append(f"⚠ Opening at normal flow: {opening_normal:.1f}% (below optimal)")
        else:
            parts.append(f"⚠ Opening at normal flow: {opening_normal:.1f}% (above optimal)")

        if opening_max <= 90:
            parts.append(f"✓ Opening at max flow: {opening_max:.1f}% (within limit)")
        else:
            parts.append(f"✗ Opening at max flow: {opening_max:.1f}% (exceeds 90%)")

        if is_choked:
            parts.append("⚠ Flow is choked - consider larger valve or higher inlet pressure")

        if is_cavitating:
            if cavitation_index <= 1.0:
                parts.append("✗ Full cavitation expected - redesign required")
            else:
                parts.append(f"⚠ Incipient cavitation expected (σ={cavitation_index:.2f})")

        return " | ".join(parts)