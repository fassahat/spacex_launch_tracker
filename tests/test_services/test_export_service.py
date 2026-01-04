"""Tests for ExportService."""

import json
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.export_service import ExportService
from app.services.launch_service import LaunchService
from app.models.launch import Launch
from app.models.rocket import Rocket
from app.models.launchpad import Launchpad


@pytest.fixture
def mock_launch_service():
    """Create a mock launch service."""
    service = MagicMock(spec=LaunchService)
    service.api_client = MagicMock()
    return service


@pytest.fixture
def export_service(mock_launch_service):
    """Create an ExportService instance with mock dependencies."""
    return ExportService(mock_launch_service)


@pytest.fixture
def sample_rockets():
    """Sample rocket data."""
    return [
        Rocket(id="rocket1", name="Falcon 9", type="orbital", active=True),
        Rocket(id="rocket2", name="Falcon Heavy", type="orbital", active=True)
    ]


@pytest.fixture
def sample_launchpads():
    """Sample launchpad data."""
    return [
        Launchpad(id="pad1", name="LC-39A", full_name="Launch Complex 39A", locality="Cape Canaveral", region="Florida", status="active"),
        Launchpad(id="pad2", name="SLC-40", full_name="Space Launch Complex 40", locality="Cape Canaveral", region="Florida", status="active")
    ]


@pytest.fixture
def sample_launches():
    """Sample launch data."""
    return [
        Launch(
            id="launch1",
            name="Starlink Mission",
            date_utc=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            rocket="rocket1",
            launchpad="pad1",
            success=True,
            flight_number=100,
            details="Successful Starlink deployment",
            upcoming=False
        ),
        Launch(
            id="launch2",
            name="GPS Satellite",
            date_utc=datetime(2024, 2, 20, 14, 15, 0, tzinfo=timezone.utc),
            rocket="rocket2",
            launchpad="pad2",
            success=True,
            flight_number=101,
            details="GPS satellite deployment",
            upcoming=False
        ),
        Launch(
            id="launch3",
            name="Upcoming Mission",
            date_utc=None,
            rocket="rocket1",
            launchpad="pad1",
            success=None,
            flight_number=102,
            details=None,
            upcoming=True
        )
    ]


class TestPrepareData:
    """Tests for prepare_launch_data method."""

    @pytest.mark.asyncio
    async def test_prepare_launch_data_no_filters(
        self, export_service, mock_launch_service, sample_rockets,
        sample_launchpads, sample_launches
    ):
        """Test preparing launch data without filters."""
        # Setup mocks
        mock_launch_service.api_client.get_all_rockets = AsyncMock(return_value=sample_rockets)
        mock_launch_service.api_client.get_all_launchpads = AsyncMock(return_value=sample_launchpads)
        mock_launch_service.get_filtered_launches = AsyncMock(return_value=sample_launches)

        # Call method
        launches, rocket_map, launchpad_map = await export_service.prepare_launch_data()

        # Assertions
        assert len(launches) == 3
        assert rocket_map == {"rocket1": "Falcon 9", "rocket2": "Falcon Heavy"}
        assert launchpad_map == {"pad1": "LC-39A", "pad2": "SLC-40"}
        mock_launch_service.api_client.get_all_rockets.assert_called_once()
        mock_launch_service.api_client.get_all_launchpads.assert_called_once()

    @pytest.mark.asyncio
    async def test_prepare_launch_data_with_filters(
        self, export_service, mock_launch_service, sample_rockets,
        sample_launchpads, sample_launches
    ):
        """Test preparing launch data with filters."""
        # Setup mocks
        mock_launch_service.api_client.get_all_rockets = AsyncMock(return_value=sample_rockets)
        mock_launch_service.api_client.get_all_launchpads = AsyncMock(return_value=sample_launchpads)
        mock_launch_service.get_filtered_launches = AsyncMock(return_value=[sample_launches[0]])

        # Call method with filters
        launches, rocket_map, launchpad_map = await export_service.prepare_launch_data(
            rocket_name="Falcon 9",
            success="true",
            date_from="2024-01-01",
            date_to="2024-01-31"
        )

        # Assertions
        assert len(launches) == 1
        assert launches[0].name == "Starlink Mission"

        # Verify get_filtered_launches was called with correct parameters
        call_args = mock_launch_service.get_filtered_launches.call_args
        filter_obj = call_args[0][0]
        assert filter_obj.rocket_name == "Falcon 9"
        assert filter_obj.success is True
        assert filter_obj.date_from == datetime(2024, 1, 1, tzinfo=timezone.utc)
        assert filter_obj.date_to == datetime(2024, 1, 31, 23, 59, 59, tzinfo=timezone.utc)

    @pytest.mark.asyncio
    async def test_prepare_launch_data_with_pagination(
        self, export_service, mock_launch_service, sample_rockets,
        sample_launchpads, sample_launches
    ):
        """Test preparing launch data with pagination (multiple pages)."""
        # Setup mocks
        mock_launch_service.api_client.get_all_rockets = AsyncMock(return_value=sample_rockets)
        mock_launch_service.api_client.get_all_launchpads = AsyncMock(return_value=sample_launchpads)

        # Simulate pagination: first call returns 1000 items, second returns remaining items
        first_page = sample_launches * 334  # 1002 items (simulate full page)
        second_page = sample_launches[:2]  # 2 items (last page)

        mock_launch_service.get_filtered_launches = AsyncMock(side_effect=[
            first_page[:1000],  # First call returns 1000
            second_page  # Second call returns remaining
        ])

        # Call method
        launches, _, _ = await export_service.prepare_launch_data()

        # Assertions
        assert len(launches) == 1002
        assert mock_launch_service.get_filtered_launches.call_count == 2

    @pytest.mark.asyncio
    async def test_prepare_launch_data_empty_result(
        self, export_service, mock_launch_service, sample_rockets, sample_launchpads
    ):
        """Test preparing launch data with no matching results."""
        # Setup mocks
        mock_launch_service.api_client.get_all_rockets = AsyncMock(return_value=sample_rockets)
        mock_launch_service.api_client.get_all_launchpads = AsyncMock(return_value=sample_launchpads)
        mock_launch_service.get_filtered_launches = AsyncMock(return_value=[])

        # Call method
        launches, rocket_map, launchpad_map = await export_service.prepare_launch_data(
            rocket_name="Nonexistent Rocket"
        )

        # Assertions
        assert len(launches) == 0
        assert len(rocket_map) == 2
        assert len(launchpad_map) == 2


