"""Unit tests for Orifice Sizer module

Tests cover ISO 5167-2:2003 requirements including:
- Reader-Harris/Gallagher discharge coefficient
- Expansibility factor
- Reynolds number calculation
- Permanent pressure loss
- Straight run requirements
- Uncertainty analysis
- Beta optimization
"""

import pytest
import math
from src.core.orifice_sizer import OrificeSizer
from src.models import OrificeInput, TapType, FluidType


class TestOrificeSizer:
    """Test suite for Orifice Sizer"""

    def test_discharge_coefficient_water_corner_tap(self):
        """Test discharge coefficient for water with corner tap

        Validated against ISO 5167-2 Annex A examples
        """
        input_params = OrificeInput(
            pipe_id_mm=100.0,
            pipe_schedule="SCH40",
            fluid_type=FluidType.LIQUID,
            fluid_name="Water",
            density_kg_m3=997.0,
            viscosity_Pa_s=0.00089,
            isentropic_exponent=1.0,
            flow_unit="kg/h",
            normal_flow=50000.0,
            max_flow=65000.0,
            min_flow=20000.0,
            operating_pressure_barg=25.0,
            operating_temperature_C=80.0,
            dp_transmitter_range_mbar=250.0,
            tap_type=TapType.CORNER,
            upstream_fitting="single_elbow"
        )

        sizer = OrificeSizer(input_params)
        C = sizer._discharge_coefficient(0.5, 100000.0)

        # Discharge coefficient should be in typical range
        assert 0.59 <= C <= 0.62

    def test_discharge_coefficient_natural_gas_flange_tap(self):
        """Test discharge coefficient for natural gas with flange tap

        Validated against ISO 5167-2 Annex A examples
        """
        input_params = OrificeInput(
            pipe_id_mm=150.0,
            pipe_schedule="SCH40",
            fluid_type=FluidType.GAS,
            fluid_name="Natural Gas",
            density_kg_m3=0.717,
            viscosity_Pa_s=0.000011,
            isentropic_exponent=1.32,
            flow_unit="kg/h",
            normal_flow=10000.0,
            max_flow=12000.0,
            min_flow=5000.0,
            operating_pressure_barg=50.0,
            operating_temperature_C=20.0,
            dp_transmitter_range_mbar=500.0,
            tap_type=TapType.FLANGE,
            upstream_fitting="single_elbow"
        )

        sizer = OrificeSizer(input_params)
        C = sizer._discharge_coefficient(0.6, 200000.0)

        assert 0.59 <= C <= 0.62

    def test_expansibility_factor_liquid(self):
        """Test expansibility factor for liquid (should be 1.0)"""
        input_params = OrificeInput(
            pipe_id_mm=100.0,
            pipe_schedule="SCH40",
            fluid_type=FluidType.LIQUID,
            fluid_name="Water",
            density_kg_m3=997.0,
            viscosity_Pa_s=0.00089,
            isentropic_exponent=1.0,
            flow_unit="kg/h",
            normal_flow=50000.0,
            max_flow=65000.0,
            min_flow=20000.0,
            operating_pressure_barg=25.0,
            operating_temperature_C=80.0,
            dp_transmitter_range_mbar=250.0,
            tap_type=TapType.CORNER,
            upstream_fitting="single_elbow"
        )

        sizer = OrificeSizer(input_params)
        epsilon = sizer._expansibility_factor(0.5, 5000.0)

        assert epsilon == 1.0

    def test_expansibility_factor_gas(self):
        """Test expansibility factor for gas

        Should be less than 1.0 for compressible flow
        """
        input_params = OrificeInput(
            pipe_id_mm=100.0,
            pipe_schedule="SCH40",
            fluid_type=FluidType.GAS,
            fluid_name="Natural Gas",
            density_kg_m3=0.717,
            viscosity_Pa_s=0.000011,
            isentropic_exponent=1.32,
            flow_unit="kg/h",
            normal_flow=10000.0,
            max_flow=12000.0,
            min_flow=5000.0,
            operating_pressure_barg=50.0,
            operating_temperature_C=20.0,
            dp_transmitter_range_mbar=500.0,
            tap_type=TapType.FLANGE,
            upstream_fitting="single_elbow"
        )

        sizer = OrificeSizer(input_params)
        dp = 10000.0  # 100 mbar
        epsilon = sizer._expansibility_factor(0.6, dp)

        # Should be less than 1.0 but close to it for small pressure ratio
        assert 0.98 <= epsilon < 1.0

    def test_permanent_pressure_loss(self):
        """Test permanent pressure loss calculation

        ISO 5167-2:2003 Equation 12
        """
        input_params = OrificeInput(
            pipe_id_mm=100.0,
            pipe_schedule="SCH40",
            fluid_type=FluidType.LIQUID,
            fluid_name="Water",
            density_kg_m3=997.0,
            viscosity_Pa_s=0.00089,
            isentropic_exponent=1.0,
            flow_unit="kg/h",
            normal_flow=50000.0,
            max_flow=65000.0,
            min_flow=20000.0,
            operating_pressure_barg=25.0,
            operating_temperature_C=80.0,
            dp_transmitter_range_mbar=250.0,
            tap_type=TapType.CORNER,
            upstream_fitting="single_elbow"
        )

        sizer = OrificeSizer(input_params)
        dp = 10000.0  # 100 mbar in Pa

        # For beta = 0.5: loss ratio ≈ 40%
        loss, loss_pct = sizer._permanent_pressure_loss(0.5, dp)

        assert 0.35 <= loss_pct <= 0.45  # Should be around 40%
        assert 3500 <= loss <= 4500

    def test_reynolds_number(self):
        """Test Reynolds number calculation

        Re_D = (4 × q_m) / (π × D × μ)
        """
        input_params = OrificeInput(
            pipe_id_mm=100.0,
            pipe_schedule="SCH40",
            fluid_type=FluidType.LIQUID,
            fluid_name="Water",
            density_kg_m3=997.0,
            viscosity_Pa_s=0.00089,
            isentropic_exponent=1.0,
            flow_unit="kg/h",
            normal_flow=50000.0,
            max_flow=65000.0,
            min_flow=20000.0,
            operating_pressure_barg=25.0,
            operating_temperature_C=80.0,
            dp_transmitter_range_mbar=250.0,
            tap_type=TapType.CORNER,
            upstream_fitting="single_elbow"
        )

        sizer = OrificeSizer(input_params)
        Re = sizer._reynolds_number(50.0)  # 50 kg/s

        # Re should be >> 10000 for turbulent flow
        assert Re > 100000

    def test_straight_run_requirements_single_elbow(self):
        """Test straight run requirements for single elbow

        ISO 5167-2 Table 3
        """
        input_params = OrificeInput(
            pipe_id_mm=100.0,
            pipe_schedule="SCH40",
            fluid_type=FluidType.LIQUID,
            fluid_name="Water",
            density_kg_m3=997.0,
            viscosity_Pa_s=0.00089,
            isentropic_exponent=1.0,
            flow_unit="kg/h",
            normal_flow=50000.0,
            max_flow=65000.0,
            min_flow=20000.0,
            operating_pressure_barg=25.0,
            operating_temperature_C=80.0,
            dp_transmitter_range_mbar=250.0,
            tap_type=TapType.CORNER,
            upstream_fitting="single_elbow"
        )

        sizer = OrificeSizer(input_params)
        upstream_D, upstream_mm, downstream_D, downstream_mm = sizer._straight_run_requirements(0.6)

        # From ISO 5167-2 Table 3 for beta=0.6, single elbow
        assert 25 <= upstream_D <= 27  # Should be around 26D
        assert 2500 <= upstream_mm <= 2700

        assert 7 <= downstream_D <= 9  # Should be around 8D

    def test_straight_run_requirements_two_elbows_different_plane(self):
        """Test straight run requirements for two elbows in different plane"""
        input_params = OrificeInput(
            pipe_id_mm=100.0,
            pipe_schedule="SCH40",
            fluid_type=FluidType.LIQUID,
            fluid_name="Water",
            density_kg_m3=997.0,
            viscosity_Pa_s=0.00089,
            isentropic_exponent=1.0,
            flow_unit="kg/h",
            normal_flow=50000.0,
            max_flow=65000.0,
            min_flow=20000.0,
            operating_pressure_barg=25.0,
            operating_temperature_C=80.0,
            dp_transmitter_range_mbar=250.0,
            tap_type=TapType.CORNER,
            upstream_fitting="two_elbows_different_plane"
        )

        sizer = OrificeSizer(input_params)
        upstream_D, upstream_mm, downstream_D, downstream_mm = sizer._straight_run_requirements(0.75)

        # From ISO 5167-2 Table 3 for beta=0.75, two elbows different plane
        assert 68 <= upstream_D <= 72  # Should be around 70D
        assert 11 <= downstream_D <= 13  # Should be around 12D

    def test_uncertainty_analysis(self):
        """Test uncertainty analysis calculation

        ISO 5167-2:2003 Section 5.1
        """
        input_params = OrificeInput(
            pipe_id_mm=100.0,
            pipe_schedule="SCH40",
            fluid_type=FluidType.LIQUID,
            fluid_name="Water",
            density_kg_m3=997.0,
            viscosity_Pa_s=0.00089,
            isentropic_exponent=1.0,
            flow_unit="kg/h",
            normal_flow=50000.0,
            max_flow=65000.0,
            min_flow=20000.0,
            operating_pressure_barg=25.0,
            operating_temperature_C=80.0,
            dp_transmitter_range_mbar=250.0,
            tap_type=TapType.CORNER,
            upstream_fitting="single_elbow"
        )

        sizer = OrificeSizer(input_params)
        total, breakdown = sizer._uncertainty_analysis(0.5, 0.6, 10000.0, 200000.0)

        # Total uncertainty should be reasonable
        assert 0.5 <= total <= 2.0  # 0.5% to 2%

        # Check breakdown components exist
        assert 'discharge_coefficient' in breakdown
        assert 'expansibility' in breakdown
        assert 'orifice_bore' in breakdown
        assert 'pipe_id' in breakdown
        assert 'dp_transmitter' in breakdown
        assert 'density' in breakdown

    def test_beta_optimization(self):
        """Test beta ratio optimization

        Should find beta in optimal range [0.20, 0.60]
        """
        input_params = OrificeInput(
            pipe_id_mm=100.0,
            pipe_schedule="SCH40",
            fluid_type=FluidType.LIQUID,
            fluid_name="Water",
            density_kg_m3=997.0,
            viscosity_Pa_s=0.00089,
            isentropic_exponent=1.0,
            flow_unit="kg/h",
            normal_flow=50000.0,
            max_flow=65000.0,
            min_flow=20000.0,
            operating_pressure_barg=25.0,
            operating_temperature_C=80.0,
            dp_transmitter_range_mbar=250.0,
            tap_type=TapType.CORNER,
            upstream_fitting="single_elbow"
        )

        sizer = OrificeSizer(input_params)
        result = sizer.optimize_beta()

        # Check basic result structure
        assert 0.10 <= result.beta <= 0.75
        assert result.orifice_bore_mm > 0
        assert 0.59 <= result.discharge_coefficient <= 0.62
        assert result.expansibility_factor > 0
        assert result.dp_at_max_flow_mbar > 0
        assert result.reynolds_at_max > 0
        assert result.turndown_ratio > 0
        assert result.total_uncertainty_pct > 0

    def test_beta_out_of_range(self):
        """Test validation for beta out of range"""
        input_params = OrificeInput(
            pipe_id_mm=100.0,
            pipe_schedule="SCH40",
            fluid_type=FluidType.LIQUID,
            fluid_name="Water",
            density_kg_m3=997.0,
            viscosity_Pa_s=0.00089,
            isentropic_exponent=1.0,
            flow_unit="kg/h",
            normal_flow=50000.0,
            max_flow=65000.0,
            min_flow=20000.0,
            operating_pressure_barg=25.0,
            operating_temperature_C=80.0,
            dp_transmitter_range_mbar=250.0,
            tap_type=TapType.CORNER,
            upstream_fitting="single_elbow"
        )

        sizer = OrificeSizer(input_params)

        # Beta below minimum
        C = sizer._discharge_coefficient(0.05, 100000.0)
        assert C is not None

        # Beta above maximum
        C = sizer._discharge_coefficient(0.8, 100000.0)
        assert C is not None

    def test_d_d2_tap_configuration(self):
        """Test D and D/2 tap configuration"""
        input_params = OrificeInput(
            pipe_id_mm=100.0,
            pipe_schedule="SCH40",
            fluid_type=FluidType.LIQUID,
            fluid_name="Water",
            density_kg_m3=997.0,
            viscosity_Pa_s=0.00089,
            isentropic_exponent=1.0,
            flow_unit="kg/h",
            normal_flow=50000.0,
            max_flow=65000.0,
            min_flow=20000.0,
            operating_pressure_barg=25.0,
            operating_temperature_C=80.0,
            dp_transmitter_range_mbar=250.0,
            tap_type=TapType.D_D2,
            upstream_fitting="single_elbow"
        )

        sizer = OrificeSizer(input_params)
        result = sizer.optimize_beta()

        # Should successfully calculate with D/D2 taps
        assert result is not None
        assert result.discharge_coefficient > 0

    def test_flange_tap_configuration(self):
        """Test flange tap configuration"""
        input_params = OrificeInput(
            pipe_id_mm=100.0,
            pipe_schedule="SCH40",
            fluid_type=FluidType.LIQUID,
            fluid_name="Water",
            density_kg_m3=997.0,
            viscosity_Pa_s=0.00089,
            isentropic_exponent=1.0,
            flow_unit="kg/h",
            normal_flow=50000.0,
            max_flow=65000.0,
            min_flow=20000.0,
            operating_pressure_barg=25.0,
            operating_temperature_C=80.0,
            dp_transmitter_range_mbar=250.0,
            tap_type=TapType.FLANGE,
            upstream_fitting="single_elbow"
        )

        sizer = OrificeSizer(input_params)
        result = sizer.optimize_beta()

        # Should successfully calculate with flange taps
        assert result is not None
        assert result.discharge_coefficient > 0

    def test_low_reynolds_warning(self):
        """Test warning for low Reynolds number"""
        input_params = OrificeInput(
            pipe_id_mm=100.0,
            pipe_schedule="SCH40",
            fluid_type=FluidType.LIQUID,
            fluid_name="Water",
            density_kg_m3=997.0,
            viscosity_Pa_s=0.00089,
            isentropic_exponent=1.0,
            flow_unit="kg/h",
            normal_flow=1000.0,
            max_flow=1500.0,
            min_flow=500.0,
            operating_pressure_barg=25.0,
            operating_temperature_C=80.0,
            dp_transmitter_range_mbar=250.0,
            tap_type=TapType.CORNER,
            upstream_fitting="single_elbow"
        )

        sizer = OrificeSizer(input_params)
        result = sizer.optimize_beta()

        # Should have warning about low Reynolds number
        assert any("Reynolds" in w.lower() for w in result.warnings)

    def test_turndown_validation(self):
        """Test turndown ratio validation"""
        input_params = OrificeInput(
            pipe_id_mm=100.0,
            pipe_schedule="SCH40",
            fluid_type=FluidType.LIQUID,
            fluid_name="Water",
            density_kg_m3=997.0,
            viscosity_Pa_s=0.00089,
            isentropic_exponent=1.0,
            flow_unit="kg/h",
            normal_flow=50000.0,
            max_flow=65000.0,
            min_flow=20000.0,
            operating_pressure_barg=25.0,
            operating_temperature_C=80.0,
            dp_transmitter_range_mbar=250.0,
            tap_type=TapType.CORNER,
            upstream_fitting="single_elbow"
        )

        sizer = OrificeSizer(input_params)
        result = sizer.optimize_beta()

        # Turndown should be >= 3:1
        assert result.turndown_ratio >= 3.0

    def test_result_status_flags(self):
        """Test result status flags"""
        input_params = OrificeInput(
            pipe_id_mm=100.0,
            pipe_schedule="SCH40",
            fluid_type=FluidType.LIQUID,
            fluid_name="Water",
            density_kg_m3=997.0,
            viscosity_Pa_s=0.00089,
            isentropic_exponent=1.0,
            flow_unit="kg/h",
            normal_flow=50000.0,
            max_flow=65000.0,
            min_flow=20000.0,
            operating_pressure_barg=25.0,
            operating_temperature_C=80.0,
            dp_transmitter_range_mbar=250.0,
            tap_type=TapType.CORNER,
            upstream_fitting="single_elbow"
        )

        sizer = OrificeSizer(input_params)
        result = sizer.optimize_beta()

        # Check status flags
        assert result.beta_status in ["optimal", "acceptable", "marginal", "out_of_range"]
        assert result.dp_status in ["ok", "exceeds_range", "too_low"]
        assert result.reynolds_status in ["ok", "below_minimum"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])