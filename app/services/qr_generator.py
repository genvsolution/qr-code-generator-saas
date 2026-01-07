import os
import io
import re
import qrcode
from qrcode.image.pil import PilImage
from qrcode.image.svg import SvgImage
from typing import Optional, Union, Tuple

# --- Custom Exceptions ---
class QRGenerationError(Exception):
    """Custom exception for QR code generation failures."""
    pass

# --- Constants/Configuration ---
# These can be externalized to a config file (e.g., config.py) for larger applications.
DEFAULT_QR_BOX_SIZE = 10
DEFAULT_QR_BORDER = 4
DEFAULT_QR_FILL_COLOR = "black"
DEFAULT_QR_BACK_COLOR = "white"
# High error correction (approx 30% of codewords can be restored)
DEFAULT_QR_ERROR_CORRECTION = qrcode.constants.ERROR_CORRECT_H
SUPPORTED_QR_FORMATS = ['PNG', 'SVG']

class QRGeneratorService:
    """
    Encapsulates the business logic for QR code generation, including image processing
    and format handling. This service is designed to be robust and handle various
    output requirements for a commercial SaaS platform.
    """

    def __init__(self):
        """
        Initializes the QRGeneratorService.
        Currently, no specific dependencies are injected, but this constructor
        could be extended to accept configuration, logger instances, or storage
        providers if needed in the future.
        """
        pass

    def _validate_url(self, url: str) -> bool:
        """
        Performs a robust validation of the input URL.
        This regex aims to cover common valid URL patterns including http/https schemes,
        domain names (including localhost and IP addresses), optional ports, and paths.
        While comprehensive, perfect URL validation is complex and might require
        additional checks or dedicated libraries in highly sensitive contexts.

        Args:
            url (str): The URL string to validate.

        Returns:
            bool: True if the URL is valid, False otherwise.
        """
        # Regex adapted from Django's URL validator, simplified for clarity.
        # It checks for a scheme (http/https), a valid host (domain/IP/localhost),
        # an optional port, and an optional path/query/fragment.
        url_regex = re.compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return re.match(url_regex, url) is not None

    def generate_qr_code(
        self,
        url: str,
        format: str = 'PNG',
        box_size: int = DEFAULT_QR_BOX_SIZE,
        border: int = DEFAULT_QR_BORDER,
        fill_color: str = DEFAULT_QR_FILL_COLOR,
        back_color: str = DEFAULT_QR_BACK_COLOR,
        output_path: Optional[str] = None
    ) -> Union[str, bytes]:
        """
        Generates a QR code for the given URL in the specified format.

        This method handles URL validation, QR code data encoding, and renders the
        QR code into either a PNG or SVG format. It can save the generated image
        to a specified file path or return its raw byte data for in-memory processing
        or direct streaming.

        Args:
            url (str): The target URL for the QR code. Must be a valid HTTP/HTTPS URL.
            format (str): The desired output format. Currently supported: 'PNG' (default)
                          and 'SVG'. Case-insensitive.
            box_size (int): How many pixels each "box" (module) of the QR code is.
                            A larger value results in a larger image.
            border (int): How many boxes thick the border around the QR code is.
                          Minimum is 4 according to QR code standard.
            fill_color (str): The color of the QR code modules (e.g., "black", "#000000").
            back_color (str): The background color of the QR code (e.g., "white", "#FFFFFF").
            output_path (Optional[str]): If provided, the QR code will be saved to this
                                        absolute or relative file path. The necessary
                                        directories will be created if they don't exist.
                                        If None, the image data is returned as bytes.

        Returns:
            Union[str, bytes]: If `output_path` is provided, returns the absolute path
                               to the saved file (str). Otherwise, returns the raw image
                               data as bytes (PNG bytes or SVG XML bytes).

        Raises:
            QRGenerationError: If the URL is invalid, the specified format is unsupported,
                               or an error occurs during QR code generation or file I/O.
        """
        if not self._validate_url(url):
            raise QRGenerationError(
                f"Invalid URL provided: '{url}'. Please ensure it's a valid HTTP/HTTPS URL."
            )

        format = format.upper()
        if format not in SUPPORTED_QR_FORMATS:
            raise QRGenerationError(
                f"Unsupported QR code format: '{format}'. Supported formats are {', '.join(SUPPORTED_QR_FORMATS)}."
            )

        try:
            qr = qrcode.QRCode(
                version=None,  # Automatically determines the best version
                error_correction=DEFAULT_QR_ERROR_CORRECTION,
                box_size=box_size,
                border=border,
            )
            qr.add_data(url)
            qr.make(fit=True)  # Ensures the smallest possible QR code is generated

            if format == 'PNG':
                img = qr.make_image(
                    image_factory=PilImage,  # Use Pillow for PNG output
                    fill_color=fill_color,
                    back_color=back_color
                )
                if output_path:
                    # Ensure the directory for the output file exists
                    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
                    img.save(output_path, 'PNG')
                    return os.path.abspath(output_path)
                else:
                    byte_arr = io.BytesIO()
                    img.save(byte_arr, format='PNG')
                    return byte_arr.getvalue()
            elif format == 'SVG':
                img = qr.make_image(
                    image_factory=SvgImage,  # Use SVG image factory
                    fill_color=fill_color,
                    back_color=back_color
                )
                if output_path:
                    # Ensure the directory for the output file exists
                    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
                    img.save(output_path, 'SVG')
                    return os.path.abspath(output_path)
                else:
                    byte_arr = io.BytesIO()
                    img.save(byte_arr, format='SVG')
                    return byte_arr.getvalue()
            # No 'else' needed here as unsupported formats are caught earlier.

        except Exception as e:
            # Catch any unexpected errors during QR code generation or file operations
            raise QRGenerationError(f"Failed to generate QR code for URL '{url}': {e}")

