# SpaceX Launch Tracker

A FastAPI-based application for tracking and analyzing SpaceX launches using the public SpaceX API v4.

## Features

- **Web Interface**: Simple, user-friendly web interface to browse launches and view statistics
- **RESTful API**: Full API endpoints for programmatic access
- **Launch Data Management**: Fetch and cache launch data from SpaceX API
- **Advanced Filtering**: Filter launches by date range, rocket, success status, and launchpad
- **Data Export**: Export filtered launch data to CSV or JSON formats with automatic pagination
- **Webhook Notifications**: Real-time notifications when new SpaceX launches are detected
- **Statistical Analysis**:
  - Success rates by rocket
  - Launch counts by launchpad
  - Launch frequency (monthly and yearly)
  - Overall statistics
- **Efficient Caching**: File-based caching to minimize API calls
- **Type Safety**: Full type hints with Pydantic models
- **Comprehensive Testing**: Unit tests for all core functionality

## Project Structure

```
spacex_launch_tracker/
├── app/
│   ├── models/              # Pydantic data models
│   │   ├── launch.py       # Launch and filter models
│   │   ├── rocket.py       # Rocket models
│   │   └── launchpad.py    # Launchpad models
│   ├── lib/                # External libraries/API clients
│   │   └── spacex_api.py   # SpaceX API client
│   ├── services/           # Business logic layer
│   │   ├── cache_service.py      # Caching implementation
│   │   ├── launch_service.py     # Launch operations
│   │   ├── stats_service.py      # Statistics calculations
│   │   ├── export_service.py     # Data export operations
│   │   ├── webhook_manager.py    # Webhook management
│   │   └── background_service.py # Background task scheduler
│   ├── controllers/        # FastAPI route handlers
│   │   ├── launch_controller.py  # Launch API endpoints
│   │   ├── stats_controller.py   # Statistics API
│   │   ├── web_controller.py     # Web interface routes
│   │   └── webhook_controller.py # Webhook API endpoints
│   ├── templates/          # Jinja2 HTML templates
│   │   ├── base.html       # Base template
│   │   ├── home.html       # Home page
│   │   ├── launches.html   # Launches list page
│   │   └── statistics.html # Statistics page
│   ├── data/               # Data storage (gitignored)
│   │   ├── webhooks.json   # Webhook subscriptions
│   │   └── launches_cache.json # Launch tracking cache
│   ├── config.py          # Application configuration
│   └── main.py            # FastAPI app initialization
├── tests/                 # Test suite (mirrors main structure)
│   ├── test_lib/          # API client tests
│   ├── test_services/     # Business logic tests
│   ├── test_controllers/  # Controller tests
│   └── conftest.py        # Pytest configuration & fixtures
├── requirements.txt       # Python dependencies
├── pytest.ini            # Pytest configuration
└── README.md             # This file
```

## Requirements

- Python 3.8+
- Dependencies listed in `requirements.txt`

Key dependencies:
- **FastAPI** - Web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation
- **httpx** - Async HTTP client
- **schedule** - Background task scheduling (for webhooks)
- **requests** - HTTP library (for webhook delivery)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd spacex_launch_tracker
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment (optional)**
   ```bash
   cp .env.example .env
   # Edit .env to customize settings
   ```

## Running the Application

**Start the development server:**
```bash
uvicorn app.main:app --reload
```

The application will be available at `http://localhost:8000`

### Access Points

**Web Interface (Recommended for browsing):**
- Home: `http://localhost:8000/`
- Browse Launches: `http://localhost:8000/web/launches`
- View Statistics: `http://localhost:8000/web/statistics`

**API Documentation (For developers):**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Using the Web Interface

The web interface provides an easy way to explore SpaceX launch data without writing code.

### Features

1. **Home Page** (`/`)
   - Overview of application features
   - Quick links to launches and statistics

2. **Launches Page** (`/web/launches`)
   - Browse all SpaceX launches in a table format
   - **Filters:**
     - Rocket name (e.g., "Falcon 9", "Falcon Heavy")
     - Launchpad name (e.g., "LC-39A")
     - Success status (Successful/Failed)
     - Date range (From/To dates)
   - Real-time filtering with "Apply Filters" button
   - Color-coded status badges (Success/Failed/Upcoming)
   - Shows mission name, date, rocket, launchpad, and flight number
   - **Export Data:**
     - Export to CSV format (includes all fields: mission name, date, rocket, launchpad, status, flight number, details)
     - Export to JSON format (structured data with all launch properties)
     - Exports respect current filters (only exports filtered results)
     - Automatic pagination handles large datasets (>1000 launches)
     - Timestamped filenames (e.g., `spacex_launches_20240115_143022.csv`)

3. **Statistics Page** (`/web/statistics`)
   - **Overall Statistics:**
     - Total launches
     - Successful launches
     - Failed launches
     - Overall success rate
   - **Success Rate by Rocket:**
     - Launch counts per rocket
     - Success rates with color coding
   - **Launchpad Statistics:**
     - Launch counts per launchpad
     - Success rates
   - **Launch Frequency:**
     - Launches by year
     - Launches by month (last 12 months)

