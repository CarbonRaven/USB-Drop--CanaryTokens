"""EXIF extraction and injection service for images."""

from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import piexif
import io
import logging
import random

logger = logging.getLogger(__name__)


# Camera profiles for EXIF injection
CAMERA_PROFILES: Dict[str, Dict[str, Any]] = {
    "iphone_15_pro": {
        "make": "Apple",
        "model": "iPhone 15 Pro",
        "software": "17.2",
        "lens": "iPhone 15 Pro back triple camera 6.86mm f/1.78",
        "focal_length": (686, 100),  # 6.86mm as rational
        "f_number": (178, 100),      # f/1.78 as rational
        "iso_range": (50, 800),
        "exposure_times": [(1, 60), (1, 100), (1, 125), (1, 250), (1, 500)],
    },
    "iphone_14": {
        "make": "Apple",
        "model": "iPhone 14",
        "software": "17.1",
        "lens": "iPhone 14 back dual wide camera 5.7mm f/1.5",
        "focal_length": (570, 100),
        "f_number": (150, 100),
        "iso_range": (50, 1600),
        "exposure_times": [(1, 60), (1, 100), (1, 125), (1, 250)],
    },
    "iphone_13": {
        "make": "Apple",
        "model": "iPhone 13",
        "software": "16.6",
        "lens": "iPhone 13 back dual wide camera 5.1mm f/1.6",
        "focal_length": (510, 100),
        "f_number": (160, 100),
        "iso_range": (50, 1600),
        "exposure_times": [(1, 60), (1, 100), (1, 125), (1, 250)],
    },
    "galaxy_s23": {
        "make": "samsung",
        "model": "SM-S918U",
        "software": "S918USQS3BWL1",
        "lens": "Samsung S5KHP2 f/1.7",
        "focal_length": (230, 100),
        "f_number": (170, 100),
        "iso_range": (50, 3200),
        "exposure_times": [(1, 60), (1, 100), (1, 200), (1, 400)],
    },
    "galaxy_s22": {
        "make": "samsung",
        "model": "SM-S908U",
        "software": "S908USQS4CWK3",
        "lens": "Samsung S5KHM3 f/1.8",
        "focal_length": (230, 100),
        "f_number": (180, 100),
        "iso_range": (50, 3200),
        "exposure_times": [(1, 60), (1, 100), (1, 200), (1, 400)],
    },
    "pixel_8": {
        "make": "Google",
        "model": "Pixel 8",
        "software": "14",
        "lens": "Pixel 8 back camera 6.9mm f/1.68",
        "focal_length": (690, 100),
        "f_number": (168, 100),
        "iso_range": (50, 1600),
        "exposure_times": [(1, 60), (1, 100), (1, 125), (1, 250)],
    },
    "canon_r5": {
        "make": "Canon",
        "model": "Canon EOS R5",
        "software": "Firmware Version 1.8.1",
        "lens": "RF24-105mm F4 L IS USM",
        "focal_length": (50, 1),
        "f_number": (40, 10),
        "iso_range": (100, 6400),
        "exposure_times": [(1, 125), (1, 250), (1, 500), (1, 1000)],
    },
}

# GPS locations for different scenarios
GPS_LOCATIONS: Dict[str, Tuple[float, float]] = {
    "san_francisco": (37.7749, -122.4194),
    "new_york": (40.7128, -74.0060),
    "los_angeles": (34.0522, -118.2437),
    "chicago": (41.8781, -87.6298),
    "seattle": (47.6062, -122.3321),
    "austin": (30.2672, -97.7431),
    "denver": (39.7392, -104.9903),
    "miami": (25.7617, -80.1918),
    "boston": (42.3601, -71.0589),
    "portland": (45.5152, -122.6784),
    "atlanta": (33.7490, -84.3880),
    "phoenix": (33.4484, -112.0740),
}


def _get_exif_data(image: Image.Image) -> dict:
    """Extract EXIF data from an image."""
    exif_data = {}
    try:
        exif = image._getexif()
        if exif:
            for tag_id, value in exif.items():
                tag = TAGS.get(tag_id, tag_id)
                exif_data[tag] = value
    except Exception as e:
        logger.warning(f"Failed to extract EXIF data: {e}")
    return exif_data


def _get_gps_info(exif_data: dict) -> dict:
    """Extract GPS info from EXIF data."""
    gps_info = {}
    if "GPSInfo" in exif_data:
        for key, value in exif_data["GPSInfo"].items():
            tag = GPSTAGS.get(key, key)
            gps_info[tag] = value
    return gps_info


