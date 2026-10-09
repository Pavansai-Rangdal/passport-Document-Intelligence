"""Test extraction on sample passport files."""

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.extraction import ExtractionService
from app.core.logging import configure_logging

configure_logging()


def main():
    """Test extraction on sample files."""
    sample_dir = Path(__file__).parent.parent / "sample-passports"

    if not sample_dir.exists():
        print(f"Sample directory not found: {sample_dir}")
        return

    sample_files = list(sample_dir.glob("*"))
    print(f"Found {len(sample_files)} sample files")

    extraction_service = ExtractionService()

    for sample_file in sample_files:
        print(f"\nProcessing: {sample_file.name}")
        print("-" * 50)

        try:
            result = extraction_service.extract_from_image(sample_file)

            print(f"MRZ Detected: {result['mrz_detected']}")
            print(f"OCR Engine: {result.get('ocr_engine_used', 'N/A')}")

            if result.get('quality'):
                q = result['quality']
                print(f"Dimensions: {q.get('width')}x{q.get('height')}")
                print(f"Blur Score: {q.get('blur_score', 0):.2f}")
                print(f"Brightness: {q.get('brightness', 0):.2f}")
                print(f"Quality Passed: {q.get('quality_passed', False)}")

            if result.get('mrz_data'):
                mrz = result['mrz_data']
                print(f"\nMRZ Data:")
                print(f"  Document Type: {mrz.get('document_type')}")
                print(f"  Issuing State: {mrz.get('issuing_state')}")
                print(f"  Document Number: {mrz.get('document_number')}")
                print(f"  Birth Date: {mrz.get('birth_date')}")
                print(f"  Expiry Date: {mrz.get('expiry_date')}")
                print(f"  Sex: {mrz.get('sex')}")

            if result.get('ocr_fields'):
                print(f"\nOCR Fields: {len(result['ocr_fields'])} fields extracted")

        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
