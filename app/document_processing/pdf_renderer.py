"""PDF rendering for processing PDF documents."""

from pathlib import Path

import pymupdf  # PyMuPDF

from app.core.logging import get_logger

logger = get_logger(__name__)


class PDFRenderer:
    """Renders PDF pages to images for processing."""

    @staticmethod
    def render_page_to_image(
        pdf_path: Path,
        page_num: int,
        output_path: Path,
        dpi: int = 200,
        format: str = "png",
    ) -> bool:
        """Render a single PDF page to an image."""
        try:
            doc = pymupdf.open(str(pdf_path))
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=dpi)

            if format.lower() == "png":
                pix.save(str(output_path))
            elif format.lower() == "jpeg":
                pix.save(str(output_path), jpegquality=95)  # type: ignore
            else:
                pix.save(str(output_path))

            doc.close()
            logger.info("PDF page rendered", page_num=page_num, output_path=str(output_path))
            return True
        except Exception as e:
            logger.error("Failed to render PDF page", error=str(e))
            return False

    @staticmethod
    def get_page_count(pdf_path: Path) -> int:
        """Get the number of pages in a PDF."""
        try:
            doc = pymupdf.open(str(pdf_path))
            count = doc.page_count
            doc.close()
            return count
        except Exception as e:
            logger.error("Failed to get PDF page count", error=str(e))
            return 0

    @staticmethod
    def render_all_pages(
        pdf_path: Path,
        output_dir: Path,
        dpi: int = 200,
        format: str = "png",
    ) -> list[Path]:
        """Render all PDF pages to images."""
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            page_count = PDFRenderer.get_page_count(pdf_path)
            rendered_paths = []

            for page_num in range(page_count):
                output_path = output_dir / f"page_{page_num + 1}.{format}"
                if PDFRenderer.render_page_to_image(pdf_path, page_num, output_path, dpi, format):
                    rendered_paths.append(output_path)

            logger.info("All PDF pages rendered", count=len(rendered_paths))
            return rendered_paths
        except Exception as e:
            logger.error("Failed to render PDF pages", error=str(e))
            return []