def _convert_to_degrees(value) -> float:
    """Convert GPS coordinates to decimal degrees."""
    try:
        # Handle IFDRational objects
        if hasattr(value[0], 'numerator'):
            d = float(value[0].numerator) / float(value[0].denominator)
            m = float(value[1].numerator) / float(value[1].denominator)
            s = float(value[2].numerator) / float(value[2].denominator)
        else:
            d = float(value[0])
            m = float(value[1])
            s = float(value[2])
        return d + (m / 60.0) + (s / 3600.0)
    except Exception as e:
        logger.warning(f"Failed to convert GPS value: {e}")
        return 0.0


def extract_gps_coordinates(image_data: bytes) -> Optional[Tuple[float, float]]:
    """
    Extract GPS coordinates from image EXIF data.

    Returns:
        Tuple of (latitude, longitude) or None if not available.
    """
    try:
        image = Image.open(io.BytesIO(image_data))
        exif_data = _get_exif_data(image)
        gps_info = _get_gps_info(exif_data)

        if not gps_info:
            logger.info("No GPS info found in image")
            return None

        # Extract latitude
        if "GPSLatitude" not in gps_info or "GPSLatitudeRef" not in gps_info:
            return None

        lat = _convert_to_degrees(gps_info["GPSLatitude"])
        if gps_info["GPSLatitudeRef"] == "S":
            lat = -lat

        # Extract longitude
        if "GPSLongitude" not in gps_info or "GPSLongitudeRef" not in gps_info:
            return None

        lon = _convert_to_degrees(gps_info["GPSLongitude"])
        if gps_info["GPSLongitudeRef"] == "W":
            lon = -lon

        logger.info(f"Extracted GPS coordinates: {lat}, {lon}")
        return (lat, lon)

    except Exception as e:
        logger.error(f"Failed to extract GPS coordinates: {e}")
        return None


def extract_datetime(image_data: bytes) -> Optional[datetime]:
    """
    Extract datetime from image EXIF data.

    Returns:
        datetime object or None if not available.
    """
    try:
        image = Image.open(io.BytesIO(image_data))
        exif_data = _get_exif_data(image)

        # Try different EXIF datetime fields in order of preference
        datetime_fields = [
            "DateTimeOriginal",  # When photo was taken
            "DateTimeDigitized",  # When photo was digitized
            "DateTime",  # File modification time
        ]

        for field in datetime_fields:
            if field in exif_data:
                dt_str = exif_data[field]
                try:
                    # EXIF datetime format: "YYYY:MM:DD HH:MM:SS"
                    dt = datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
                    logger.info(f"Extracted datetime from {field}: {dt}")
                    return dt
                except ValueError:
                    continue

        logger.info("No datetime found in image EXIF")
        return None

    except Exception as e:
        logger.error(f"Failed to extract datetime: {e}")
        return None


def extract_photo_metadata(image_data: bytes) -> dict:
    """
    Extract all relevant metadata from a deployment photo.

    Returns:
        Dictionary with extracted metadata:
        - latitude: float or None
        - longitude: float or None
        - datetime: datetime or None
        - camera_make: str or None
        - camera_model: str or None
    """
    result = {
        "latitude": None,
        "longitude": None,
        "datetime": None,
        "camera_make": None,
        "camera_model": None,
    }

    try:
        image = Image.open(io.BytesIO(image_data))
        exif_data = _get_exif_data(image)

        # Extract GPS
        coords = extract_gps_coordinates(image_data)
        if coords:
            result["latitude"] = coords[0]
            result["longitude"] = coords[1]

        # Extract datetime
        result["datetime"] = extract_datetime(image_data)

        # Extract camera info
        result["camera_make"] = exif_data.get("Make")
        result["camera_model"] = exif_data.get("Model")

    except Exception as e:
        logger.error(f"Failed to extract photo metadata: {e}")

    return result


# =============================================================================
# EXIF INJECTION FUNCTIONS
# =============================================================================

def _degrees_to_exif(value: float) -> Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int]]:
    """
    Convert decimal degrees to EXIF GPS format.

    Returns:
        Tuple of ((degrees, 1), (minutes, 1), (seconds * 100, 100))
    """
    is_negative = value < 0
    value = abs(value)

    degrees = int(value)
    minutes = int((value - degrees) * 60)
    seconds = int(((value - degrees) * 60 - minutes) * 60 * 100)

    return ((degrees, 1), (minutes, 1), (seconds, 100))


