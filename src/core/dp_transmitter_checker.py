"""DP Transmitter Range Checker Module

Verifies DP transmitter range selection for any primary element.
Includes rangeability, turndown, accuracy, and 4-20mA signal analysis.
"""

import math
from typing import List, Tuple

from ..models import DPCheckResult


class DPTransmitterChecker:
    """DP transmitter range checker"""

    # Standard transmitter ranges (mbar)
    STANDARD_RANGES = [25, 50, 100, 250, 500, 1000, 2500, 5000, 10000]

    # Typical accuracy classes (% of span)
    ACCURACY_CLASSES = [0.04, 0.05, 0.075, 0.1, 0.15, 0.2, 0.25]

    def __init__(self):
        """Initialize DP transmitter checker"""
        pass

    def check_rangeability(self, dp_max: float, dp_min: float,
                           transmitter_range: float,
                           accuracy_class: float = 0.075,
                           min_turndown: float = 3.0) -> DPCheckResult:
        """Check transmitter rangeability

        Args:
            dp_max: Maximum DP [mbar]
            dp_min: Minimum DP [mbar]
            transmitter_range: Transmitter full scale range [mbar]
            accuracy_class: Transmitter accuracy class [% of span]
            min_turndown: Minimum required turndown ratio

        Returns:
            DPCheckResult with all checks
        """
        warnings = []
        overall_pass = True

        # Calculate percentages
        dp_max_pct = (dp_max / transmitter_range) * 100.0
        dp_min_pct = (dp_min / transmitter_range) * 100.0

        # Calculate turndown
        if dp_min > 0:
            turndown_ratio = dp_max / dp_min
        else:
            turndown_ratio = float('inf')

        # Calculate accuracy at various flows
        accuracy_at_max = (accuracy_class * transmitter_range / dp_max) if dp_max > 0 else float('inf')
        accuracy_at_min = (accuracy_class * transmitter_range / dp_min) if dp_min > 0 else float('inf')

        # Calculate 4-20mA signal
        signal_at_max = 4.0 + 16.0 * (dp_max / transmitter_range)
        signal_at_min = 4.0 + 16.0 * (dp_min / transmitter_range)

        # Check 1: dp_max should not exceed range
        if dp_max > transmitter_range:
            warnings.append(f"✗ DP at max flow ({dp_max:.1f} mbar) exceeds transmitter range ({transmitter_range:.1f} mbar)")
            overall_pass = False
        elif dp_max_pct > 90:
            warnings.append(f"⚠ DP at max flow is {dp_max_pct:.1f}% of range (recommended: ≤90%)")
        elif dp_max_pct < 50:
            warnings.append(f"⚠ DP at max flow is only {dp_max_pct:.1f}% of range (accuracy may be poor)")

        # Check 2: dp_min should provide adequate resolution
        if dp_min_pct < 10:
            warnings.append(f"⚠ DP at min flow is only {dp_min_pct:.1f}% of range (resolution may be inadequate)")
            if dp_min_pct < 5:
                overall_pass = False

        # Check 3: Turndown ratio
        if turndown_ratio < min_turndown:
            warnings.append(f"✗ Turndown ratio {turndown_ratio:.2f}:1 below minimum {min_turndown}:1")
            overall_pass = False

        # Check 4: Accuracy at max flow
        if accuracy_at_max > 2.0:  # 2% threshold
            warnings.append(f"⚠ Accuracy at max flow: {accuracy_at_max:.2f}% (may be acceptable)")

        # Check 5: Accuracy at min flow
        if accuracy_at_min > 5.0:  # 5% threshold
            warnings.append(f"✗ Accuracy at min flow: {accuracy_at_min:.2f}% (exceeds 5%)")
            overall_pass = False
        elif accuracy_at_min > 2.0:
            warnings.append(f"⚠ Accuracy at min flow: {accuracy_at_min:.2f}% (consider larger transmitter)")

        # Check 6: Signal range (should be within 4-20mA)
        if signal_at_max > 20.0:
            warnings.append(f"✗ Signal at max flow ({signal_at_max:.2f} mA) exceeds 20 mA")
            overall_pass = False

        if signal_at_min < 4.0:
            warnings.append(f"✗ Signal at min flow ({signal_at_min:.2f} mA) below 4 mA")
            overall_pass = False

        # Generate recommendation
        recommendation = self._generate_recommendation(
            dp_max_pct, dp_min_pct, turndown_ratio,
            accuracy_at_max, accuracy_at_min, overall_pass
        )

        return DPCheckResult(
            selected_range_mbar=transmitter_range,
            dp_max_pct_of_range=dp_max_pct,
            dp_min_pct_of_range=dp_min_pct,
            turndown_ratio=turndown_ratio,
            accuracy_at_max_flow_pct=accuracy_at_max,
            accuracy_at_min_flow_pct=accuracy_at_min,
            signal_at_max_flow_mA=signal_at_max,
            signal_at_min_flow_mA=signal_at_min,
            overall_pass=overall_pass,
            warnings=warnings,
            recommendation=recommendation
        )

    def recommend_range(self, dp_max: float, dp_min: float,
                        min_turndown: float = 3.0,
                        accuracy_class: float = 0.075) -> List[Tuple[float, DPCheckResult]]:
        """Recommend transmitter ranges

        Args:
            dp_max: Maximum DP [mbar]
            dp_min: Minimum DP [mbar]
            min_turndown: Minimum required turndown ratio
            accuracy_class: Transmitter accuracy class [% of span]

        Returns:
            List of (range, DPCheckResult) tuples, sorted by suitability
        """
        results = []

        for range_val in self.STANDARD_RANGES:
            if range_val < dp_max:
                continue  # Range too small

            result = self.check_rangeability(
                dp_max, dp_min, range_val, accuracy_class, min_turndown
            )

            results.append((range_val, result))

        # Sort by score (prefer ranges with dp_max in 70-90% range)
        results.sort(key=lambda x: self._score_range(x[0], dp_max, x[1]), reverse=True)

        return results

    def _score_range(self, range_val: float, dp_max: float, result: DPCheckResult) -> float:
        """Score a range selection (higher is better)

        Args:
            range_val: Transmitter range [mbar]
            dp_max: Maximum DP [mbar]
            result: DPCheckResult

        Returns:
            Score value
        """
        score = 0.0

        dp_pct = result.dp_max_pct_of_range

        # Prefer dp_max in 70-90% of range
        if 70 <= dp_pct <= 90:
            score += 100
        elif 60 <= dp_pct <= 95:
            score += 50
        elif 50 <= dp_pct <= 100:
            score += 20

        # Penalize if result fails
        if not result.overall_pass:
            score -= 100

        # Prefer smaller ranges (better accuracy)
        score -= (range_val / 10000.0) * 10

        return score

    def _generate_recommendation(self, dp_max_pct: float, dp_min_pct: float,
                                   turndown: float, accuracy_max: float,
                                   accuracy_min: float, overall_pass: bool) -> str:
        """Generate human-readable recommendation

        Args:
            dp_max_pct: DP at max flow as % of range
            dp_min_pct: DP at min flow as % of range
            turndown: Turndown ratio
            accuracy_max: Accuracy at max flow [%]
            accuracy_min: Accuracy at min flow [%]
            overall_pass: Overall pass status

        Returns:
            Recommendation string
        """
        parts = []

        if overall_pass:
            parts.append("✓ Transmitter range is acceptable")
        else:
            parts.append("✗ Transmitter range is not acceptable")

        if 70 <= dp_max_pct <= 90:
            parts.append(f"✓ DP at max flow {dp_max_pct:.1f}% (optimal)")
        elif dp_max_pct <= 100:
            parts.append(f"⚠ DP at max flow {dp_max_pct:.1f}%")

        if dp_min_pct >= 10:
            parts.append(f"✓ DP at min flow {dp_min_pct:.1f}% (adequate)")
        else:
            parts.append(f"⚠ DP at min flow {dp_min_pct:.1f}% (may be low)")

        if turndown >= 3.0:
            parts.append(f"✓ Turndown {turndown:.2f}:1 meets minimum")
        else:
            parts.append(f"✗ Turndown {turndown:.2f}:1 below minimum")

        parts.append(f"✓ Accuracy at max flow: ±{accuracy_max:.2f}%")
        parts.append(f"✓ Accuracy at min flow: ±{accuracy_min:.2f}%")

        return " | ".join(parts)