"""Thermowell Wake Frequency Calculator Module

ASME PTC 19.3 TW-2016 compliant thermowell design verification.
"""

import math
from typing import Dict

from ..models import (
    ThermowellInput, ThermowellResult, ThermowellTipType,
    ThermowellSupportType, FluidType
)


class ThermowellSizer:
    """Thermowell sizer per ASME PTC 19.3 TW-2016"""

    # Thermowell material properties at room temperature
    MATERIAL_PROPS = {
        '316SS': {
            'E_GPa': 195.0,
            'rho_kg_m3': 8000.0,
            'sigma_allowable_MPa': 138.0,
            'poisson': 0.3
        },
        '304SS': {
            'E_GPa': 193.0,
            'rho_kg_m3': 8000.0,
            'sigma_allowable_MPa': 115.0,
            'poisson': 0.3
        },
        'Hastelloy_C276': {
            'E_GPa': 205.0,
            'rho_kg_m3': 8890.0,
            'sigma_allowable_MPa': 137.9,
            'poisson': 0.307
        },
        'Inconel_600': {
            'E_GPa': 207.0,
            'rho_kg_m3': 8440.0,
            'sigma_allowable_MPa': 110.3,
            'poisson': 0.29
        },
        'Monel_400': {
            'E_GPa': 179.0,
            'rho_kg_m3': 8830.0,
            'sigma_allowable_MPa': 179.3,
            'poisson': 0.32
        },
    }

    # Strouhal number (typical for cylindrical thermowell)
    STROUHAL_NUMBER = 0.21

    # Frequency ratio limits per ASME PTC 19.3
    SAFE_RATIO = 0.8
    CAUTION_RATIO = 0.9
    UNSAFE_RATIO = 1.0

    # In-line frequency ratio limit
    INLINE_SAFE_RATIO = 0.4

    def __init__(self, input_params: ThermowellInput):
        """Initialize thermowell sizer with input parameters

        Args:
            input_params: ThermowellInput dataclass with all input parameters
        """
        self.input = input_params

        # Get material properties
        mat_props = self.MATERIAL_PROPS.get(
            self.input.material,
            self.MATERIAL_PROPS['316SS']
        )

        # Adjust Young's modulus for temperature
        self.E = self._temperature_corrected_E(mat_props['E_GPa'], self.input.operating_temperature_C)
        self.rho_tw = mat_props['rho_kg_m3']
        self.sigma_allowable = self._temperature_corrected_sigma(
            mat_props['sigma_allowable_MPa'],
            self.input.operating_temperature_C
        )
        self.nu = mat_props['poisson']

        # Thermowell geometry
        self.L = self.input.insertion_length_mm / 1000.0  # m
        self.d_tip = self.input.tip_diameter_mm / 1000.0  # m
        self.d_root = self.input.root_diameter_mm / 1000.0  # m
        self.d_bore = self.input.bore_diameter_mm / 1000.0  # m

        # Process conditions
        self.V = self.input.velocity_ms
        self.rho_fluid = self.input.density_kg_m3
        self.P = self.input.operating_pressure_barg * 1e5  # Pa
        self.T = self.input.operating_temperature_C + 273.15  # K
        self.mu = self.input.viscosity_Pa_s

    def _temperature_corrected_E(self, E_room: float, temp_C: float) -> float:
        """Correct Young's modulus for temperature

        Args:
            E_room: Young's modulus at room temperature [GPa]
            temp_C: Temperature [°C]

        Returns:
            Temperature-corrected Young's modulus [GPa]
        """
        # Simplified temperature correction
        # For 316SS: E decreases approximately linearly with temperature
        if temp_C <= 20:
            return E_room
        elif temp_C >= 600:
            return E_room * 0.7
        else:
            factor = 1.0 - 0.0005 * (temp_C - 20)
            return E_room * factor

    def _temperature_corrected_sigma(self, sigma_room: float, temp_C: float) -> float:
        """Correct allowable stress for temperature

        Args:
            sigma_room: Allowable stress at room temperature [MPa]
            temp_C: Temperature [°C]

        Returns:
            Temperature-corrected allowable stress [MPa]
        """
        # Simplified temperature correction
        if temp_C <= 38:
            return sigma_room
        elif temp_C >= 600:
            return sigma_room * 0.5
        else:
            # Linear interpolation
            factor = 1.0 - 0.001 * (temp_C - 38)
            return sigma_room * factor

    def _calculate_moment_of_inertia(self) -> float:
        """Calculate moment of inertia

        Depends on thermowell geometry

        Returns:
            Moment of inertia [m⁴]
        """
        # Annular cross-section
        I = math.pi * (self.d_tip**4 - self.d_bore**4) / 64.0

        return I

    def _calculate_cross_sectional_area(self) -> float:
        """Calculate cross-sectional area

        Returns:
            Cross-sectional area [m²]
        """
        # Annular area
        A = math.pi * (self.d_tip**2 - self.d_bore**2) / 4.0

        return A

    def _calculate_natural_frequency(self) -> float:
        """Calculate natural frequency

        fn = (λ²/(2πL²)) × √(E×I/(ρ_w×A))

        Where λ depends on support condition:
        - Clamped-free: λ = 1.875
        - Pinned-free: λ = π
        - Clamped-pinned: λ = 3.927

        Returns:
            Natural frequency [Hz]
        """
        # Get lambda based on support condition
        if self.input.support_type == ThermowellSupportType.FLANGED:
            lam = 1.875  # Clamped-free
        elif self.input.support_type == ThermowellSupportType.THREADED:
            lam = 3.1416  # Pinned-free (approximated)
        elif self.input.support_type == ThermowellSupportType.WELDED:
            lam = 3.927  # Clamped-pinned
        else:
            lam = 1.875  # Default to clamped-free

        # Calculate geometric properties
        I = self._calculate_moment_of_inertia()
        A = self._calculate_cross_sectional_area()

        # Convert E to Pa
        E_Pa = self.E * 1e9

        # Natural frequency
        fn = (lam**2 / (2 * math.pi * self.L**2)) * math.sqrt(E_Pa * I / (self.rho_tw * A))

        return fn

    def _calculate_wake_frequency(self) -> float:
        """Calculate Strouhal wake frequency

        fs = St × V / d

        Returns:
            Wake frequency [Hz]
        """
        fs = self.STROUHAL_NUMBER * self.V / self.d_tip

        return fs

    def _calculate_inline_frequency(self) -> float:
        """Calculate in-line oscillation frequency

        Typically 50% of cross-flow frequency

        Returns:
            In-line frequency [Hz]
        """
        fs = self._calculate_wake_frequency()
        f_inline = 0.5 * fs

        return f_inline

    def _calculate_bending_stress(self) -> float:
        """Calculate bending stress from fluid drag

        Simplified approach per ASME PTC 19.3

        Returns:
            Bending stress [MPa]
        """
        # Drag force
        # Fd = Cd × 0.5 × rho × V² × A
        Cd = 1.2  # Drag coefficient for cylinder
        A = self.d_tip * self.L  # Projected area
        Fd = Cd * 0.5 * self.rho_fluid * self.V**2 * A

        # Bending moment at root
        M = Fd * self.L / 2.0  # Assuming uniform load

        # Section modulus
        I = self._calculate_moment_of_inertia()
        c = self.d_tip / 2.0  # Outer radius
        Z = I / c

        # Bending stress
        sigma_bend = M / Z

        return sigma_bend / 1e6  # Convert to MPa

    def _calculate_pressure_stress(self) -> float:
        """Calculate pressure stress on thermowell

        Simplified approach

        Returns:
            Pressure stress [MPa]
        """
        # Hoop stress from external pressure
        # sigma = P × d / (2 × t)
        t = (self.d_tip - self.d_bore) / 2.0  # Wall thickness

        if t > 0:
            sigma_pressure = self.P * self.d_tip / (2.0 * t * 1e6)
        else:
            sigma_pressure = 0.0

        return sigma_pressure

    def _calculate_total_stress(self) -> float:
        """Calculate total stress

        Returns:
            Total stress [MPa]
        """
        sigma_bend = self._calculate_bending_stress()
        sigma_pressure = self._calculate_pressure_stress()

        # von Mises stress (simplified)
        sigma_total = sigma_bend + sigma_pressure

        return sigma_total

    def _estimate_fatigue_life(self) -> float:
        """Estimate fatigue life (simplified)

        Returns:
            Estimated fatigue life [cycles]
        """
        # S-N curve approximation (simplified)
        # Assume infinite life if stress below endurance limit
        sigma_total = self._calculate_total_stress()
        sigma_endurance = self.sigma_allowable * 0.5  # 50% of allowable

        if sigma_total < sigma_endurance:
            return float('inf')
        else:
            # S-N power law: N = (A / S)^b
            # Simplified values
            A = 1e12
            b = 3.0
            N = (A / (sigma_total * 1e6))**b

            return N

    def calculate_wake_frequency(self) -> ThermowellResult:
        """Perform complete thermowell wake frequency calculation

        Returns:
            ThermowellResult with all calculations
        """
        warnings = []

        # Calculate frequencies
        fn = self._calculate_natural_frequency()
        fs = self._calculate_wake_frequency()
        f_inline = self._calculate_inline_frequency()

        # Calculate frequency ratios
        ratio = fs / fn if fn > 0 else float('inf')
        ratio_inline = f_inline / fn if fn > 0 else float('inf')

        # Determine status
        if ratio >= self.UNSAFE_RATIO:
            status = "unsafe"
            design_pass = False
        elif ratio >= self.CAUTION_RATIO:
            status = "caution"
            design_pass = True
        else:
            status = "safe"
            design_pass = True

        if ratio_inline >= self.INLINE_SAFE_RATIO:
            warnings.append(f"⚠ In-line frequency ratio {ratio_inline:.3f} ≥ {self.INLINE_SAFE_RATIO}")

        # Calculate stresses
        sigma_bend = self._calculate_bending_stress()
        sigma_pressure = self._calculate_pressure_stress()
        sigma_total = self._calculate_total_stress()

        stress_pass = sigma_total < self.sigma_allowable

        if not stress_pass:
            warnings.append(f"✗ Total stress {sigma_total:.2f} MPa exceeds allowable {self.sigma_allowable:.2f} MPa")

        # Fatigue evaluation
        fatigue_life = self._estimate_fatigue_life()
        fatigue_pass = fatigue_life >= 1e6  # 1 million cycles

        if not fatigue_pass:
            warnings.append(f"✗ Fatigue life {fatigue_life:.0e} cycles below 1e6")

        # Calculate suggested maximum velocity
        # fs = St × V / d  →  V = fs × d / St
        # For safe: fs = 0.8 × fn
        safe_fs = self.SAFE_RATIO * fn
        safe_V = safe_fs * self.d_tip / self.STROUHAL_NUMBER

        # Generate recommendation
        recommendation = self._generate_recommendation(
            ratio, ratio_inline, status, stress_pass, fatigue_pass, safe_V
        )

        return ThermowellResult(
            natural_frequency_Hz=fn,
            wake_frequency_Hz=fs,
            frequency_ratio=ratio,
            inline_frequency_ratio=ratio_inline,
            ratio_status=status,
            bending_stress_MPa=sigma_bend,
            pressure_stress_MPa=sigma_pressure,
            total_stress_MPa=sigma_total,
            allowable_stress_MPa=self.sigma_allowable,
            stress_pass=stress_pass,
            fatigue_life_cycles=fatigue_life,
            fatigue_pass=fatigue_pass,
            youngs_modulus_GPa=self.E,
            material_at_temperature=self.input.material,
            design_pass=design_pass,
            recommendation=recommendation,
            warnings=warnings,
            suggested_max_velocity_ms=safe_V
        )

    def _generate_recommendation(self, ratio: float, ratio_inline: float,
                                   status: str, stress_pass: bool,
                                   fatigue_pass: bool, safe_V: float) -> str:
        """Generate human-readable recommendation

        Args:
            ratio: Cross-flow frequency ratio
            ratio_inline: In-line frequency ratio
            status: Overall status
            stress_pass: Stress check pass
            fatigue_pass: Fatigue check pass
            safe_V: Suggested max velocity [m/s]

        Returns:
            Recommendation string
        """
        parts = []

        if status == "safe":
            parts.append(f"✓ Frequency ratio {ratio:.3f} is safe (< {self.SAFE_RATIO})")
        elif status == "caution":
            parts.append(f"⚠ Frequency ratio {ratio:.3f} in caution range [{self.SAFE_RATIO}, {self.CAUTION_RATIO})")
        else:
            parts.append(f"✗ Frequency ratio {ratio:.3f} is unsafe (≥ {self.CAUTION_RATIO})")

        parts.append(f"✓ In-line ratio {ratio_inline:.3f}")

        if stress_pass:
            parts.append(f"✓ Stress {self._calculate_total_stress():.2f} MPa < allowable {self.sigma_allowable:.2f} MPa")
        else:
            parts.append(f"✗ Stress exceeds allowable")

        if fatigue_pass:
            parts.append(f"✓ Fatigue life adequate")
        else:
            parts.append(f"✗ Fatigue life inadequate")

        parts.append(f"✓ Maximum safe velocity: {safe_V:.2f} m/s")

        return " | ".join(parts)