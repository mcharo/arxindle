import argparse
import logging
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

import requests

log = logging.getLogger(__name__)

# Matches ArXiv IDs in new format: YYMM.NNNNN (e.g., 2301.00001)
# Optionally with version suffix (e.g., v1, v2)
ARXIV_ID_PATTERN = re.compile(
    r"""
    (?:                     # Optional URL prefix (non-capturing)
        https?://           # http:// or https://
        (?:www\.)?          # optional www.
        arxiv\.org/         # arxiv.org/
        (?:abs|pdf|e-print)/ # abs/, pdf/, or e-print/
    )?
    (?P<id>                 # Capture the ID
        \d{4}               # 4-digit year+month (YYMM)
        \.                  # literal dot
        \d{4,5}             # 4-5 digit paper number
        (?:v\d{1,2})?       # optional version (v1, v12, etc.)
    )
    """,
    re.VERBOSE,
)


def parse_arxiv_id(url_or_id: str) -> str:
    """
    Extract ArXiv paper ID from a URL or raw ID string.

    Accepts:
        - Raw ID: "2301.00001", "2301.00001v2"
        - Full URL: "https://arxiv.org/abs/2301.00001"
        - PDF URL: "https://arxiv.org/pdf/2301.00001"

    Returns:
        The paper ID (e.g., "2301.00001" or "2301.00001v2")

    Raises:
        ValueError: If the input doesn't contain a valid ArXiv ID
    """
    match = ARXIV_ID_PATTERN.search(url_or_id.strip())
    if not match:
        raise ValueError(
            f"Invalid ArXiv URL or ID: {url_or_id!r}\n"
            f"Expected format: YYMM.NNNNN (e.g., 2301.00001) or full arxiv.org URL"
        )
    return match.group("id")


