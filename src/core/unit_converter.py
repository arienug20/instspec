"""Unit Converter Module for InstSpec"""

from typing import Tuple, Union


class UnitConverter:
    """Unit conversion utilities for engineering calculations"""

    # Pressure units (all conversions TO and FROM bar)
    PRESSURE_UNITS = {
        'Pa': 1e-5,      # 1 bar = 100000 Pa
        'kPa': 0.01,     # 1 bar = 100 kPa
        'bar': 1.0,      # base
        'mbar': 0.001,   # 1 bar = 1000 mbar
        'psi': 0.0689476, # 1 bar ≈ 14.5038 psi
        'MPa': 10.0,     # 1 bar = 0.1 MPa
        'kgf/cm2': 0.980665,  # 1 bar ≈ 1.019716 kgf/cm²
    }

    # Temperature units
    # Note: Temperature requires offset conversions, handled separately
    TEMPERATURE_UNITS = ['°C', 'K', '°F', '°R']

    # Flow units (all conversions TO and FROM kg/h)
    FLOW_UNITS = {
        'kg/h': 1.0,      # base
        'kg/s': 3600.0,
        'lb/h': 0.45359237,
        'lb/s': 1632.9325,
        'm³/h': None,    # requires density
        'm³/s': None,
        'L/min': None,
        'GPM': None,     # US gallons per minute
        'BPD': None,     # barrels per day (oil)
        'Nm³/h': None,   # standard cubic meters per hour (requires reference conditions)
    }

    # Length units (all conversions TO and FROM mm)
    LENGTH_UNITS = {
        'mm': 1.0,       # base
        'cm': 10.0,
        'm': 1000.0,
        'inch': 25.4,
        'ft': 304.8,
    }

    # Viscosity units (all conversions TO and FROM Pa·s)
    VISCOSITY_UNITS = {
        'Pa·s': 1.0,     # base
        'cP': 0.001,     # 1 cP = 0.001 Pa·s
        'lb/(ft·s)': 1.48816,
        'lb/(ft·h)': 0.0004133788,
    }

    # Density units (all conversions TO and FROM kg/m³)
    DENSITY_UNITS = {
        'kg/m³': 1.0,    # base
        'g/cm³': 1000.0,
        'lb/ft³': 16.0185,
        'lb/gal': 119.826,
    }

    # Energy/Enthalpy units (all conversions TO and FROM kJ/kg)
    ENERGY_UNITS = {
        'kJ/kg': 1.0,    # base
        'J/kg': 0.001,
        'cal/g': 4.184,
        'Btu/lb': 2.326,
    }

    # Specific heat units (all conversions TO and FROM kJ/(kg·K))
    SPECIFIC_HEAT_UNITS = {
        'kJ/(kg·K)': 1.0,  # base
        'J/(kg·K)': 0.001,
        'cal/(g·K)': 4.184,
        'Btu/(lb·°R)': 4.1868,
    }

    @staticmethod
    def convert_pressure(value: float, from_unit: str, to_unit: str) -> float:
        """Convert pressure between units

        Args:
            value: Value to convert
            from_unit: Source unit ('Pa', 'kPa', 'bar', 'mbar', 'psi', 'MPa', 'kgf/cm2')
            to_unit: Target unit

        Returns:
            Converted value
        """
        # Convert to bar (base unit)
        value_bar = value * UnitConverter.PRESSURE_UNITS.get(from_unit, 1.0)

        # Convert from bar to target unit
        conversion_factor = UnitConverter.PRESSURE_UNITS.get(to_unit, 1.0)
        return value_bar / conversion_factor

    @staticmethod
    def convert_temperature(value: float, from_unit: str, to_unit: str) -> float:
        """Convert temperature between units

        Args:
            value: Value to convert
            from_unit: Source unit ('°C', 'K', '°F', '°R')
            to_unit: Target unit

        Returns:
            Converted value
        """
        # Convert to Celsius first
        if from_unit == '°C':
            temp_c = value
        elif from_unit == 'K':
            temp_c = value - 273.15
        elif from_unit == '°F':
            temp_c = (value - 32) * 5/9
        elif from_unit == '°R':
            temp_c = (value - 491.67) * 5/9
        else:
            raise ValueError(f"Unknown temperature unit: {from_unit}")

        # Convert from Celsius to target unit
        if to_unit == '°C':
            return temp_c
        elif to_unit == 'K':
            return temp_c + 273.15
        elif to_unit == '°F':
            return temp_c * 9/5 + 32
        elif to_unit == '°R':
            return (temp_c + 273.15) * 9/5
        else:
            raise ValueError(f"Unknown temperature unit: {to_unit}")

    @staticmethod
    def convert_flow(value: float, from_unit: str, to_unit: str,
                    density: float = None) -> float:
        """Convert flow between units

        For volumetric to mass conversions (m³/h, L/min, GPM, BPD, Nm³/h),
        density (kg/m³) must be provided.

        Args:
            value: Value to convert
            from_unit: Source unit
            to_unit: Target unit
            density: Density in kg/m³ (required for volumetric ↔ mass conversions)

        Returns:
            Converted value

        Raises:
            ValueError: If density not provided when needed
        """
        # Convert to kg/h (base unit)
        if from_unit in UnitConverter.FLOW_UNITS:
            factor = UnitConverter.FLOW_UNITS[from_unit]
            if factor is None:
                # Volumetric unit - need density
                if density is None:
                    raise ValueError(f"Cannot convert from {from_unit} without density")
                value_kg_h = UnitConverter._volumetric_to_mass(value, from_unit, density)
            else:
                value_kg_h = value * factor
        else:
            raise ValueError(f"Unknown flow unit: {from_unit}")

        # Convert from kg/h to target unit
        if to_unit in UnitConverter.FLOW_UNITS:
            factor = UnitConverter.FLOW_UNITS[to_unit]
            if factor is None:
                # Volumetric unit - need density
                if density is None:
                    raise ValueError(f"Cannot convert to {to_unit} without density")
                return UnitConverter._mass_to_volumetric(value_kg_h, to_unit, density)
            else:
                return value_kg_h / factor
        else:
            raise ValueError(f"Unknown flow unit: {to_unit}")

    @staticmethod
    def _volumetric_to_mass(value: float, unit: str, density: float) -> float:
        """Convert volumetric flow to kg/h"""
        if unit == 'm³/h':
            return value * density
        elif unit == 'm³/s':
            return value * density * 3600
        elif unit == 'L/min':
            return value * density * 0.001 * 60  # L/min = kg/min = kg/h / 60
        elif unit == 'GPM':
            # 1 US gallon = 3.78541 L = 0.00378541 m³
            return value * 0.00378541 * density * 60  # GPM → m³/min → m³/h
        elif unit == 'BPD':
            # 1 barrel (oil) = 158.987 L = 0.158987 m³
            return value * 0.158987 * density / 24  # BPD → m³/day → m³/h
        elif unit == 'Nm³/h':
            # Standard cubic meter at 0°C, 101325 Pa
            # For ideal gas: 1 Nm³ = density at std conditions
            # Standard air density = 1.225 kg/m³ at 15°C
            # For general gas, use ideal gas law at std conditions
            # At 0°C, 101325 Pa, ideal gas density = P/RT
            R = 8314.46  # J/(kmol·K)
            # If molecular weight available, can calculate exact density
            # For now, assume standard conditions for air
            return value * 1.293  # Approximate density of air at 0°C
        else:
            raise ValueError(f"Unknown volumetric flow unit: {unit}")

    @staticmethod
    def _mass_to_volumetric(value: float, unit: str, density: float) -> float:
        """Convert kg/h to volumetric flow"""
        if unit == 'm³/h':
            return value / density
        elif unit == 'm³/s':
            return value / density / 3600
        elif unit == 'L/min':
            return value / density / 0.001 / 60  # kg/h → kg/min → L/min
        elif unit == 'GPM':
            return value / density / 0.00378541 / 60  # kg/h → kg/min → m³/min → GPM
        elif unit == 'BPD':
            return value / density / 0.158987 * 24  # kg/h → kg/day → m³/day → BPD
        elif unit == 'Nm³/h':
            return value / 1.293
        else:
            raise ValueError(f"Unknown volumetric flow unit: {unit}")

    @staticmethod
    def convert_length(value: float, from_unit: str, to_unit: str) -> float:
        """Convert length between units

        Args:
            value: Value to convert
            from_unit: Source unit ('mm', 'cm', 'm', 'inch', 'ft')
            to_unit: Target unit

        Returns:
            Converted value
        """
        # Convert to mm (base unit)
        value_mm = value * UnitConverter.LENGTH_UNITS.get(from_unit, 1.0)

        # Convert from mm to target unit
        conversion_factor = UnitConverter.LENGTH_UNITS.get(to_unit, 1.0)
        return value_mm / conversion_factor

    @staticmethod
    def convert_viscosity(value: float, from_unit: str, to_unit: str) -> float:
        """Convert viscosity between units

        Args:
            value: Value to convert
            from_unit: Source unit ('Pa·s', 'cP', 'lb/(ft·s)', 'lb/(ft·h)')
            to_unit: Target unit

        Returns:
            Converted value
        """
        # Convert to Pa·s (base unit)
        value_pa_s = value * UnitConverter.VISCOSITY_UNITS.get(from_unit, 1.0)

        # Convert from Pa·s to target unit
        conversion_factor = UnitConverter.VISCOSITY_UNITS.get(to_unit, 1.0)
        return value_pa_s / conversion_factor

    @staticmethod
    def convert_density(value: float, from_unit: str, to_unit: str) -> float:
        """Convert density between units

        Args:
            value: Value to convert
            from_unit: Source unit ('kg/m³', 'g/cm³', 'lb/ft³', 'lb/gal')
            to_unit: Target unit

        Returns:
            Converted value
        """
        # Convert to kg/m³ (base unit)
        value_kg_m3 = value * UnitConverter.DENSITY_UNITS.get(from_unit, 1.0)

        # Convert from kg/m³ to target unit
        conversion_factor = UnitConverter.DENSITY_UNITS.get(to_unit, 1.0)
        return value_kg_m3 / conversion_factor

    @staticmethod
    def convert_energy(value: float, from_unit: str, to_unit: str) -> float:
        """Convert energy/enthalpy between units

        Args:
            value: Value to convert
            from_unit: Source unit ('kJ/kg', 'J/kg', 'cal/g', 'Btu/lb')
            to_unit: Target unit

        Returns:
            Converted value
        """
        # Convert to kJ/kg (base unit)
        value_kj_kg = value * UnitConverter.ENERGY_UNITS.get(from_unit, 1.0)

        # Convert from kJ/kg to target unit
        conversion_factor = UnitConverter.ENERGY_UNITS.get(to_unit, 1.0)
        return value_kj_kg / conversion_factor

    @staticmethod
    def convert_specific_heat(value: float, from_unit: str, to_unit: str) -> float:
        """Convert specific heat between units

        Args:
            value: Value to convert
            from_unit: Source unit ('kJ/(kg·K)', 'J/(kg·K)', 'cal/(g·K)', 'Btu/(lb·°R)')
            to_unit: Target unit

        Returns:
            Converted value
        """
        # Convert to kJ/(kg·K) (base unit)
        value_kj_kg_k = value * UnitConverter.SPECIFIC_HEAT_UNITS.get(from_unit, 1.0)

        # Convert from kJ/(kg·K) to target unit
        conversion_factor = UnitConverter.SPECIFIC_HEAT_UNITS.get(to_unit, 1.0)
        return value_kj_kg_k / conversion_factor

    @staticmethod
    def get_pressure_units() -> list:
        """Get list of available pressure units"""
        return list(UnitConverter.PRESSURE_UNITS.keys())

    @staticmethod
    def get_temperature_units() -> list:
        """Get list of available temperature units"""
        return UnitConverter.TEMPERATURE_UNITS

    @staticmethod
    def get_flow_units() -> list:
        """Get list of available flow units"""
        return list(UnitConverter.FLOW_UNITS.keys())

    @staticmethod
    def get_length_units() -> list:
        """Get list of available length units"""
        return list(UnitConverter.LENGTH_UNITS.keys())

    @staticmethod
    def get_viscosity_units() -> list:
        """Get list of available viscosity units"""
        return list(UnitConverter.VISCOSITY_UNITS.keys())

    @staticmethod
    def get_density_units() -> list:
        """Get list of available density units"""
        return list(UnitConverter.DENSITY_UNITS.keys())

    @staticmethod
    def get_energy_units() -> list:
        """Get list of available energy units"""
        return list(UnitConverter.ENERGY_UNITS.keys())

    @staticmethod
    def get_specific_heat_units() -> list:
        """Get list of available specific heat units"""
        return list(UnitConverter.SPECIFIC_HEAT_UNITS.keys())


# Convenience functions for common conversions
def pressure_to_bar(value: float, unit: str) -> float:
    """Convert pressure to bar"""
    return UnitConverter.convert_pressure(value, unit, 'bar')


def pressure_from_bar(value: float, unit: str) -> float:
    """Convert pressure from bar to specified unit"""
    return UnitConverter.convert_pressure(value, 'bar', unit)


def temperature_to_celsius(value: float, unit: str) -> float:
    """Convert temperature to Celsius"""
    return UnitConverter.convert_temperature(value, unit, '°C')


def temperature_from_celsius(value: float, unit: str) -> float:
    """Convert temperature from Celsius to specified unit"""
    return UnitConverter.convert_temperature(value, '°C', unit)


def flow_to_kg_per_h(value: float, unit: str, density: float = None) -> float:
    """Convert flow to kg/h"""
    return UnitConverter.convert_flow(value, unit, 'kg/h', density)


def flow_from_kg_per_h(value: float, unit: str, density: float = None) -> float:
    """Convert flow from kg/h to specified unit"""
    return UnitConverter.convert_flow(value, 'kg/h', unit, density)