class TestGenerateCSV:
    """Tests for generate_csv method."""

    def test_generate_csv_basic(self, export_service, sample_launches):
        """Test CSV generation with basic data."""
        rocket_map = {"rocket1": "Falcon 9", "rocket2": "Falcon Heavy"}
        launchpad_map = {"pad1": "LC-39A", "pad2": "SLC-40"}

        csv_content = export_service.generate_csv(sample_launches, rocket_map, launchpad_map)

        # Verify CSV structure
        lines = csv_content.strip().split('\n')
        assert len(lines) == 4  # Header + 3 data rows

        # Verify header
        assert "Mission Name" in lines[0]
        assert "Date (UTC)" in lines[0]
        assert "Rocket" in lines[0]
        assert "Success" in lines[0]

        # Verify data rows
        assert "Starlink Mission" in lines[1]
        assert "Falcon 9" in lines[1]
        assert "Success" in lines[1]

        assert "GPS Satellite" in lines[2]
        assert "Falcon Heavy" in lines[2]

        assert "Upcoming Mission" in lines[3]
        assert "TBD" in lines[3]  # No date for upcoming
        assert "Upcoming" in lines[3]  # Status

    def test_generate_csv_with_failed_launch(self, export_service):
        """Test CSV generation with failed launch."""
        failed_launch = Launch(
            id="launch_fail",
            name="Failed Mission",
            date_utc=datetime(2024, 1, 1, tzinfo=timezone.utc),
            rocket="rocket1",
            launchpad="pad1",
            success=False,
            flight_number=99,
            details="Launch failure",
            upcoming=False
        )

        rocket_map = {"rocket1": "Falcon 9"}
        launchpad_map = {"pad1": "LC-39A"}

        csv_content = export_service.generate_csv([failed_launch], rocket_map, launchpad_map)

        # Verify failed status
        lines = csv_content.strip().split('\n')
        assert "Failed" in lines[1]

    def test_generate_csv_with_missing_details(self, export_service):
        """Test CSV generation with missing details."""
        minimal_launch = Launch(
            id="launch_min",
            name="Minimal Launch",
            date_utc=datetime(2024, 1, 1, tzinfo=timezone.utc),
            rocket="unknown_rocket",
            launchpad="unknown_pad",
            success=True,
            flight_number=None,
            details=None,
            upcoming=False
        )

        rocket_map = {}
        launchpad_map = {}

        csv_content = export_service.generate_csv([minimal_launch], rocket_map, launchpad_map)

        # Verify handling of missing data
        lines = csv_content.strip().split('\n')
        # When rocket/pad not in map, it falls back to ID or 'Unknown'
        assert "unknown_rocket" in lines[1] or "Unknown" in lines[1]
        assert "-" in lines[1]  # No flight number

    def test_generate_csv_empty_list(self, export_service):
        """Test CSV generation with empty launch list."""
        csv_content = export_service.generate_csv([], {}, {})

        # Should only have header
        lines = csv_content.strip().split('\n')
        assert len(lines) == 1
        assert "Mission Name" in lines[0]