def strip_exif(image_data: bytes) -> bytes:
    """
    Remove all EXIF metadata from an image.
    Useful for stripping AI generation signatures.

    Args:
        image_data: Raw image bytes

    Returns:
        Clean image bytes without EXIF data
    """
    try:
        img = Image.open(io.BytesIO(image_data))

        # Convert to RGB if necessary (removes alpha channel)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        # Re-encode without metadata
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=95)
        output.seek(0)

        return output.read()

    except Exception as e:
        logger.error(f"Failed to strip EXIF: {e}")
        return image_data


def inject_exif(
    image_data: bytes,
    camera: Optional[str] = None,
    location: Optional[Tuple[float, float]] = None,
    location_name: Optional[str] = None,
    photo_date: Optional[datetime] = None,
    add_gps_variance: bool = True,
    strip_existing: bool = True,
) -> bytes:
    """
    Inject realistic EXIF metadata into an image.

    Args:
        image_data: Raw image bytes
        camera: Camera profile name (e.g., "iphone_15_pro", "galaxy_s23")
                If None, a random camera profile is selected
        location: (latitude, longitude) tuple
                  If None and location_name provided, uses named location
                  If both None, uses random location
        location_name: Name of location from GPS_LOCATIONS
        photo_date: Date photo was taken
                    If None, generates random date 1-60 days ago
        add_gps_variance: Add slight randomness to GPS coordinates
        strip_existing: Strip existing EXIF before injecting new data

    Returns:
        Image bytes with injected EXIF data
    """
    try:
        # Optionally strip existing EXIF first
        if strip_existing:
            image_data = strip_exif(image_data)

        # Load image
        img = Image.open(io.BytesIO(image_data))

        # Ensure RGB mode
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        # Select camera profile
        if camera is None:
            camera = random.choice(list(CAMERA_PROFILES.keys()))
        cam = CAMERA_PROFILES.get(camera, CAMERA_PROFILES["iphone_15_pro"])

        # Determine location
        if location is None:
            if location_name and location_name in GPS_LOCATIONS:
                location = GPS_LOCATIONS[location_name]
            else:
                location = random.choice(list(GPS_LOCATIONS.values()))

        # Add GPS variance (small random offset ~100-500m)
        if add_gps_variance:
            lat_offset = random.uniform(-0.005, 0.005)
            lon_offset = random.uniform(-0.005, 0.005)
            location = (location[0] + lat_offset, location[1] + lon_offset)

        # Determine photo date
        if photo_date is None:
            photo_date = datetime.now() - timedelta(
                days=random.randint(1, 60),
                hours=random.randint(8, 20),  # Daytime hours
                minutes=random.randint(0, 59),
                seconds=random.randint(0, 59)
            )

        date_str = photo_date.strftime("%Y:%m:%d %H:%M:%S")

        # Select random exposure settings from camera profile
        iso = random.randint(*cam["iso_range"])
        exposure_time = random.choice(cam["exposure_times"])

        # Build EXIF dictionary
        exif_dict = {
            "0th": {
                piexif.ImageIFD.Make: cam["make"],
                piexif.ImageIFD.Model: cam["model"],
                piexif.ImageIFD.Software: cam["software"],
                piexif.ImageIFD.DateTime: date_str,
                piexif.ImageIFD.Orientation: 1,
                piexif.ImageIFD.XResolution: (72, 1),
                piexif.ImageIFD.YResolution: (72, 1),
                piexif.ImageIFD.ResolutionUnit: 2,
                piexif.ImageIFD.YCbCrPositioning: 1,
            },
            "Exif": {
                piexif.ExifIFD.DateTimeOriginal: date_str,
                piexif.ExifIFD.DateTimeDigitized: date_str,
                piexif.ExifIFD.ExifVersion: b"0232",
                piexif.ExifIFD.ComponentsConfiguration: b"\x01\x02\x03\x00",
                piexif.ExifIFD.ColorSpace: 1,
                piexif.ExifIFD.PixelXDimension: img.width,
                piexif.ExifIFD.PixelYDimension: img.height,
                piexif.ExifIFD.FocalLength: cam["focal_length"],
                piexif.ExifIFD.FNumber: cam["f_number"],
                piexif.ExifIFD.ExposureTime: exposure_time,
                piexif.ExifIFD.ISOSpeedRatings: iso,
                piexif.ExifIFD.ExposureProgram: 2,  # Normal program
                piexif.ExifIFD.MeteringMode: 5,    # Pattern
                piexif.ExifIFD.Flash: 0,           # No flash
                piexif.ExifIFD.WhiteBalance: 0,    # Auto
                piexif.ExifIFD.SceneCaptureType: 0,  # Standard
            },
            "GPS": {
                piexif.GPSIFD.GPSVersionID: (2, 3, 0, 0),
                piexif.GPSIFD.GPSLatitudeRef: "N" if location[0] >= 0 else "S",
                piexif.GPSIFD.GPSLatitude: _degrees_to_exif(location[0]),
                piexif.GPSIFD.GPSLongitudeRef: "E" if location[1] >= 0 else "W",
                piexif.GPSIFD.GPSLongitude: _degrees_to_exif(abs(location[1])),
                piexif.GPSIFD.GPSAltitudeRef: 0,
                piexif.GPSIFD.GPSAltitude: (random.randint(0, 500), 1),
                piexif.GPSIFD.GPSTimeStamp: (
                    (photo_date.hour, 1),
                    (photo_date.minute, 1),
                    (photo_date.second, 1)
                ),
                piexif.GPSIFD.GPSDateStamp: photo_date.strftime("%Y:%m:%d"),
            },
            "1st": {},
            "thumbnail": None,
        }

        # Add lens model if available
        if "lens" in cam:
            exif_dict["Exif"][piexif.ExifIFD.LensModel] = cam["lens"]

        # Generate and embed thumbnail
        try:
            thumb = img.copy()
            thumb.thumbnail((160, 120))
            thumb_io = io.BytesIO()
            thumb.save(thumb_io, format="JPEG", quality=85)
            thumb_io.seek(0)

            exif_dict["1st"] = {
                piexif.ImageIFD.Compression: 6,  # JPEG
                piexif.ImageIFD.XResolution: (72, 1),
                piexif.ImageIFD.YResolution: (72, 1),
                piexif.ImageIFD.ResolutionUnit: 2,
            }
            exif_dict["thumbnail"] = thumb_io.read()
        except Exception as e:
            logger.warning(f"Failed to generate thumbnail: {e}")

        # Dump EXIF to bytes
        exif_bytes = piexif.dump(exif_dict)

        # Save image with new EXIF
        output = io.BytesIO()
        img.save(output, format="JPEG", exif=exif_bytes, quality=95)
        output.seek(0)

        logger.info(f"Injected EXIF: camera={cam['model']}, location={location}, date={date_str}")
        return output.read()

    except Exception as e:
        logger.error(f"Failed to inject EXIF: {e}")
        return image_data