class Arxiv2KindleConverter:
    def __init__(self, arxiv_url: str, is_landscape: bool) -> None:
        self.arxiv_url = arxiv_url
        self.is_landscape = is_landscape
        self.check_prerequisite()

    def check_prerequisite(self):
        result = subprocess.run(
            ["pdflatex", "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if result.returncode != 0:
            raise SystemError("pdflatex not found - please install TeX Live")
        if self.is_landscape:
            result = subprocess.run(
                ["pdftk", "--version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if result.returncode != 0:
                raise SystemError("pdftk not found (required for landscape mode)")

    def download_source(self, work_dir: Path) -> tuple[str, str]:
        """Download and extract ArXiv source to work_dir. Returns (arxiv_id, arxiv_title)."""
        arxiv_id = parse_arxiv_id(self.arxiv_url)
        arxiv_abs = f"https://arxiv.org/abs/{arxiv_id}"

        log.debug(f"Fetching metadata from {arxiv_abs}")
        response = requests.get(arxiv_abs)
        response.raise_for_status()

        # Extract title from HTML (e.g., "[2301.00001] Paper Title Here")
        title_match = re.search(r"<title>([^<]+)</title>", response.text)
        if not title_match:
            raise ValueError(f"Could not extract title from {arxiv_abs}")

        # Remove the "[XXXX.XXXXX] " prefix from the title
        arxiv_pgtitle = title_match.group(1)
        arxiv_title = re.sub(r"^\[[^\]]+\]\s*", "", arxiv_pgtitle)
        arxiv_title = re.sub(r"\s+", " ", arxiv_title).strip()

        archive_url = f"https://arxiv.org/e-print/{arxiv_id}"
        tar_path = work_dir / f"{arxiv_title}.tar.gz"

        log.info(f"Downloading {arxiv_id}...")
        log.debug(f"Archive URL: {archive_url}")
        response = requests.get(archive_url, stream=True)
        response.raise_for_status()

        with open(tar_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        log.debug(f"Extracting to {work_dir}")
        with tarfile.open(tar_path) as f:
            f.extractall(work_dir)

        return arxiv_id, arxiv_title

    def process_tex(self, work_dir: Path, geometric_settings: dict) -> Path:
        """Process and compile the TeX file. Returns path to generated PDF."""
        # Neutralize geometry and column settings in local .sty and .cls files
        for styfile in list(work_dir.glob("*.sty")) + list(work_dir.glob("*.cls")):
            log.debug(f"Processing: {styfile.name}")
            sty_content = styfile.read_text()

            # Comment out geometry package loading and newgeometry calls
            sty_content = re.sub(
                r"\\usepackage(\[[^\]]*\])?\{geometry\}",
                "% geometry disabled by arxindle",
                sty_content,
            )
            sty_content = re.sub(
                r"\\newgeometry\s*\{[^}]*\}",
                "% newgeometry disabled by arxindle",
                sty_content,
                flags=re.DOTALL,
            )
            sty_content = re.sub(
                r"\\geometry\s*\{[^}]*\}",
                "% geometry disabled by arxindle",
                sty_content,
                flags=re.DOTALL,
            )
            sty_content = re.sub(
                r"\\RequirePackage(\[[^\]]*\])?\{geometry\}",
                "% geometry disabled by arxindle",
                sty_content,
            )

            # Replace \twocolumn with \onecolumn in style files
            # If \twocolumn has an optional arg like [\@maketitle], preserve the content
            def replace_twocolumn(m):
                if m.group(1):
                    # Extract content from [...] and execute it after \onecolumn
                    content = m.group(1)[1:-1]  # Strip the brackets
                    return f"\\onecolumn {content}"
                return "\\onecolumn"

            sty_content = re.sub(
                r"\\twocolumn(\s*\[[^\]]*\])?",
                replace_twocolumn,
                sty_content,
            )
            # Comment out package error checks that would block geometry
            # These are typically in \@ifpackageloaded{geometry}{ERROR}{} blocks
            sty_content = re.sub(
                r"(\\@ifpackageloaded\{geometry\})",
                r"% \1",
                sty_content,
            )
            # Also disable any direct PackageError about geometry
            sty_content = re.sub(
                r"(\\PackageError\{[^}]*\}\{[^}]*geometry[^}]*\}\{[^}]*\})",
                r"% \1",
                sty_content,
                flags=re.IGNORECASE,
            )
            styfile.write_text(sty_content)

        # Find the main tex file (contains \documentclass)
        texfile = None
        for candidate in work_dir.glob("*.tex"):
            first_line = candidate.read_text().split("\n")[0]
            if "documentclass" in first_line:
                texfile = candidate
                break

        if texfile is None:
            raise FileNotFoundError("No main .tex file found (no \\documentclass)")

        log.info(f"Processing: {texfile.name}")

        src = texfile.read_text().split("\n")

        # Filter comments/newlines for easier processing
        src = [line for line in src if not line.startswith("%") and line.strip()]

        # Strip font size, column, and paper size from documentclass line
        src[0] = re.sub(r"\b\d+pt\b", "", src[0])
        src[0] = re.sub(r"\b\w+column\b", "", src[0])
        src[0] = re.sub(r"\b\w+paper\b", "", src[0])
        src[0] = re.sub(r"(?<=\[),", "", src[0])  # remove starting commas
        src[0] = re.sub(r",(?=[\],])", "", src[0])  # remove trailing commas

        # Add onecolumn option to documentclass if it has options
        if re.search(r"\\documentclass\s*\[", src[0]):
            src[0] = re.sub(r"(\\documentclass\s*\[)", r"\1onecolumn,", src[0])
        else:
            # No options yet, add them
            src[0] = re.sub(r"(\\documentclass)\s*(\{)", r"\1[onecolumn]\2", src[0])

        # Comment out \newgeometry and \twocolumn calls
        for i in range(len(src)):
            src[i] = re.sub(
                r"\\newgeometry\s*\{[^}]*\}",
                "% newgeometry disabled by arxindle",
                src[i],
            )

            # Replace \twocolumn with \onecolumn, preserving optional arg content
            def replace_twocolumn_tex(m):
                if m.group(1):
                    content = m.group(1).strip()[1:-1]  # Strip whitespace and brackets
                    return f"\\onecolumn {content}"
                return "\\onecolumn"

            src[i] = re.sub(
                r"\\twocolumn(\s*\[[^\]]*\])?",
                replace_twocolumn_tex,
                src[i],
            )

        # Find \begin{document}
        begindocs = [i for i, line in enumerate(src) if line.startswith(r"\begin{document}")]
        if len(begindocs) != 1:
            raise ValueError(f"Expected 1 \\begin{{document}}, found {len(begindocs)}")

        # Insert our geometry settings (reverse order since same position)
        geometry_str = ",".join(f"{k}={v}" for k, v in geometric_settings.items())
        log.debug(f"Applying geometry: {geometry_str}")
        src.insert(begindocs[0], f"\\geometry{{{geometry_str}}}\n")
        src.insert(
            begindocs[0],
            "\\makeatletter\\@ifpackageloaded{geometry}{}{\\usepackage{geometry}}\\makeatother\n",
        )
        src.insert(begindocs[0], "\\usepackage{times}\n")
        src.insert(begindocs[0], "\\pagestyle{empty}\n")

        if self.is_landscape:
            src.insert(begindocs[0], "\\usepackage{pdflscape}\n")

        # Scale images to fit the page
        for i in range(len(src)):
            src[i] = re.sub(
                r"\\includegraphics\[width=([.\d]+)\\(line|text)width\]",
                lambda m: f"\\includegraphics[width={m.group(1)}\\textwidth,height={m.group(1)}\\textheight,keepaspectratio]",  # noqa: E501
                src[i],
            )

        # Backup original and write modified version
        shutil.copy(texfile, texfile.with_suffix(".tex.bak"))
        texfile.write_text("\n".join(src))

        # Compile with pdflatex
        self._compile_latex(work_dir, texfile)

        pdf_file = work_dir / f"{texfile.stem}.pdf"
        if not pdf_file.exists():
            raise FileNotFoundError(f"PDF was not generated: {pdf_file}")

        return pdf_file

    def _compile_latex(self, work_dir: Path, texfile: Path) -> None:
        """Run pdflatex and bibtex to compile the document."""
        pdflatex_cmd = ["pdflatex", "-interaction=nonstopmode", texfile.name]
        texbase = texfile.stem

        # Suppress output unless debug logging is enabled
        if log.isEnabledFor(logging.DEBUG):
            stdout = None  # show output
        else:
            stdout = subprocess.DEVNULL

        log.info("Compiling LaTeX (pass 1/3)...")
        subprocess.run(pdflatex_cmd, stdout=stdout, stderr=stdout, cwd=work_dir)

        # Run bibtex if needed
        bbl_file = work_dir / f"{texbase}.bbl"
        if list(work_dir.glob("*.bib")) or bbl_file.exists():
            log.debug("Running bibtex...")
            subprocess.run(["bibtex", texbase], stdout=stdout, stderr=stdout, cwd=work_dir)

        log.info("Compiling LaTeX (pass 2/3)...")
        subprocess.run(pdflatex_cmd, stdout=stdout, stderr=stdout, cwd=work_dir)

        log.info("Compiling LaTeX (pass 3/3)...")
        subprocess.run(pdflatex_cmd, stdout=stdout, stderr=stdout, cwd=work_dir)

    def convert(self, output: Path, width: int, height: int, margin: float) -> None:
        """Convert ArXiv paper and save to output path."""
        if self.is_landscape:
            width, height = height, width

        geometric_settings = {
            "paperwidth": f"{width}in",
            "paperheight": f"{height}in",
            "margin": f"{margin}in",
        }

        with tempfile.TemporaryDirectory(prefix="arxindle_") as tmp:
            work_dir = Path(tmp)
            _, arxiv_title = self.download_source(work_dir)
            log.info(f"Title: {arxiv_title}")

            pdf_file = self.process_tex(work_dir, geometric_settings)
            shutil.copy(pdf_file, output)

        log.info(f"Conversion complete! PDF saved to: {output.resolve()}")
        log.info("Send to Kindle at: https://www.amazon.com/sendtokindle")


def setup_logging(verbose: bool) -> None:
    """Configure logging based on verbosity level."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s" if not verbose else "%(levelname)s: %(message)s",
    )


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Convert ArXiv papers to Kindle-friendly PDFs")
    parser.add_argument("-u", "--url", required=True, metavar="URL", help="ArXiv URL or paper ID")
    parser.add_argument("-o", "--output", required=True, metavar="PATH", help="Output PDF path")
    parser.add_argument(
        "-W", "--width", type=int, default=4, help="Page width in inches (default: 4)"
    )
    parser.add_argument(
        "-H", "--height", type=int, default=6, help="Page height in inches (default: 6)"
    )
    parser.add_argument(
        "-m",
        "--margin",
        type=float,
        default=0.2,
        help="Page margin in inches (default: 0.2)",
    )
    parser.add_argument(
        "-l", "--landscape", action="store_true", help="Enable landscape orientation"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed output including LaTeX logs",
    )

    args = parser.parse_args(argv)
    setup_logging(args.verbose)

    if not 0.0 < args.margin < 1.0:
        parser.error("Margin must be between 0 and 1")

    output_path = Path(args.output)
    if not output_path.suffix:
        output_path = output_path.with_suffix(".pdf")

    try:
        converter = Arxiv2KindleConverter(args.url, args.landscape)
        converter.convert(output_path, args.width, args.height, args.margin)
    except (ValueError, SystemError, FileNotFoundError) as e:
        log.error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
