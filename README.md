# arxindle

Convert ArXiv papers to Kindle-friendly PDFs. arxindle downloads the LaTeX source from ArXiv and recompiles it with optimized formatting for e-readers like the Kindle.

## Features

- **Reformats for e-readers**: Converts papers to fit small screens (default 4×6 inches)
- **Full fidelity**: Renders images, diagrams, tables, and formulae correctly
- **Single-column layout**: Converts 2-column academic formats into readable single-column
- **Landscape mode**: Optional landscape orientation for wider content

## Prerequisites

You'll need these tools installed on your system:

- **pdflatex** (required): For compiling LaTeX to PDF
  - macOS: `brew install --cask mactex` or `brew install basictex`
  - Ubuntu/Debian: `sudo apt install texlive-latex-base`
  
- **pdftk** (optional, for landscape mode only):
  - macOS: `brew install pdftk-java`
  - Ubuntu/Debian: `sudo apt install pdftk`

### TeX Live Packages

If you installed a minimal TeX distribution (like `basictex`), you may need additional packages for some papers. Install them with `tlmgr`:

```bash
# Recommended: Install common package collections
sudo tlmgr install collection-latexrecommended collection-fontsrecommended

# For most ArXiv papers, also install:
sudo tlmgr install collection-latexextra   # algorithms, listings, etc.
sudo tlmgr install ieeetran                # IEEE conference papers
sudo tlmgr install acmart                  # ACM conference papers
```

**Common missing packages and their fixes:**

| Error | Fix |
|-------|-----|
| `IEEEtran.cls not found` | `sudo tlmgr install ieeetran` |
| `acmart.cls not found` | `sudo tlmgr install acmart` |
| `algorithm2e.sty not found` | `sudo tlmgr install algorithm2e` |
| `nicefrac.sty not found` | `sudo tlmgr install units` |
| `threeparttable.sty not found` | `sudo tlmgr install threeparttable` |
| `lipsum.sty not found` | `sudo tlmgr install lipsum` |
| `microtype.sty not found` | `sudo tlmgr install microtype` |

Alternatively, install the full TeX Live distribution to avoid missing packages:
- macOS: `brew install --cask mactex` (~5GB)
- Ubuntu/Debian: `sudo apt install texlive-full`

## Installation

```bash
# Clone the repository
git clone https://github.com/mcharo/arxindle.git
cd arxindle

# Install with uv
uv sync
```

Or with pip:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Convert a paper with default Kindle-friendly dimensions (4×6 inches):

```bash
uv run arxindle -u "https://arxiv.org/abs/2301.00001" -o paper.pdf
```

### CLI Options

```
Usage: arxindle [-h] -u URL -o PATH [-W WIDTH] [-H HEIGHT] [-m MARGIN] [-l] [-v]

Options:
  -u, --url URL       ArXiv URL or paper ID (e.g., "2301.00001") [required]
  -o, --output PATH   Output PDF path [required]
  -W, --width WIDTH   Page width in inches (default: 4)
  -H, --height HEIGHT Page height in inches (default: 6)
  -m, --margin MARGIN Page margin in inches, 0-1 (default: 0.2)
  -l, --landscape     Enable landscape orientation (requires pdftk)
  -v, --verbose       Show detailed output including LaTeX logs
  -h, --help          Show help message and exit
```

### Examples

**Standard Kindle conversion:**
```bash
uv run arxindle -u "https://arxiv.org/abs/2301.00001" -o paper.pdf
```

**Custom dimensions for larger e-readers:**
```bash
uv run arxindle -u "2301.00001" -o paper.pdf -W 6 -H 8 -m 0.3
```

**Landscape mode (useful for papers with wide figures/tables):**
```bash
uv run arxindle -u "2301.00001" -o paper.pdf -l
```

## Limitations

- **Source required**: Only works with ArXiv papers that have LaTeX source available (most do)
- **LaTeX compatibility**: Some complex LaTeX setups may not recompile cleanly
- **Results vary**: The automated transformations work well for most papers, but some may need manual adjustment

## License

See [LICENSE](./LICENSE) for details.

## Credits

- [Soumik Rakshit](https://github.com/soumik12345) for the original [arxiv2kindle](https://github.com/soumik12345/Arxiv2Kindle) project.
