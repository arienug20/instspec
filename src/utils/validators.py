"""Validation utilities for InstSpec"""

from typing import List, Tuple, Optional, Any
from dataclasses import dataclass
import re


@dataclass
class ValidationResult:
    """Result of validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]


class Validators:
    """Input validation rules and utilities"""

    @staticmethod
    def validate_positive(value: float, field_name: str, allow_zero: bool = False) -> ValidationResult:
        """Validate that a value is positive (or non-negative if allow_zero=True)"""
        errors = []
        warnings = []

        if value is None:
            errors.append(f"{field_name} cannot be None")
        elif not isinstance(value, (int, float)):
            errors.append(f"{field_name} must be a number")
        elif allow_zero and value < 0:
            errors.append(f"{field_name} must be non-negative")
        elif not allow_zero and value <= 0:
            errors.append(f"{field_name} must be positive")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    @staticmethod
    def validate_range(value: float, field_name: str, min_val: float, max_val: float,
                      allow_equal: bool = True) -> ValidationResult:
        """Validate that a value is within a specified range"""
        errors = []
        warnings = []

        if value is None:
            errors.append(f"{field_name} cannot be None")
        elif not isinstance(value, (int, float)):
            errors.append(f"{field_name} must be a number")
        else:
            if allow_equal:
                if value < min_val or value > max_val:
                    errors.append(f"{field_name} must be between {min_val} and {max_val}")
            else:
                if value <= min_val or value >= max_val:
                    errors.append(f"{field_name} must be strictly between {min_val} and {max_val}")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    @staticmethod
    def validate_string(value: str, field_name: str, min_length: int = 0,
                       max_length: int = 100, pattern: Optional[str] = None) -> ValidationResult:
        """Validate a string field"""
        errors = []
        warnings = []

        if value is None:
            errors.append(f"{field_name} cannot be None")
        elif not isinstance(value, str):
            errors.append(f"{field_name} must be a string")
        else:
            if len(value) < min_length:
                errors.append(f"{field_name} must be at least {min_length} characters")
            if max_length > 0 and len(value) > max_length:
                errors.append(f"{field_name} must not exceed {max_length} characters")
            if pattern and not re.match(pattern, value):
                errors.append(f"{field_name} does not match required pattern")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    @staticmethod
    def validate_orifice_beta(beta: float) -> ValidationResult:
        """Validate orifice beta ratio (ISO 5167-2 requirements)"""
        errors = []
        warnings = []

        if beta < 0.10:
            errors.append(f"Beta ratio {beta:.3f} is below minimum of 0.10")
        elif beta > 0.75:
            errors.append(f"Beta ratio {beta:.3f} exceeds maximum of 0.75")
        elif beta < 0.20:
            warnings.append(f"Beta ratio {beta:.3f} is below preferred range [0.20, 0.60]")
        elif beta > 0.60:
            warnings.append(f"Beta ratio {beta:.3f} is above preferred range [0.20, 0.60]")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    @staticmethod
    def validate_pipe_id(pipe_id_mm: float) -> ValidationResult:
        """Validate pipe internal diameter (must be >= 50mm for ISO 5167-2)"""
        errors = []
        warnings = []

        if pipe_id_mm < 50.0:
            errors.append(f"Pipe ID {pipe_id_mm:.2f} mm is below minimum of 50 mm for ISO 5167-2")
        elif pipe_id_mm < 71.12:
            warnings.append(f"Pipe ID {pipe_id_mm:.2f} mm is below 71.12 mm; uncertainty may be higher")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    @staticmethod
    def validate_reynolds_number(re: float, beta: float) -> ValidationResult:
        """Validate Reynolds number per ISO 5167-2 requirements"""
        errors = []
        warnings = []

        # ISO 5167-2 minimum Re_D based on beta
        if beta <= 0.56:
            min_re = 10000
        else:
            min_re = 20000

        if re < min_re:
            errors.append(f"Reynolds number {re:.0f} is below minimum {min_re:.0f} for beta={beta:.2f}")

        # Additional constraint for corner/flange taps
        additional_min = 170000 * (beta ** 2) * (pipe_id_mm := 100)  # Approximate
        if re < additional_min:
            warnings.append(f"Reynolds number {re:.0f} may be low for this beta ratio")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    @staticmethod
    def validate_pressure_ratio(dp: float, p1: float) -> ValidationResult:
        """Validate pressure ratio for gas expansibility factor"""
        errors = []
        warnings = []

        ratio = dp / p1

        if ratio >= 0.25:
            errors.append(f"Pressure ratio {ratio:.3f} >= 0.25; incompressible assumption invalid")
        elif ratio >= 0.15:
            warnings.append(f"Pressure ratio {ratio:.3f} is high; check expansibility factor accuracy")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    @staticmethod
    def validate_dp_transmitter_range(dp_max: float, tx_range: float) -> ValidationResult:
        """Validate DP transmitter range"""
        errors = []
        warnings = []

        pct = (dp_max / tx_range) * 100

        if pct > 100:
            errors.append(f"DP at max flow ({dp_max:.1f} mbar) exceeds transmitter range ({tx_range:.1f} mbar)")
        elif pct > 90:
            warnings.append(f"DP at max flow is {pct:.1f}% of range; consider larger transmitter")
        elif pct < 10:
            warnings.append(f"DP at max flow is only {pct:.1f}% of range; accuracy may be poor")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    @staticmethod
    def validate_turndown_ratio(max_flow: float, min_flow: float, min_turndown: float = 3.0) -> ValidationResult:
        """Validate turndown ratio"""
        errors = []
        warnings = []

        if min_flow <= 0:
            errors.append("Min flow must be positive")

        turndown = max_flow / min_flow

        if turndown < min_turndown:
            errors.append(f"Turndown ratio {turndown:.2f} is below minimum {min_turndown:.2f}")
        elif turndown < min_turndown * 1.5:
            warnings.append(f"Turndown ratio {turndown:.2f} is marginal for accurate measurement")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    @staticmethod
    def validate_thermowell_frequency_ratio(ratio: float) -> ValidationResult:
        """Validate thermowell frequency ratio per ASME PTC 19.3"""
        errors = []
        warnings = []

        if ratio >= 0.9:
            errors.append(f"Frequency ratio {ratio:.3f} >= 0.9; UNSAFE - redesign required")
        elif ratio >= 0.8:
            warnings.append(f"Frequency ratio {ratio:.3f} in caution range [0.8, 0.9); verify design")
        elif ratio >= 0.4:
            # Check in-line oscillation
            inline_ratio = ratio * 0.5  # Approximate
            if inline_ratio >= 0.4:
                warnings.append(f"Inline frequency ratio may exceed safe limit")

        return ValidationResult(
            is_valid=ratio < 0.9,
            errors=errors,
            warnings=warnings
        )

    @staticmethod
    def validate_valve_cv(cv_required: float, cv_rated: float) -> ValidationResult:
        """Validate valve Cv selection"""
        errors = []
        warnings = []

        if cv_rated < cv_required:
            errors.append(f"Rated Cv {cv_rated:.2f} is less than required {cv_required:.2f}")

        margin = (cv_rated / cv_required - 1) * 100

        if margin < 20:
            errors.append(f"Cv margin {margin:.1f}% is below minimum 20%")
        elif margin > 200:
            warnings.append(f"Cv margin {margin:.1f}% is very large; valve may be oversized")

        return ValidationResult(
            is_valid=cv_rated >= cv_required * 1.2,
            errors=errors,
            warnings=warnings
        )

    @staticmethod
    def validate_valve_opening(opening_pct: float, flow_condition: str = "normal") -> ValidationResult:
        """Validate valve opening percentage"""
        errors = []
        warnings = []

        if flow_condition == "normal":
            if opening_pct < 50:
                warnings.append(f"Opening at normal flow is {opening_pct:.1f}% (target: 50-80%)")
            elif opening_pct > 80:
                warnings.append(f"Opening at normal flow is {opening_pct:.1f}% (target: 50-80%)")
        elif flow_condition == "max":
            if opening_pct > 90:
                errors.append(f"Opening at max flow is {opening_pct:.1f}% (maximum: 90%)")
        elif flow_condition == "min":
            if opening_pct < 20:
                errors.append(f"Opening at min flow is {opening_pct:.1f}% (minimum: 20%)")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    @staticmethod
    def validate_cavitation_index(sigma: float) -> ValidationResult:
        """Validate cavitation index"""
        errors = []
        warnings = []

        if sigma <= 1.0:
            errors.append(f"Cavitation index {sigma:.2f} <= 1.0; full cavitation expected - damage risk")
        elif sigma <= 2.0:
            warnings.append(f"Cavitation index {sigma:.2f} indicates incipient cavitation; noise expected")

        return ValidationResult(
            is_valid=sigma > 1.0,
            errors=errors,
            warnings=warnings
        )

    @staticmethod
    def validate_tag_number(tag: str) -> ValidationResult:
        """Validate instrument tag number format (e.g., FT-101, PT-201A)"""
        errors = []
        warnings = []

        if not tag:
            errors.append("Tag number cannot be empty")

        # Common tag format: XX-NNN or XX-NNNX
        if not re.match(r'^[A-Z]{2,3}-\d{3,4}[A-Z]?$', tag):
            warnings.append(f"Tag number '{tag}' may not follow standard format (e.g., FT-101)")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    @staticmethod
    def validate_schedule(schedule: str) -> ValidationResult:
        """Validate pipe schedule"""
        errors = []
        warnings = []

        valid_schedules = [
            'SCH5', 'SCH5S', 'SCH10', 'SCH10S', 'SCH20', 'SCH30',
            'SCH40', 'SCH40S', 'SCH60', 'SCH80', 'SCH80S',
            'SCH100', 'SCH120', 'SCH140', 'SCH160', 'XS', 'XXS'
        ]

        if schedule.upper() not in valid_schedules:
            errors.append(f"Invalid schedule '{schedule}'. Must be one of: {', '.join(valid_schedules)}")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    @staticmethod
    def combine_validations(*results: ValidationResult) -> ValidationResult:
        """Combine multiple validation results"""
        all_errors = []
        all_warnings = []

        for result in results:
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)

        return ValidationResult(
            is_valid=len(all_errors) == 0,
            errors=all_errors,
            warnings=all_warnings
        )


def validate_required_fields(data: dict, required_fields: List[str]) -> ValidationResult:
    """Validate that all required fields are present and not empty"""
    errors = []
    warnings = []

    for field in required_fields:
        if field not in data:
            errors.append(f"Required field '{field}' is missing")
        elif data[field] is None:
            errors.append(f"Required field '{field}' is None")
        elif isinstance(data[field], str) and not data[field].strip():
            errors.append(f"Required field '{field}' is empty")
        elif isinstance(data[field], (list, dict)) and len(data[field]) == 0:
            errors.append(f"Required field '{field}' is empty")

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings
    )