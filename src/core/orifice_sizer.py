"""Orifice Plate Sizer Module

ISO 5167-2 compliant orifice plate sizing calculations.
Implements Reader-Harris/Gallagher discharge coefficient equation.
"""

import math
import numpy as np
from typing import Tuple, Optional, Dict, List
from dataclasses import dataclass, field

from ..models import (
    OrificeInput, OrificeResult, TapType, FluidType
)
from ..utils.validators import Validators


class OrificeSizer:
    """Orifice plate sizer per ISO 5167-2:2003"""

    # Tap type distance ratios (L1 = l1/D, L2' = l2'/D)
    TAP_CONFIG = {
        TapType.CORNER: {'L1': 0.0, 'L2_prime': 0.0},
        TapType.FLANGE: {'L1': 25.4, 'L2_prime': 25.4},  # 1 inch = 25.4 mm
        TapType.D_D2: {'L1': 1.0, 'L2_prime': 0.47},  # D and D/2 taps
    }

    # Straight run requirements (ISO 5167-2 Table 3)
    # Distances in pipe diameters D
    STRAIGHT_RUN = {
        'single_elbow': [10, 10, 14, 18, 26, 32, 36, 44],
        'two_elbows_same_plane': [14, 16, 18, 22, 32, 36, 44, 54],
        'two_elbows_different_plane': [34, 34, 36, 40, 48, 54, 62, 70],
        'reducer_concentric': [5, 6, 8, 10, 14, 16, 20, 24],
        'expander_concentric': [16, 18, 20, 24, 30, 34, 40, 48],
        'globe_valve': [18, 20, 22, 26, 34, 40, 48, 56],
        'gate_valve': [12, 14, 16, 20, 28, 32, 38, 44],
    }

    # Downstream straight run (same for all fittings)
    STRAIGHT_RUN_DOWNSTREAM = [4, 5, 6, 7, 8, 9, 10, 12]

    # Beta ratio indices for interpolation
    BETA_INDICES = [0.20, 0.30, 0.40, 0.50, 0.60, 0.65, 0.70, 0.75]

    def __init__(self, input_params: OrificeInput):
        """Initialize orifice sizer with input parameters

        Args:
            input_params: OrificeInput dataclass with all input parameters
        """
        self.input = input_params
        self.validator = Validators()

        # Convert inputs to SI units if needed
        self.D = self.input.pipe_id_mm / 1000.0  # Convert mm to m for some calculations
        self.D_mm = self.input.pipe_id_mm  # Keep in mm for ISO 5167-2 equations

        # Convert pressure to Pa
        self.P1 = self.input.operating_pressure_barg * 1e5  # bar to Pa

        # Temperature to K
        self.T = self.input.operating_temperature_C + 273.15

        # Density in kg/m³
        self.rho = self.input.density_kg_m3

        # Viscosity in Pa·s
        self.mu = self.input.viscosity_Pa_s

        # Isentropic exponent
        self.kappa = self.input.isentropic_exponent

        # Tap configuration
        self.tap_config = self.TAP_CONFIG.get(self.input.tap_type, self.TAP_CONFIG[TapType.FLANGE])

        # Flow rates (convert to kg/s for calculations)
        self.q_normal = self._convert_flow_to_kg_s(self.input.normal_flow, self.input.flow_unit)
        self.q_max = self._convert_flow_to_kg_s(self.input.max_flow, self.input.flow_unit)
        self.q_min = self._convert_flow_to_kg_s(self.input.min_flow, self.input.flow_unit)

        # DP transmitter range (convert to Pa)
        self.dp_range = self.input.dp_transmitter_range_mbar * 100.0  # mbar to Pa

    def _convert_flow_to_kg_s(self, flow: float, unit: str) -> float:
        """Convert flow to kg/s

        Args:
            flow: Flow value
            unit: Flow unit

        Returns:
            Flow in kg/s
        """
        if unit == 'kg/h':
            return flow / 3600.0
        elif unit == 'kg/s':
            return flow
        elif unit == 'm³/h':
            # Need density
            return (flow / 3600.0) * self.rho
        elif unit == 'GPM':
            # 1 GPM = 3.78541 L/min = 0.00378541 m³/min
            return (flow * 0.00378541 / 60.0) * self.rho
        elif unit == 'BPD':
            # 1 BPD = 0.158987 m³/day
            return (flow * 0.158987 / 86400.0) * self.rho
        else:
            raise ValueError(f"Unknown flow unit: {unit}")

    def _discharge_coefficient(self, beta: float, Re_D: float) -> float:
        """Calculate discharge coefficient using Reader-Harris/Gallagher equation

        ISO 5167-2:2003 Equation 1

        C = C_∞ + correction terms

        Args:
            beta: Diameter ratio (d/D)
            Re_D: Reynolds number based on pipe diameter

        Returns:
            Discharge coefficient C (typically 0.59-0.62)
        """
        # C_inf: infinite Reynolds number asymptotic value
        C_inf = 0.5961 + 0.0261 * beta**2 - 0.216 * beta**8

        # A term
        A = (19000 * beta / Re_D) ** 0.8

        # Tap-dependent terms
        L1 = self.tap_config['L1'] / self.D_mm  # Convert to ratio
        L2_prime = self.tap_config['L2_prime'] / self.D_mm

        # First correction term (Reynolds number)
        term1 = 0.000521 * (10**6 * beta / Re_D)**0.7

        # Second correction term (tap-dependent)
        term2 = (0.0188 + 0.0006 * A) * beta**3.5 * (10**6 / Re_D)**0.3

        # Third correction term (tap geometry)
        exp_term = math.exp(-10 * L1) if L1 > 0 else 0
        M2_prime = 2 * L2_prime / (1 - beta)
        term3 = (0.043 + 0.080 * exp_term - 0.123 * math.exp(-7 * L1)) * \
                 (1 - 0.11 * A) * beta**4 / (1 - beta**4)

        # Fourth correction term (wall thickness)
        term4 = -0.031 * (M2_prime - 0.8 * M2_prime**1.1) * beta**1.3

        C = C_inf + term1 + term2 + term3 + term4

        return C

    def _expansibility_factor(self, beta: float, dp: float) -> float:
        """Calculate expansibility factor for gases

        ISO 5167-2:2003 Equation 8

        ε = 1 - (0.351 + 0.256β⁴ + 0.93β⁸) × [1 - (1 - Δp/P1)^(1/κ)] × (Δp/P1)^0.7

        For incompressible fluids (liquids): ε = 1.0

        Args:
            beta: Diameter ratio
            dp: Differential pressure [Pa]

        Returns:
            Expansibility factor ε (dimensionless)
        """
        if self.input.fluid_type == FluidType.LIQUID:
            return 1.0

        # Check if pressure ratio is within valid range
        pressure_ratio = dp / self.P1
        if pressure_ratio >= 0.25:
            # Warning will be added in results
            pass

        # Calculate expansibility factor
        beta_term = 0.351 + 0.256 * beta**4 + 0.93 * beta**8
        pressure_term = 1 - (1 - pressure_ratio)**(1 / self.kappa)
        ratio_term = pressure_ratio**0.7

        epsilon = 1 - beta_term * pressure_term * ratio_term

        return epsilon

    def _permanent_pressure_loss(self, beta: float, dp: float) -> Tuple[float, float]:
        """Calculate permanent pressure loss

        ISO 5167-2:2003 Equation 12

        Δω = ((1 - β²^1.5) / (1 + β²^1.5)) × Δp

        Args:
            beta: Diameter ratio
            dp: Differential pressure [Pa]

        Returns:
            Tuple of (permanent_pressure_loss_Pa, permanent_pressure_loss_pct)
        """
        loss_ratio = (1 - (beta**2)**1.5) / (1 + (beta**2)**1.5)
        permanent_loss = loss_ratio * dp
        permanent_loss_pct = loss_ratio * 100.0

        return permanent_loss, permanent_loss_pct

    def _reynolds_number(self, mass_flow: float) -> float:
        """Calculate Reynolds number

        Re_D = (4 × q_m) / (π × D × μ)

        Args:
            mass_flow: Mass flow rate [kg/s]

        Returns:
            Reynolds number (dimensionless)
        """
        area = math.pi * (self.D_mm / 1000.0)**2 / 4.0  # Pipe cross-sectional area [m²]
        velocity = mass_flow / (self.rho * area)  # Velocity [m/s]
        Re = (self.rho * velocity * (self.D_mm / 1000.0)) / self.mu

        return Re

    def _calculate_dp_from_flow(self, beta: float, C: float, epsilon: float,
                                 mass_flow: float) -> float:
        """Calculate differential pressure from mass flow

        Rearranged ISO 5167-2 equation:

        Δp = (q_m / (C × ε × (π/4) × d²))² × (2 × ρ)

        Args:
            beta: Diameter ratio
            C: Discharge coefficient
            epsilon: Expansibility factor
            mass_flow: Mass flow rate [kg/s]

        Returns:
            Differential pressure [Pa]
        """
        d = beta * (self.D_mm / 1000.0)  # Orifice bore diameter [m]
        area = math.pi * d**2 / 4.0  # Orifice area [m²]

        # For gases, need to iterate because epsilon depends on dp
        # For liquids, epsilon = 1.0
        if self.input.fluid_type == FluidType.LIQUID:
            dp = (mass_flow / (C * epsilon * area))**2 * self.rho / 2.0
            return dp
        else:
            # Iterative calculation for gases
            dp_guess = (mass_flow / (C * 1.0 * area))**2 * self.rho / 2.0  # Initial guess with epsilon=1

            for _ in range(5):  # Typically converges in 3-5 iterations
                epsilon = self._expansibility_factor(beta, dp_guess)
                dp_new = (mass_flow / (C * epsilon * area))**2 * self.rho / 2.0

                if abs(dp_new - dp_guess) / dp_guess < 1e-6:
                    break

                dp_guess = dp_new

            return dp_guess

    def _straight_run_requirements(self, beta: float) -> Tuple[float, float, float, float]:
        """Get straight run requirements

        Args:
            beta: Diameter ratio

        Returns:
            Tuple of (upstream_D, upstream_mm, downstream_D, downstream_mm)
        """
        fitting = self.input.upstream_fitting.lower().replace(' ', '_')

        if fitting not in self.STRAIGHT_RUN:
            fitting = 'single_elbow'  # Default

        # Interpolate for given beta
        upstream_D = self._interpolate_straight_run(beta, self.STRAIGHT_RUN[fitting])

        # Downstream is same for all fittings
        downstream_D = self._interpolate_straight_run(beta, self.STRAIGHT_RUN_DOWNSTREAM)

        # Convert to mm
        upstream_mm = upstream_D * self.D_mm
        downstream_mm = downstream_D * self.D_mm

        return upstream_D, upstream_mm, downstream_D, downstream_mm

    def _interpolate_straight_run(self, beta: float, values: List[float]) -> float:
        """Interpolate straight run requirement for given beta

        Args:
            beta: Diameter ratio
            values: List of straight run values at beta indices

        Returns:
            Interpolated straight run requirement
        """
        if beta <= self.BETA_INDICES[0]:
            return values[0]
        elif beta >= self.BETA_INDICES[-1]:
            return values[-1]

        # Find interval
        for i in range(len(self.BETA_INDICES) - 1):
            if self.BETA_INDICES[i] <= beta <= self.BETA_INDICES[i + 1]:
                # Linear interpolation
                x0, x1 = self.BETA_INDICES[i], self.BETA_INDICES[i + 1]
                y0, y1 = values[i], values[i + 1]
                return y0 + (y1 - y0) * (beta - x0) / (x1 - x0)

        return values[0]

    def _uncertainty_analysis(self, beta: float, C: float, dp: float,
                               Re_D: float) -> Tuple[float, Dict[str, float]]:
        """Calculate total uncertainty on mass flow

        ISO 5167-2:2003 Section 5.1

        Args:
            beta: Diameter ratio
            C: Discharge coefficient
            dp: Differential pressure [Pa]
            Re_D: Reynolds number

        Returns:
            Tuple of (total_uncertainty_pct, uncertainty_breakdown)
        """
        # Discharge coefficient uncertainty (base value from ISO 5167-2)
        if self.D_mm >= 71.12:
            u_C = 0.5  # 0.5%
        else:
            u_C = 0.75  # Higher uncertainty for smaller pipes

        # Expansibility factor uncertainty
        if self.input.fluid_type == FluidType.LIQUID:
            u_epsilon = 0.0
        else:
            pressure_ratio = dp / self.P1
            u_epsilon = 3.5 * pressure_ratio / self.kappa * 100.0

        # Orifice bore uncertainty (typical ±0.05%)
        u_d = 0.05

        # Pipe ID uncertainty (typical ±0.3%)
        u_D = 0.3

        # DP transmitter uncertainty (assumed 0.075%)
        u_dp = 0.075

        # Density uncertainty (assumed 0.1% for CoolProp)
        u_rho = 0.1

        # Combined uncertainty (simplified ISO 5167-2 formula)
        beta_term = (2 * beta**4 / (1 - beta**4))**2

        # Combine using root-sum-square
        total = math.sqrt(
            u_C**2 + u_epsilon**2 +
            beta_term * (u_d**2 + u_D**2) +
            (0.5 * u_dp)**2 + (0.5 * u_rho)**2
        )

        breakdown = {
            'discharge_coefficient': u_C,
            'expansibility': u_epsilon,
            'orifice_bore': u_d * beta_term**0.5,
            'pipe_id': u_D * beta_term**0.5,
            'dp_transmitter': 0.5 * u_dp,
            'density': 0.5 * u_rho
        }

        return total, breakdown

    def optimize_beta(self) -> OrificeResult:
        """Optimize beta ratio

        Iterate β from 0.10 to 0.75 to find optimal:
        - β in preferred range [0.20, 0.60]
        - dp_at_max_flow within 70-90% of transmitter full scale
        - Turndown ≥ 3:1

        Returns:
            OrificeResult with optimal beta and all calculations
        """
        best_result = None
        best_score = -float('inf')

        warnings = []

        # Iterate through beta values
        beta_values = np.linspace(0.10, 0.75, 651)  # Step of 0.001

        for beta in beta_values:
            try:
                # Calculate discharge coefficient (initial guess)
                C_guess = 0.61
                Re_guess = self._reynolds_number(self.q_max)

                # Iterate to get accurate C
                for _ in range(10):
                    C_new = self._discharge_coefficient(beta, Re_guess)
                    if abs(C_new - C_guess) < 1e-6:
                        C_guess = C_new
                        break
                    C_guess = C_new

                # Calculate expansibility factor
                dp_guess = (self.q_max / (C_guess * 1.0 * (math.pi * beta * (self.D_mm / 1000.0))**2 / 4.0))**2 * self.rho / 2.0
                epsilon = self._expansibility_factor(beta, dp_guess)

                # Calculate dp at max flow
                dp_max = self._calculate_dp_from_flow(beta, C_guess, epsilon, self.q_max)

                # Check dp range
                dp_pct = dp_max / self.dp_range

                # Calculate turndown
                dp_min = self._calculate_dp_from_flow(beta, C_guess, epsilon, self.q_min)
                turndown = dp_max / dp_min if dp_min > 0 else float('inf')

                # Score calculation (higher is better)
                score = 0

                # Beta in preferred range
                if 0.20 <= beta <= 0.60:
                    score += 100
                elif 0.10 <= beta <= 0.75:
                    score += 50

                # DP in optimal range (70-90%)
                if 0.70 <= dp_pct <= 0.90:
                    score += 80
                elif 0.50 <= dp_pct <= 1.00:
                    score += 40
                elif dp_pct <= 1.00:
                    score += 10

                # Turndown >= 3:1
                if turndown >= 3.0:
                    score += 50
                elif turndown >= 2.0:
                    score += 20

                # Add all results
                if best_result is None or score > best_score:
                    # Calculate full results for this beta
                    result = self._calculate_full_result(beta, C_guess, epsilon, dp_max, dp_min)
                    best_result = result
                    best_score = score

            except Exception:
                continue

        # Add warnings
        if best_result.beta < 0.20 or best_result.beta > 0.60:
            warnings.append(f"Beta {best_result.beta:.3f} outside preferred range [0.20, 0.60]")

        dp_max_pct = best_result.dp_at_max_flow_mbar / self.input.dp_transmitter_range_mbar
        if dp_max_pct > 0.90:
            warnings.append(f"DP at max flow is {dp_max_pct*100:.1f}% of range (exceeds 90%)")
        elif dp_max_pct < 0.50:
            warnings.append(f"DP at max flow is only {dp_max_pct*100:.1f}% of range (may affect accuracy)")

        if best_result.turndown_ratio < 3.0:
            warnings.append(f"Turndown ratio {best_result.turndown_ratio:.2f} below minimum 3:1")

        # Reynolds check
        if best_result.reynolds_at_min < 10000:
            warnings.append(f"Reynolds at min flow ({best_result.reynolds_at_min:.0f}) below 10,000")
        elif best_result.reynolds_at_min < 170000 * best_result.beta**2 * (self.D_mm / 1000.0):
            warnings.append("Reynolds number may be low for accurate measurement")

        best_result.warnings = warnings
        best_result.recommendation = self._generate_recommendation(best_result)

        return best_result

    def _calculate_full_result(self, beta: float, C: float, epsilon: float,
                                dp_max: float, dp_min: float) -> OrificeResult:
        """Calculate full result for given beta

        Args:
            beta: Diameter ratio
            C: Discharge coefficient
            epsilon: Expansibility factor
            dp_max: DP at max flow [Pa]
            dp_min: DP at min flow [Pa]

        Returns:
            OrificeResult with all calculations
        """
        # Orifice bore
        orifice_bore = beta * self.D_mm

        # DP at normal flow
        dp_normal = self._calculate_dp_from_flow(beta, C, epsilon, self.q_normal)

        # Reynolds numbers
        Re_max = self._reynolds_number(self.q_max)
        Re_normal = self._reynolds_number(self.q_normal)
        Re_min = self._reynolds_number(self.q_min)

        # Permanent pressure loss
        permanent_loss, permanent_loss_pct = self._permanent_pressure_loss(beta, dp_max)

        # Turndown
        turndown = self.q_max / self.q_min if self.q_min > 0 else float('inf')

        # Straight run requirements
        upstream_D, upstream_mm, downstream_D, downstream_mm = self._straight_run_requirements(beta)

        # Uncertainty analysis
        total_uncertainty, uncertainty_breakdown = self._uncertainty_analysis(beta, C, dp_max, Re_max)

        # Status checks
        if 0.20 <= beta <= 0.60:
            beta_status = "optimal"
        elif 0.10 <= beta <= 0.75:
            beta_status = "acceptable"
        else:
            beta_status = "out_of_range"

        dp_max_mbar = dp_max / 100.0
        dp_pct = dp_max_mbar / self.input.dp_transmitter_range_mbar
        if dp_pct <= 1.0:
            dp_status = "ok"
        else:
            dp_status = "exceeds_range"

        if Re_min >= 10000:
            reynolds_status = "ok"
        else:
            reynolds_status = "below_minimum"

        return OrificeResult(
            beta=beta,
            orifice_bore_mm=orifice_bore,
            discharge_coefficient=C,
            expansibility_factor=epsilon,
            dp_at_max_flow_mbar=dp_max / 100.0,  # Convert Pa to mbar
            dp_at_normal_flow_mbar=dp_normal / 100.0,
            dp_at_min_flow_mbar=dp_min / 100.0,
            reynolds_at_max=Re_max,
            reynolds_at_normal=Re_normal,
            reynolds_at_min=Re_min,
            turndown_ratio=turndown,
            permanent_pressure_loss_pct=permanent_loss_pct,
            permanent_pressure_loss_bar=permanent_loss / 1e5,  # Convert Pa to bar
            straight_run_upstream_D=upstream_D,
            straight_run_upstream_mm=upstream_mm,
            straight_run_downstream_D=downstream_D,
            straight_run_downstream_mm=downstream_mm,
            total_uncertainty_pct=total_uncertainty,
            uncertainty_breakdown=uncertainty_breakdown,
            beta_status=beta_status,
            dp_status=dp_status,
            reynolds_status=reynolds_status,
            recommendation="",
            warnings=[]
        )

    def _generate_recommendation(self, result: OrificeResult) -> str:
        """Generate human-readable recommendation

        Args:
            result: OrificeResult object

        Returns:
            Recommendation string
        """
        parts = []

        if result.beta_status == "optimal":
            parts.append(f"✓ Beta ratio {result.beta:.3f} is in optimal range")
        elif result.beta_status == "acceptable":
            parts.append(f"✓ Beta ratio {result.beta:.3f} is acceptable but outside optimal range")
        else:
            parts.append(f"✗ Beta ratio {result.beta:.3f} is out of range")

        parts.append(f"✓ Orifice bore: {result.orifice_bore_mm:.2f} mm")
        parts.append(f"✓ DP at max flow: {result.dp_at_max_flow_mbar:.1f} mbar")

        dp_pct = result.dp_at_max_flow_mbar / self.input.dp_transmitter_range_mbar
        if 0.70 <= dp_pct <= 0.90:
            parts.append(f"✓ DP utilization {dp_pct*100:.0f}% is optimal")
        elif dp_pct <= 1.0:
            parts.append(f"⚠ DP utilization {dp_pct*100:.0f}% - consider different transmitter range")

        if result.turndown_ratio >= 3.0:
            parts.append(f"✓ Turndown {result.turndown_ratio:.2f}:1 meets minimum requirement")
        else:
            parts.append(f"✗ Turndown {result.turndown_ratio:.2f}:1 below minimum 3:1")

        parts.append(f"✓ Permanent pressure loss: {result.permanent_pressure_loss_pct:.1f}% of ΔP")

        return " | ".join(parts)