# Example Usage (for demonstration and testing purposes)
if __name__ == '__main__':
    generator = QRGeneratorService()

    # Define test URLs
    valid_url_1 = "https://www.google.com/search?q=qr+code+genius+saas"
    valid_url_2 = "http://localhost:5000/dashboard"
    invalid_url = "this-is-not-a-valid-url"

    # Define an output directory for generated files
    output_directory = "temp_qr_outputs"
    os.makedirs(output_directory, exist_ok=True)
    print(f"QR codes will be saved to: {os.path.abspath(output_directory)}\n")

    # --- Test Case 1: Generate PNG to file ---
    print("--- Test Case 1: Generate PNG to file ---")
    try:
        png_filename = os.path.join(output_directory, "google_search_qr.png")
        result_path = generator.generate_qr_code(
            url=valid_url_1,
            format='PNG',
            output_path=png_filename,
            box_size=12,
            border=6,
            fill_color="darkblue",
            back_color="lightblue"
        )
        print(f"Successfully generated PNG to: {result_path}")
    except QRGenerationError as e:
        print(f"Error generating PNG: {e}")

    # --- Test Case 2: Generate SVG to file ---
    print("\n--- Test Case 2: Generate SVG to file ---")
    try:
        svg_filename = os.path.join(output_directory, "localhost_dashboard_qr.svg")
        result_path = generator.generate_qr_code(
            url=valid_url_2,
            format='SVG',
            output_path=svg_filename,
            fill_color="green",
            back_color="white"
        )
        print(f"Successfully generated SVG to: {result_path}")
    except QRGenerationError as e:
        print(f"Error generating SVG: {e}")

    # --- Test Case 3: Generate PNG in-memory (bytes) ---
    print("\n--- Test Case 3: Generate PNG in-memory ---")
    try:
        png_bytes = generator.generate_qr_code(
            url=valid_url_1,
            format='PNG',
            box_size=8
        )
        print(f"Successfully generated PNG in-memory. Bytes length: {len(png_bytes)}")
        # You can now stream these bytes directly in a web response or upload to cloud storage
        # Example: with open(os.path.join(output_directory, "in_memory_qr.png"), "wb") as f: f.write(png_bytes)
    except QRGenerationError as e:
        print(f"Error generating in-memory PNG: {e}")

    # --- Test Case 4: Generate SVG in-memory (bytes) ---
    print("\n--- Test Case 4: Generate SVG in-memory ---")
    try:
        svg_bytes = generator.generate_qr_code(
            url=valid_url_2,
            format='SVG'
        )
        print(f"Successfully generated SVG in-memory. Bytes length: {len(svg_bytes)}")
        # Example: with open(os.path.join(output_directory, "in_memory_qr.svg"), "wb") as f: f.write(svg_bytes)
    except QRGenerationError as e:
        print(f"Error generating in-memory SVG: {e}")

    # --- Test Case 5: Invalid URL ---
    print("\n--- Test Case 5: Invalid URL ---")
    try:
        generator.generate_qr_code(
            url=invalid_url,
            format='PNG',
            output_path=os.path.join(output_directory, "invalid_url_qr.png")
        )
    except QRGenerationError as e:
        print(f"Caught expected error for invalid URL: {e}")

    # --- Test Case 6: Unsupported Format ---
    print("\n--- Test Case 6: Unsupported Format ---")
    try:
        generator.generate_qr_code(
            url=valid_url_1,
            format='JPG',  # Unsupported format
            output_path=os.path.join(output_directory, "unsupported_format_qr.jpg")
        )
    except QRGenerationError as e:
        print(f"Caught expected error for unsupported format: {e}")

    # Optional: Clean up the temporary directory
    # import shutil
    # if os.path.exists(output_directory):
    #     shutil.rmtree(output_directory)
    #     print(f"\nCleaned up temporary directory: {output_directory}")