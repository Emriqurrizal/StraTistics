import decimal
from unittest.mock import MagicMock, patch
import numpy as np
import pandas as pd
import pytest

from dashboard.components.kpi_cards import _safe_float, format_pace, render_kpi_row


class TestSafeFloat:
    """Unit tests for _safe_float helper function."""

    def test_valid_numbers(self):
        assert _safe_float(5) == 5.0
        assert _safe_float(5.25) == 5.25
        assert _safe_float("4.5") == 4.5
        assert _safe_float(decimal.Decimal("6.75")) == 6.75

    def test_null_and_nan_values(self):
        assert _safe_float(None) is None
        assert _safe_float(np.nan) is None
        assert _safe_float(pd.NA) is None
        assert _safe_float(float("nan")) is None

    def test_invalid_types(self):
        assert _safe_float("not_a_number") is None
        assert _safe_float([]) is None
        assert _safe_float({}) is None


class TestFormatPace:
    """Unit tests for format_pace function."""

    def test_valid_pace(self):
        assert format_pace(5.0) == "5:00"
        assert format_pace(5.5) == "5:30"
        assert format_pace(4.25) == "4:15"
        assert format_pace(decimal.Decimal("5.75")) == "5:45"

    def test_rounding_boundary(self):
        # 5.99999 minutes should roll over to 6:00, not 5:60
        assert format_pace(5.99999) == "6:00"

    def test_null_zero_and_negative(self):
        assert format_pace(None) == "0:00"
        assert format_pace(np.nan) == "0:00"
        assert format_pace(pd.NA) == "0:00"
        assert format_pace(0) == "0:00"
        assert format_pace(-1.5) == "0:00"


class TestRenderKpiRow:
    """Unit tests for render_kpi_row component."""

    @pytest.fixture(autouse=True)
    def setup_mock_streamlit(self):
        """Mock streamlit columns and metric calls."""
        with patch("streamlit.columns") as mock_cols, patch("streamlit.metric") as mock_metric:
            self.mock_cols = mock_cols
            self.mock_metric = mock_metric
            # Return context-manager mocks for columns
            mock_cols.return_value = [MagicMock() for _ in range(10)]
            yield

    def test_render_without_previous_metrics(self):
        metrics = {
            "Total Distance": (10.5, "km"),
            "Total Runs": (2, "int"),
            "Avg Pace": (5.25, "pace"),
            "Total Duration": (1.2, "hrs"),
            "Total Elevation": (120, "m"),
        }
        render_kpi_row(metrics)
        assert self.mock_metric.call_count == 5
        # Verify delta is None when no previous_metrics provided
        for call in self.mock_metric.call_args_list:
            assert call.kwargs["delta"] is None

    def test_render_exact_bug_scenario_current_pace_none(self):
        """Current pace is None, previous pace is float 5.25.
        Previously crashed with: TypeError: unsupported operand type(s) for -: 'float' and 'NoneType'.
        """
        metrics = {
            "Avg Pace": (None, "pace"),
            "Total Distance": (0, "km"),
        }
        prev_metrics = {
            "Avg Pace": (5.25, "pace"),
            "Total Distance": (15.0, "km"),
        }
        render_kpi_row(metrics, previous_metrics=prev_metrics)

        calls = {call.kwargs["label"]: call.kwargs for call in self.mock_metric.call_args_list}
        assert calls["Avg Pace"]["value"] == "0:00"
        assert calls["Avg Pace"]["delta"] is None

    def test_render_pace_delta_faster_and_slower(self):
        # Current is 5.0 (faster than 5.5)
        metrics = {"Avg Pace": (5.0, "pace")}
        prev_metrics = {"Avg Pace": (decimal.Decimal("5.5"), "pace")}
        render_kpi_row(metrics, previous_metrics=prev_metrics)

        call_kwargs = self.mock_metric.call_args_list[-1].kwargs
        assert call_kwargs["value"] == "5:00"
        assert call_kwargs["delta"] == "0:30 faster"
        assert call_kwargs["delta_color"] == "normal"

        # Current is 6.0 (slower than 5.5)
        metrics_slower = {"Avg Pace": (6.0, "pace")}
        render_kpi_row(metrics_slower, previous_metrics=prev_metrics)
        call_slower = self.mock_metric.call_args_list[-1].kwargs
        assert call_slower["value"] == "6:00"
        assert call_slower["delta"] == "0:30 slower"
        assert call_slower["delta_color"] == "inverse"

    def test_render_percentage_metric_deltas(self):
        metrics = {"Total Distance": (20.0, "km")}
        prev_metrics = {"Total Distance": (10.0, "km")}
        render_kpi_row(metrics, previous_metrics=prev_metrics)

        call_kwargs = self.mock_metric.call_args_list[-1].kwargs
        assert call_kwargs["value"] == "20.0 km"
        assert call_kwargs["delta"] == "100.0%"
        assert call_kwargs["delta_color"] == "normal"

    def test_render_zero_prior_metric_avoids_division_by_zero(self):
        metrics = {"Total Distance": (10.0, "km")}
        prev_metrics = {"Total Distance": (0, "km")}
        render_kpi_row(metrics, previous_metrics=prev_metrics)

        call_kwargs = self.mock_metric.call_args_list[-1].kwargs
        assert call_kwargs["value"] == "10.0 km"
        assert call_kwargs["delta"] is None

    def test_render_null_fallbacks_for_all_metric_types(self):
        metrics = {
            "Distance": (None, "km"),
            "Elevation": (np.nan, "m"),
            "Runs": (pd.NA, "int"),
            "Duration": (None, "hrs"),
            "Other": (None, "unknown"),
        }
        render_kpi_row(metrics)
        calls = {call.kwargs["label"]: call.kwargs["value"] for call in self.mock_metric.call_args_list}
        assert calls["Distance"] == "0.0 km"
        assert calls["Elevation"] == "0 m"
        assert calls["Runs"] == "0"
        assert calls["Duration"] == "0.0 hrs"
        assert calls["Other"] == "-"
