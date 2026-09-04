from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from typing import Dict, Any, Optional
import piexif
from datetime import datetime


class MetadataExtractor:
    """Extract EXIF and metadata from images"""

    @staticmethod
    def extract_exif(image_path: str) -> Dict[str, Any]:
        """Extract EXIF data from image"""
        try:
            image = Image.open(image_path)
            exif_data = image._getexif()
            
            if not exif_data:
                return MetadataExtractor._get_empty_metadata()
            
            # Parse EXIF data
            parsed_exif = {}
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                parsed_exif[tag] = value
            
            # Extract GPS data if available
            gps_data = None
            if "GPSInfo" in parsed_exif:
                gps_data = MetadataExtractor._parse_gps(parsed_exif["GPSInfo"])
            
            # Build structured metadata
            metadata = {
                "camera": {
                    "make": parsed_exif.get("Make"),
                    "model": parsed_exif.get("Model"),
                    "lens": parsed_exif.get("LensModel"),
                    "software": parsed_exif.get("Software"),
                },
                "capture": {
                    "dateTimeOriginal": parsed_exif.get("DateTimeOriginal"),
                    "createDate": parsed_exif.get("DateTime"),
                    "modifyDate": parsed_exif.get("DateTime"),
                },
                "geographic": gps_data,
                "image": {
                    "width": image.width,
                    "height": image.height,
                    "orientation": parsed_exif.get("Orientation", "Horizontal"),
                    "colorSpace": parsed_exif.get("ColorSpace", "sRGB"),
                    "resolution": f"{parsed_exif.get('XResolution', (72, 1))[0]} dpi",
                },
            }
            
            return metadata
            
        except Exception as e:
            print(f"Error extracting metadata: {e}")
            return MetadataExtractor._get_empty_metadata()

    @staticmethod
    def _parse_gps(gps_info: Dict) -> Optional[Dict[str, Any]]:
        """Parse GPS information from EXIF"""
        try:
            gps_data = {}
            for key in gps_info.keys():
                decode = GPSTAGS.get(key, key)
                gps_data[decode] = gps_info[key]
            
            # Convert GPS coordinates
            lat = MetadataExtractor._convert_to_degrees(
                gps_data.get("GPSLatitude"),
                gps_data.get("GPSLatitudeRef")
            )
            lon = MetadataExtractor._convert_to_degrees(
                gps_data.get("GPSLongitude"),
                gps_data.get("GPSLongitudeRef")
            )
            
            if lat is None or lon is None:
                return None
            
            altitude = gps_data.get("GPSAltitude")
            if altitude and isinstance(altitude, tuple):
                altitude = altitude[0] / altitude[1]
            
            return {
                "latitude": lat,
                "longitude": lon,
                "altitude": altitude,
                "gpsTimestamp": str(gps_data.get("GPSTimeStamp", "")),
            }
            
        except Exception as e:
            print(f"Error parsing GPS data: {e}")
            return None

    @staticmethod
    def _convert_to_degrees(value, ref) -> Optional[float]:
        """Convert GPS coordinates to degrees"""
        if not value:
            return None
        
        try:
            d = value[0][0] / value[0][1]
            m = value[1][0] / value[1][1]
            s = value[2][0] / value[2][1]
            
            decimal = d + (m / 60.0) + (s / 3600.0)
            
            if ref in ["S", "W"]:
                decimal = -decimal
            
            return decimal
        except Exception as e:
            print(f"Error converting GPS coordinates: {e}")
            return None

    @staticmethod
    def _get_empty_metadata() -> Dict[str, Any]:
        """Return empty metadata structure"""
        return {
            "camera": {
                "make": None,
                "model": None,
                "lens": None,
                "software": None,
            },
            "capture": {
                "dateTimeOriginal": None,
                "createDate": None,
                "modifyDate": None,
            },
            "geographic": None,
            "image": {
                "width": None,
                "height": None,
                "orientation": None,
                "colorSpace": None,
                "resolution": None,
            },
        }