class TestGenerateJSON:
    """Tests for generate_json method."""

    def test_generate_json_basic(self, export_service, sample_launches):
        """Test JSON generation with basic data."""
        rocket_map = {"rocket1": "Falcon 9", "rocket2": "Falcon Heavy"}
        launchpad_map = {"pad1": "LC-39A", "pad2": "SLC-40"}

        json_content = export_service.generate_json(sample_launches, rocket_map, launchpad_map)

        # Parse and verify JSON
        data = json.loads(json_content)
        assert len(data) == 3

        # Verify first launch
        assert data[0]["mission_name"] == "Starlink Mission"
        assert data[0]["rocket"] == "Falcon 9"
        assert data[0]["launchpad"] == "LC-39A"
        assert data[0]["success"] is True
        assert data[0]["flight_number"] == 100
        assert data[0]["upcoming"] is False

        # Verify upcoming launch
        assert data[2]["mission_name"] == "Upcoming Mission"
        assert data[2]["date_utc"] is None
        assert data[2]["success"] is None
        assert data[2]["upcoming"] is True

    def test_generate_json_with_special_characters(self, export_service):
        """Test JSON generation with special characters in details."""
        launch_with_special = Launch(
            id="launch_special",
            name='Mission "Apollo"',
            date_utc=datetime(2024, 1, 1, tzinfo=timezone.utc),
            rocket="rocket1",
            launchpad="pad1",
            success=True,
            flight_number=100,
            details="Details with 'quotes' and \"double quotes\"",
            upcoming=False
        )

        rocket_map = {"rocket1": "Falcon 9"}
        launchpad_map = {"pad1": "LC-39A"}

        json_content = export_service.generate_json([launch_with_special], rocket_map, launchpad_map)

        # Should be valid JSON
        data = json.loads(json_content)
        assert len(data) == 1
        assert data[0]["mission_name"] == 'Mission "Apollo"'
        assert "quotes" in data[0]["details"]

    def test_generate_json_empty_list(self, export_service):
        """Test JSON generation with empty launch list."""
        json_content = export_service.generate_json([], {}, {})

        # Should be empty array
        data = json.loads(json_content)
        assert data == []

    def test_generate_json_structure(self, export_service, sample_launches):
        """Test JSON has correct structure and all required fields."""
        rocket_map = {"rocket1": "Falcon 9", "rocket2": "Falcon Heavy"}
        launchpad_map = {"pad1": "LC-39A", "pad2": "SLC-40"}

        json_content = export_service.generate_json(sample_launches, rocket_map, launchpad_map)
        data = json.loads(json_content)

        # Verify all required fields exist
        required_fields = [
            "mission_name", "date_utc", "rocket", "launchpad",
            "success", "flight_number", "details", "upcoming"
        ]

        for launch_data in data:
            for field in required_fields:
                assert field in launch_data

    def test_generate_json_formatting(self, export_service, sample_launches):
        """Test JSON is properly formatted with indentation."""
        rocket_map = {"rocket1": "Falcon 9"}
        launchpad_map = {"pad1": "LC-39A"}

        json_content = export_service.generate_json([sample_launches[0]], rocket_map, launchpad_map)

        # Should be pretty-printed (contains newlines and spaces)
        assert '\n' in json_content
        assert '  ' in json_content  # 2-space indentation


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_prepare_data_with_invalid_date_format(
        self, export_service, mock_launch_service, sample_rockets, sample_launchpads
    ):
        """Test handling of invalid date format."""
        mock_launch_service.api_client.get_all_rockets = AsyncMock(return_value=sample_rockets)
        mock_launch_service.api_client.get_all_launchpads = AsyncMock(return_value=sample_launchpads)

        # Should raise ValueError for invalid date
        with pytest.raises(ValueError):
            await export_service.prepare_launch_data(date_from="invalid-date")

    @pytest.mark.asyncio
    async def test_prepare_data_with_success_false(
        self, export_service, mock_launch_service, sample_rockets,
        sample_launchpads, sample_launches
    ):
        """Test filtering by success=false."""
        mock_launch_service.api_client.get_all_rockets = AsyncMock(return_value=sample_rockets)
        mock_launch_service.api_client.get_all_launchpads = AsyncMock(return_value=sample_launchpads)
        mock_launch_service.get_filtered_launches = AsyncMock(return_value=[])

        # Call with success=false
        await export_service.prepare_launch_data(success="false")

        # Verify filter was applied correctly
        call_args = mock_launch_service.get_filtered_launches.call_args
        filter_obj = call_args[0][0]
        # "false" (not 'true') should be converted to False
        assert filter_obj.success is False

    def test_generate_csv_with_commas_in_data(self, export_service):
        """Test CSV handles commas in data correctly."""
        launch_with_comma = Launch(
            id="launch1",
            name="Mission, Inc.",
            date_utc=datetime(2024, 1, 1, tzinfo=timezone.utc),
            rocket="rocket1",
            launchpad="pad1",
            success=True,
            flight_number=100,
            details="Details, with, commas",
            upcoming=False
        )

        rocket_map = {"rocket1": "Falcon 9"}
        launchpad_map = {"pad1": "LC-39A"}

        csv_content = export_service.generate_csv([launch_with_comma], rocket_map, launchpad_map)

        # CSV should properly quote fields with commas
        lines = csv_content.strip().split('\n')
        assert '"Mission, Inc."' in lines[1] or 'Mission, Inc.' in lines[1]
