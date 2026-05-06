DISPLAY_STATUSES = {
    "ONLINE": "Online",
    "OFFLINE": "Offline",
    "MAINTENANCE": "Maintenance",
}

DISPLAY_ORIENTATIONS = {
    "LANDSCAPE": "Landscape",
    "PORTRAIT": "Portrait",
}


def positive_int(value: str, field_label: str) -> tuple[int | None, str | None]:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None, f"{field_label} must be a whole number."

    if parsed <= 0:
        return None, f"{field_label} must be greater than zero."

    return parsed, None


def display_form_data(form) -> tuple[dict[str, object], dict[str, str]]:
    errors: dict[str, str] = {}

    name = form.get("name", "").strip()
    location = form.get("location", "").strip()
    status = form.get("status", "OFFLINE").strip()
    orientation = form.get("orientation", "LANDSCAPE").strip()
    notes = form.get("notes", "").strip()
    resolution_width, width_error = positive_int(form.get("resolution_width", ""), "Resolution width")
    resolution_height, height_error = positive_int(form.get("resolution_height", ""), "Resolution height")

    if not name:
        errors["name"] = "Display name is required."
    if status not in DISPLAY_STATUSES:
        errors["status"] = "Choose a valid display status."
    if orientation not in DISPLAY_ORIENTATIONS:
        errors["orientation"] = "Choose a valid orientation."
    if width_error:
        errors["resolution_width"] = width_error
    if height_error:
        errors["resolution_height"] = height_error

    return (
        {
            "name": name,
            "location": location or None,
            "status": status,
            "orientation": orientation,
            "resolution_width": resolution_width,
            "resolution_height": resolution_height,
            "notes": notes or None,
        },
        errors,
    )
