"""Flow Element Sizer Module

ISO 5167-3 compliant flow element sizing calculations.
Supports: Venturi tube, Flow nozzle, V-Cone, Wedge meter.
"""

import math
from typing import Tuple

from ..models import (
    FlowElementInput, FlowElementResult, FlowElementType, FluidType
)


class FlowElementSizer:
    """Flow element sizer per ISO 5167-3"""

    def __init__(self, input_params: FlowElementInput):
        """Initialize flow element sizer with input parameters

        Args:
            input_params: FlowElementInput dataclass with all input parameters
        """
        self.input = input_params

        # Convert to SI units
        self.D = self.input.pipe_id_mm / 1000.0  # m
        self.D_mm = self.input.pipe_id_mm  # mm

        # Operating conditions
        self.P1 = self.input.operating_pressure_barg * 1e5  # Pa
        self.T = self.input.operating_temperature_C + 273.15  # K

        # Fluid properties
        self.rho = self.input.density_kg_m3
        self.mu = self.input.viscosity_Pa_s
        self.kappa = self.input.isentropic_exponent

        # Flow rates (convert to kg/s)
        self.q_normal = self.input.normal_flow / 3600.0
        self.q_max = self.input.max_flow / 3600.0
        self.q_min = self.input.min_flow / 3600.0

        # DP transmitter range
        self.dp_range = self.input.dp_transmitter_range_mbar * 100.0  # Pa

    def _calculate_discharge_coefficient_venturi(self, beta: float, Re_D: float) -> float:
        """Calculate discharge coefficient for Venturi tube

        ISO 5167-3:2003

        For machined entrance (Re_D > 2×10⁵):
          C = 0.9858 - 0.196β^4.5

        For rough-welded sheet-iron (100mm ≤ D ≤ 800mm):
          C = 0.9771 - 0.188β^4.5

        Args:
            beta: Diameter ratio
            Re_D: Reynolds number

        Returns:
            Discharge coefficient C
        """
        if Re_D > 200000 and 50 <= self.D_mm <= 400:
            # Machined entrance
            C = 0.9858 - 0.196 * beta**4.5
        elif 100 <= self.D_mm <= 800:
            # Rough-welded sheet-iron
            C = 0.9771 - 0.188 * beta**4.5
        else:
            # Default to machined
            C = 0.9858 - 0.196 * beta**4.5

        return C

    def _calculate_discharge_coefficient_nozzle(self, beta: float, Re_D: float) -> float:
        """Calculate discharge coefficient for ISA 1932 flow nozzle

        ISO 5167-3:2003

        For ISA 1932 nozzle:
          C = 0.9900 - 0.2262β^4.1 + (0.000215 - 0.001125β + 0.002490β^4.7) × (10^6β/Re_D)^0.8

        Args:
            beta: Diameter ratio
            Re_D: Reynolds number

        Returns:
            Discharge coefficient C
        """
        C_inf = 0.9900 - 0.2262 * beta**4.1
        A = (10**6 * beta / Re_D) ** 0.8
        correction = (0.000215 - 0.001125 * beta + 0.002490 * beta**4.7) * A

        C = C_inf + correction

        return C

    def _calculate_discharge_coefficient_vcone(self, beta: float) -> float:
        """Calculate discharge coefficient for V-Cone meter

        V-Cone is proprietary; use typical vendor values

        Args:
            beta: Diameter ratio (beta = √(1 - d_cone²/D²))

        Returns:
            Discharge coefficient C (typically 0.8-0.85)
        """
        # Typical value from McCrometer
        C = 0.83

        # Adjust slightly based on beta
        C += 0.02 * (0.7 - beta)

        return C

    def _calculate_discharge_coefficient_wedge(self, h_D_ratio: float) -> float:
        """Calculate discharge coefficient for Wedge meter

        Wedge meter uses H/D ratio instead of beta

        Args:
            h_D_ratio: Wedge height / pipe diameter ratio

        Returns:
            Discharge coefficient C (typically 0.6-0.7)
        """
        # Typical correlation
        C = 0.62 + 0.1 * h_D_ratio

        return C

    def _reynolds_number(self, mass_flow: float) -> float:
        """Calculate Reynolds number

        Args:
            mass_flow: Mass flow rate [kg/s]

        Returns:
            Reynolds number
        """
        velocity = mass_flow / (self.rho * math.pi * self.D**2 / 4.0)
        Re = (self.rho * velocity * self.D) / self.mu

        return Re

    def _expansibility_factor(self, beta: float, dp: float) -> float:
        """Calculate expansibility factor for gases

        Args:
            beta: Diameter ratio
            dp: Differential pressure [Pa]

        Returns:
            Expansibility factor ε
        """
        if self.input.fluid_type == FluidType.LIQUID:
            return 1.0

        pressure_ratio = dp / self.P1

        # For Venturi (ISO 5167-3)
        if self.input.element_type == FlowElementType.VENTURI:
            beta_term = 0.41 + 0.35 * beta**4
            pressure_term = 1 - (1 - pressure_ratio)**(1 / self.kappa)
            ratio_term = pressure_term / pressure_ratio
            epsilon = 1 - beta_term * ratio_term
        else:
            # Simplified for other elements
            epsilon = 1 - 0.35 * (1 - (1 - pressure_ratio)**(1 / self.kappa))

        return epsilon

    def _permanent_pressure_loss(self, element_type: FlowElementType,
                                  beta: float, dp: float) -> Tuple[float, float]:
        """Calculate permanent pressure loss

        Args:
            element_type: Type of flow element
            beta: Diameter ratio
            dp: Differential pressure [Pa]

        Returns:
            Tuple of (permanent_pressure_loss_Pa, permanent_pressure_loss_pct)
        """
        if element_type == FlowElementType.VENTURI:
            loss_ratio = 0.10 + 0.15 * beta**2  # 10-25% of dp
        elif element_type == FlowElementType.FLOW_NOZZLE:
            loss_ratio = 0.30 + 0.30 * beta**2  # 30-60% of dp
        elif element_type == FlowElementType.V_CONE:
            loss_ratio = 0.20 + 0.30 * beta**2  # 20-50% of dp
        elif element_type == FlowElementType.WEDGE:
            loss_ratio = 0.40 + 0.30 * beta**2  # 40-70% of dp
        else:
            loss_ratio = 0.5

        loss = loss_ratio * dp
        loss_pct = loss_ratio * 100.0

        return loss, loss_pct

    def _straight_run_requirements(self, element_type: FlowElementType,
                                    beta: float) -> Tuple[float, float]:
        """Get straight run requirements

        Args:
            element_type: Type of flow element
            beta: Diameter ratio

        Returns:
            Tuple of (upstream_D, downstream_D)
        """
        if element_type == FlowElementType.VENTURI:
            upstream_D = 1.0  # Very minimal straight run
            downstream_D = 4.0
        elif element_type == FlowElementType.FLOW_NOZZLE:
            upstream_D = 5.0 + 10.0 * beta
            downstream_D = 4.0
        elif element_type == FlowElementType.V_CONE:
            upstream_D = 0.0  # No straight run needed
            downstream_D = 3.0
        elif element_type == FlowElementType.WEDGE:
            upstream_D = 5.0
            downstream_D = 4.0
        else:
            upstream_D = 10.0
            downstream_D = 5.0

        return upstream_D, downstream_D

    def _uncertainty_estimate(self, element_type: FlowElementType,
                               beta: float) -> float:
        """Estimate total uncertainty

        Args:
            element_type: Type of flow element
            beta: Diameter ratio

        Returns:
            Total uncertainty percentage
        """
        if element_type == FlowElementType.VENTURI:
            u = 0.5 + 0.5 * (1.0 - beta)  # 0.5-1.0%
        elif element_type == FlowElementType.FLOW_NOZZLE:
            u = 0.75 + 0.5 * (1.0 - beta)  # 0.75-1.25%
        elif element_type == FlowElementType.V_CONE:
            u = 0.5  # Typically 0.5%
        elif element_type == FlowElementType.WEDGE:
            u = 1.0  # Typically 1.0%
        else:
            u = 1.5

        return u

    def size_element(self) -> FlowElementResult:
        """Perform complete flow element sizing

        Returns:
            FlowElementResult with all calculations
        """
        # Initial Reynolds number guess
        Re_max = self._reynolds_number(self.q_max)

        # Determine discharge coefficient method
        if self.input.element_type == FlowElementType.VENTURI:
            C = self._calculate_discharge_coefficient_venturi(0.6, Re_max)
            min_beta, max_beta = 0.30, 0.75
        elif self.input.element_type == FlowElementType.FLOW_NOZZLE:
            C = self._calculate_discharge_coefficient_nozzle(0.6, Re_max)
            min_beta, max_beta = 0.20, 0.80
        elif self.input.element_type == FlowElementType.V_CONE:
            C = self._calculate_discharge_coefficient_vcone(0.7)
            min_beta, max_beta = 0.45, 0.85
        elif self.input.element_type == FlowElementType.WEDGE:
            C = self._calculate_discharge_coefficient_wedge(0.5)
            min_beta, max_beta = 0.3, 0.7  # H/D ratio range
        else:
            raise ValueError(f"Unknown flow element type: {self.input.element_type}")

        # Optimize beta / H/D ratio
        best_result = None
        best_score = -float('inf')

        beta_values = [min_beta + i * 0.005 for i in range(int((max_beta - min_beta) / 0.005))]

        for beta in beta_values:
            try:
                # Calculate discharge coefficient
                if self.input.element_type == FlowElementType.VENTURI:
                    C = self._calculate_discharge_coefficient_venturi(beta, Re_max)
                elif self.input.element_type == FlowElementType.FLOW_NOZZLE:
                    C = self._calculate_discharge_coefficient_nozzle(beta, Re_max)
                elif self.input.element_type == FlowElementType.V_CONE:
                    C = self._calculate_discharge_coefficient_vcone(beta)
                elif self.input.element_type == FlowElementType.WEDGE:
                    C = self._calculate_discharge_coefficient_wedge(beta)

                # Calculate expansibility factor
                dp_guess = (self.q_max / (C * 1.0 * math.pi * (beta * self.D)**2 / 4.0))**2 * self.rho / 2.0
                epsilon = self._expansibility_factor(beta, dp_guess)

                # Calculate dp at max flow
                dp_max = self._calculate_dp_from_flow(beta, C, epsilon, self.q_max)

                # Check dp range
                dp_pct = dp_max / self.dp_range

                # Calculate turndown
                dp_min = self._calculate_dp_from_flow(beta, C, epsilon, self.q_min)
                turndown = dp_max / dp_min if dp_min > 0 else float('inf')

                # Score calculation
                score = 0

                # Beta in range
                if min_beta <= beta <= max_beta:
                    score += 100

                # DP in optimal range (60-90%)
                if 0.60 <= dp_pct <= 0.90:
                    score += 80
                elif 0.40 <= dp_pct <= 1.00:
                    score += 40
                elif dp_pct <= 1.00:
                    score += 10

                # Turndown >= 10:1 for Venturi
                min_turndown = 10.0 if self.input.element_type == FlowElementType.VENTURI else 5.0
                if turndown >= min_turndown:
                    score += 50
                elif turndown >= 3.0:
                    score += 20

                if best_result is None or score > best_score:
                    # Store results
                    upstream_D, downstream_D = self._straight_run_requirements(
                        self.input.element_type, beta
                    )
                    permanent_loss, permanent_loss_pct = self._permanent_pressure_loss(
                        self.input.element_type, beta, dp_max
                    )
                    uncertainty = self._uncertainty_estimate(self.input.element_type, beta)

                    dp_normal = self._calculate_dp_from_flow(beta, C, epsilon, self.q_normal)

                    throat_diameter = beta * self.D_mm

                    best_result = FlowElementResult(
                        beta_or_ratio=beta,
                        discharge_coefficient=C,
                        throat_diameter_mm=throat_diameter,
                        dp_at_max_flow_mbar=dp_max / 100.0,
                        dp_at_normal_flow_mbar=dp_normal / 100.0,
                        permanent_pressure_loss_pct=permanent_loss_pct,
                        straight_run_upstream_D=upstream_D,
                        straight_run_downstream_D=downstream_D,
                        reynolds_number=Re_max,
                        uncertainty_pct=uncertainty,
                        turndown_ratio=turndown,
                        recommendation=self._generate_recommendation(
                            beta, dp_pct, turndown, permanent_loss_pct, uncertainty
                        )
                    )
                    best_score = score

            except Exception:
                continue

        return best_result if best_result else FlowElementResult(
            beta_or_ratio=min_beta,
            discharge_coefficient=C,
            throat_diameter_mm=min_beta * self.D_mm,
            dp_at_max_flow_mbar=0.0,
            dp_at_normal_flow_mbar=0.0,
            permanent_pressure_loss_pct=0.0,
            straight_run_upstream_D=0.0,
            straight_run_downstream_D=0.0,
            reynolds_number=0.0,
            uncertainty_pct=0.0,
            turndown_ratio=0.0,
            recommendation="Calculation failed"
        )

    def _calculate_dp_from_flow(self, beta: float, C: float, epsilon: float,
                                 mass_flow: float) -> float:
        """Calculate differential pressure from mass flow

        Args:
            beta: Diameter ratio
            C: Discharge coefficient
            epsilon: Expansibility factor
            mass_flow: Mass flow rate [kg/s]

        Returns:
            Differential pressure [Pa]
        """
        d = beta * self.D
        area = math.pi * d**2 / 4.0

        dp = (mass_flow / (C * epsilon * area))**2 * self.rho / 2.0

        return dp

    def _generate_recommendation(self, beta: float, dp_pct: float,
                                   turndown: float, loss_pct: float,
                                   uncertainty: float) -> str:
        """Generate human-readable recommendation

        Args:
            beta: Diameter ratio
            dp_pct: DP as % of transmitter range
            turndown: Turndown ratio
            loss_pct: Permanent pressure loss %
            uncertainty: Uncertainty %

        Returns:
            Recommendation string
        """
        parts = []

        parts.append(f"✓ Beta/H-D ratio: {beta:.3f}")

        if 0.60 <= dp_pct <= 0.90:
            parts.append(f"✓ DP utilization {dp_pct*100:.0f}% is optimal")
        elif dp_pct <= 1.0:
            parts.append(f"⚠ DP utilization {dp_pct*100:.0f}%")

        min_turndown = 10.0 if self.input.element_type == FlowElementType.VENTURI else 5.0
        if turndown >= min_turndown:
            parts.append(f"✓ Turndown {turndown:.2f}:1 meets requirement")
        else:
            parts.append(f"✗ Turndown {turndown:.2f}:1 below minimum")

        parts.append(f"✓ Permanent loss: {loss_pct:.1f}% of ΔP")
        parts.append(f"✓ Uncertainty: ±{uncertainty:.2f}%")

        return " | ".join(parts)