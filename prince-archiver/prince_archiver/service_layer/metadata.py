from datetime import UTC, datetime

{
    "metadata": {
        "application": {
            "application": "test_application",
            "version": "v0.1.0",
            "user": "test_user",
        },
        "camera": {
            "model": "test_model",
            "station_name": "test_station",
            "exposure_time": 0.01,
            "frame_rate": 10.0,
            "frame_size": (1, 1),
            "binning": "1x1",
            "gain": 1,
            "gamma": 1,
            "intensity": [0, 0, 0],
            "bits_per_pixel": 0,
        },
        "stitching": {
            "last_focused_at": datetime(2000, 1, 1, tzinfo=UTC),
            "grid_size": (1, 1),
        },
    }
}