def inject_exif_batch(
    images: list,
    camera: Optional[str] = None,
    location_name: Optional[str] = None,
    base_date: Optional[datetime] = None,
    same_camera: bool = True,
    same_location: bool = True,
) -> list:
    """
    Inject EXIF into multiple images with consistent metadata.
    Useful for making a set of images appear to be from the same photo session.

    Args:
        images: List of (filename, image_data) tuples
        camera: Camera profile to use for all images
        location_name: Base location for all images
        base_date: Base date for photo session
        same_camera: Use same camera for all images
        same_location: Use same general location (with variance)

    Returns:
        List of (filename, processed_image_data) tuples
    """
    if base_date is None:
        base_date = datetime.now() - timedelta(days=random.randint(1, 60))

    if camera is None and same_camera:
        camera = random.choice(list(CAMERA_PROFILES.keys()))

    if location_name is None and same_location:
        location_name = random.choice(list(GPS_LOCATIONS.keys()))

    results = []
    for i, (filename, image_data) in enumerate(images):
        # Vary the photo date slightly (within the same day/session)
        photo_date = base_date + timedelta(
            minutes=random.randint(0, 120) + (i * 5),  # Spread out by ~5 mins each
            seconds=random.randint(0, 59)
        )

        processed = inject_exif(
            image_data,
            camera=camera if same_camera else None,
            location_name=location_name if same_location else None,
            photo_date=photo_date,
            add_gps_variance=True,
        )
        results.append((filename, processed))

    return results


def get_available_cameras() -> list:
    """Get list of available camera profiles."""
    return list(CAMERA_PROFILES.keys())


def get_available_locations() -> list:
    """Get list of available GPS locations."""
    return list(GPS_LOCATIONS.keys())