### Implementation Details

The web interface is built using:
- **Backend**: FastAPI with Jinja2 templates
- **Frontend**: Server-side rendered HTML with inline CSS
- **Styling**: Clean, modern design with responsive layout
- **Data**: Same backend services as the API (cached SpaceX data)

**Key Files:**
- `app/controllers/web_controller.py` - Web route handlers
- `app/services/export_service.py` - Export data processing
- `app/templates/` - HTML templates with Jinja2
- `app/main.py` - Template configuration and home route

## Data Export

The application provides robust data export functionality to download launch data in CSV or JSON formats.

### Export Features

- **Multiple Formats**: Export data as CSV (spreadsheet-compatible) or JSON (structured data)
- **Filter Preservation**: Exports only include launches matching your current filters
- **Large Dataset Support**: Automatic pagination handles datasets larger than 1000 launches
- **Complete Data**: Includes all launch details (mission name, date, rocket, launchpad, success status, flight number, details)
- **Timestamped Files**: Each export has a unique timestamp in the filename for easy organization

### Export Endpoints

**GET `/web/export/launches/csv`** - Export launches to CSV

Query Parameters (all optional):
- `rocket_name` (string): Filter by rocket name
- `launchpad_name` (string): Filter by launchpad name
- `success` (string): Filter by success status ("true" or "false")
- `date_from` (string): Start date (ISO format: YYYY-MM-DD)
- `date_to` (string): End date (ISO format: YYYY-MM-DD)

Example:
```bash
# Export all successful Falcon 9 launches in 2023
curl "http://localhost:8000/web/export/launches/csv?rocket_name=Falcon%209&success=true&date_from=2023-01-01&date_to=2023-12-31" -o launches.csv
```

**GET `/web/export/launches/json`** - Export launches to JSON

Same query parameters as CSV endpoint.

Example:
```bash
# Export all launches from LC-39A
curl "http://localhost:8000/web/export/launches/json?launchpad_name=LC-39A" -o launches.json
```

### CSV Format

CSV exports include the following columns:
- Mission Name
- Date (UTC)
- Rocket
- Launchpad
- Success (Success/Failed/Upcoming)
- Flight Number
- Details

### JSON Format

JSON exports include the following fields per launch:
```json
{
  "mission_name": "Starlink Mission",
  "date_utc": "2024-01-15T10:30:00+00:00",
  "rocket": "Falcon 9",
  "launchpad": "LC-39A",
  "success": true,
  "flight_number": 100,
  "details": "Successful Starlink deployment",
  "upcoming": false
}
```

### Using Export from Web Interface

1. Navigate to `/web/launches`
2. Apply any desired filters (rocket, launchpad, date range, success status)
3. Click "Export to CSV" or "Export to JSON" button
4. File downloads automatically with timestamped filename

### Technical Implementation

- **Pagination**: ExportService automatically handles API pagination to fetch all matching launches
- **Memory Efficient**: Uses streaming response to handle large exports without loading entire dataset into memory
- **Data Mapping**: Converts rocket/launchpad IDs to human-readable names
- **Error Handling**: Returns JSON error response if export fails

## Webhook Notifications

The application includes a simple webhook notification system that sends HTTP POST requests when new SpaceX launches are detected.

### How It Works

- A background task checks for new launches every 5 seconds (configurable)
- When a new launch is detected, registered webhooks receive a POST request
- No external dependencies required - uses Python's built-in `threading` and `schedule` library
- Data stored in JSON files (`app/data/webhooks.json` and `app/data/launches_cache.json`)

### Webhook Endpoints

**POST `/webhooks`** - Register a new webhook

Request:
```json
{
  "url": "https://your-webhook-url.com/endpoint",
  "description": "My webhook description"
}
```

Response:
```json
{
  "id": 1,
  "url": "https://your-webhook-url.com/endpoint",
  "description": "My webhook description",
  "active": true,
  "created_at": "2026-01-05T12:00:00"
}
```

**GET `/webhooks`** - List all webhooks

Query Parameters:
- `active_only` (boolean): Only return active webhooks (default: false)

**DELETE `/webhooks/{webhook_id}`** - Delete a webhook

### Webhook Payload

When a new launch is detected, your endpoint receives:

```json
{
  "event": "new_launch",
  "timestamp": "2026-01-05T12:00:00",
  "launch": {
    "id": "5eb87cd9ffd86e000604b32a",
    "name": "FalconSat",
    "date_utc": "2006-03-24T22:30:00.000Z",
    "success": false,
    "upcoming": false,
    "details": "Engine failure at 33 seconds...",
    "flight_number": 1
  }
}
```

### Usage Example

```bash
# Register a webhook
curl -X POST http://localhost:8000/webhooks \
  -H "Content-Type: application/json" \
  -d '{"url": "https://webhook.site/your-unique-id"}'

# List webhooks
curl http://localhost:8000/webhooks

# Delete webhook
curl -X DELETE http://localhost:8000/webhooks/1
```

### Configuration

The background task runs **every 5 seconds** by default (for testing). To change the interval, edit `app/services/background_service.py`:

```python
schedule.every(5).seconds.do(check_new_launches)  # Change to .minutes, .hours, etc.
# For production, use: schedule.every(1).hours.do(check_new_launches)
```

### Testing

1. Use [webhook.site](https://webhook.site) to get a test URL
2. Register the webhook URL
3. Add a test launch or restart the app
4. Check webhook.site for incoming requests

## API Endpoints

### Launches

**GET `/launches/`** - Get filtered list of launches

Query Parameters:
- `date_from` (datetime): Start date filter
- `date_to` (datetime): End date filter
- `rocket_name` (string): Filter by rocket name
- `success` (boolean): Filter by success status
- `launchpad_name` (string): Filter by launchpad name
- `limit` (int): Maximum results (default: 100, max: 1000)
- `offset` (int): Results offset (default: 0)

Example:
```bash
curl "http://localhost:8000/launches/?success=true&rocket_name=Falcon%209&limit=10"
```

**GET `/launches/{launch_id}`** - Get specific launch by ID

Example:
```bash
curl "http://localhost:8000/launches/5eb87cd9ffd86e000604b32a"
```

### Statistics

**GET `/stats/success-rate`** - Success rate by rocket

Returns total launches, successful launches, failed launches, and success rate percentage for each rocket.

**GET `/stats/launchpads`** - Launch counts by launchpad

Returns total and successful launch counts for each launchpad.

**GET `/stats/frequency`** - Launch frequency

Returns launch counts grouped by month and year.

**GET `/stats/overall`** - Overall statistics

Returns total launches, successes, failures, upcoming launches, and overall success rate.

## Running Tests

**Run all tests:**
```bash
pytest
```

**Run with coverage report:**
```bash
pytest --cov=app --cov-report=html
```

**Run specific test file:**
```bash
pytest tests/test_lib/test_spacex_api.py
```

**Run specific test:**
```bash
pytest tests/test_lib/test_spacex_api.py::TestSpaceXAPIClient::test_get_all_launches_success
```

## Configuration

Configuration is managed through environment variables or `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `SPACEX_API_BASE_URL` | SpaceX API base URL | `https://api.spacexdata.com/v4` |
| `API_TIMEOUT` | API request timeout (seconds) | `30` |
| `CACHE_TTL_SECONDS` | Cache time-to-live | `3600` (1 hour) |
| `CACHE_ENABLED` | Enable/disable caching | `True` |
| `APP_NAME` | Application name | `SpaceX Launch Tracker` |
| `DEBUG` | Debug mode | `False` |

## Architecture

### Models Layer
Pydantic models for data validation and serialization:
- Type-safe data structures
- Automatic validation
- JSON schema generation

### Library Layer
External API clients and integrations:
- **SpaceXAPIClient**: HTTP client for SpaceX API with caching

### Services Layer
Business logic and data operations:
- **LaunchService**: Manages launch data retrieval and filtering
- **StatsService**: Calculates statistical metrics
- **ExportService**: Handles data export to CSV/JSON formats with pagination
- **CacheService**: File-based caching implementation
- **WebhookManager**: Manages webhook subscriptions and data storage
- **BackgroundService**: Periodic task scheduler for webhook notifications

### Controllers Layer
FastAPI route handlers:
- Thin layer between HTTP and services
- Request validation
- Error handling
- Dependency injection

## Caching

The application implements file-based caching with automatic cleanup:
- Cached data stored in `.cache/` directory
- Default TTL: 1 hour (configurable)
- **Automatic cleanup**: Expired and corrupted files are deleted on read
- Reduces API calls and improves performance
- No stale files accumulate on disk
- **Test isolation**: Tests use disabled cache (via `tests/conftest.py`) to prevent pollution of production cache

## Error Handling

Robust error handling throughout:
- API errors return HTTP 503 (Service Unavailable)
- Not found errors return HTTP 404
- Internal errors return HTTP 500
- Graceful cache failures (continues without cache)

## Testing Strategy

Comprehensive test coverage with cache isolation:
- **Service tests**: Mock API calls, test business logic
- **Controller tests**: Test HTTP endpoints and error handling
- **Integration tests**: Verify component interactions
- **Fixtures**: Reusable test data and mocks
- **Cache isolation**: Tests automatically disable caching (via `conftest.py`) to prevent polluting production cache
  - Most tests: `cache_enabled=False` (no file I/O)
  - Cache-specific tests: Use `tmp_path` (temporary directory)
  - Production cache remains clean and unaffected by tests

## Development

**Project follows clean code principles:**
- Separation of concerns (models, services, controllers)
- Single responsibility for each function
- Type hints throughout
- Concise, meaningful comments
- No long functions or classes

**Code style:**
- Follow PEP 8
- Use type hints
- Keep functions under 50 lines
- One class per file (where applicable)

## License

This project is created for educational purposes.

## Acknowledgments

- SpaceX API: https://github.com/r-spacex/SpaceX-API
- FastAPI: https://fastapi.tiangolo.com/
- Pydantic: https://pydantic-docs.helpmanual.io/
