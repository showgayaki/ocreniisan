from logging import getLogger
from pathlib import Path
import cv2


logger = getLogger('ocr')


def comporess_file_size(original_image_path: Path) -> None:
    logger.info('Compress image.')
    original_image_size = format_file_size(original_image_path)
    image = cv2.imread(str(original_image_path))
    cv2.imwrite(str(original_image_path), image, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
    compressed_image_size = format_file_size(original_image_path)
    logger.info(f'Compressed: {original_image_size} -> {compressed_image_size}')


def format_file_size(file_path: Path) -> str:
    """
    Format the size of a file into a human-readable string with appropriate units.

    Parameters:
        file_path (str or Path): The path to the file.

    Returns:
        str: Formatted file size with units (e.g., '10.5 MB').
    """
    file = Path(file_path)

    if not file.is_file():
        raise FileNotFoundError(f'The file [{file_path}] does not exist or is not a file.')

    size_in_bytes = file.stat().st_size
    units = ['B', 'KB', 'MB', 'GB', 'TB']

    size = size_in_bytes
    unit_index = 0

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    return f'{size:.1f} {units[unit_index]}'
