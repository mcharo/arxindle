# Arxiv2Kindle

Convert ArXiv papers to Kindle-friendly PDFs. Arxiv2Kindle downloads the LaTeX source from ArXiv and recompiles it with optimized formatting for e-readers like the Kindle.

## Features

- **Reformats for e-readers**: Converts papers to fit small screens (default 4×6 inches)
- **Full fidelity**: Renders images, diagrams, tables, and formulae correctly
- **Single-column layout**: Converts 2-column academic formats into readable single-column
- **Landscape mode**: Optional landscape orientation for wider content
- **Send to Kindle**: Optionally email the converted PDF directly to your Kindle device

## Prerequisites

You'll need these tools installed on your system:

- **pdflatex** (required): For compiling LaTeX to PDF
  - macOS: `brew install --cask mactex` or `brew install basictex`
  - Ubuntu/Debian: `sudo apt install texlive-latex-base`
  
- **pdftk** (optional, for landscape mode only):
  - macOS: `brew install pdftk-java`
  - Ubuntu/Debian: `sudo apt install pdftk`

## Installation

```bash
# Clone the repository
git clone https://github.com/soumik12345/Arxiv2Kindle.git
cd Arxiv2Kindle

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
uv run arxiv2kindle -u "https://arxiv.org/abs/2301.00001"
```

The converted PDF will be saved in a temporary directory (path printed to console).

### CLI Options

```
Usage: arxiv2kindle [OPTIONS]

Options:
  -u, --arxiv_url TEXT    ArXiv URL or paper ID (e.g., "2301.00001" or full URL)
  -w, --width INTEGER     Page width in inches [default: 4]
  -h, --height INTEGER    Page height in inches [default: 6]
  -m, --margin FLOAT      Page margin in inches (must be between 0 and 1) [default: 0.2]
  -l, --is_landscape      Enable landscape orientation (swaps width/height, requires pdftk)
  -g, --gmail TEXT        Your Gmail address (for sending to Kindle)
  -k, --kindle_mail TEXT  Your Kindle email address (for sending to Kindle)
  --help                  Show this message and exit
```

### Examples

**Standard Kindle conversion:**
```bash
uv run arxiv2kindle -u "https://arxiv.org/abs/2301.00001"
```

**Custom dimensions for larger e-readers:**
```bash
uv run arxiv2kindle -u "2301.00001" -w 6 -h 8 -m 0.3
```

**Landscape mode (useful for papers with wide figures/tables):**
```bash
uv run arxiv2kindle -u "2301.00001" -l
```

**Send directly to your Kindle:**
```bash
uv run arxiv2kindle -u "2301.00001" -g "your.email@gmail.com" -k "your_kindle@kindle.com"
```

### Sending to Kindle

The `-g` (Gmail) and `-k` (Kindle email) options let you send the converted PDF directly to your Kindle device via email:

1. **Find your Kindle email address**: Go to Amazon → Manage Your Content and Devices → Preferences → Personal Document Settings. Your Kindle email looks like `name_XXXX@kindle.com`.

2. **Add your Gmail to approved senders**: In the same settings page, add your Gmail address to the "Approved Personal Document E-mail List".

3. **Use an App Password**: Gmail requires an [App Password](https://support.google.com/accounts/answer/185833) for third-party apps. Generate one in your Google Account settings.

4. **Run with email options**: When you include both `-g` and `-k`, the tool will prompt for your Gmail app password and send the PDF to your Kindle.

## Limitations

- **Source required**: Only works with ArXiv papers that have LaTeX source available (most do)
- **LaTeX compatibility**: Some complex LaTeX setups may not recompile cleanly
- **Results vary**: The automated transformations work well for most papers, but some may need manual adjustment

## Converted Samples

All photos captured on a Kindle Paperwhite 10th Generation:

![](./assets/1.jpeg)

![](./assets/2.jpeg)

![](./assets/3.jpeg)

![](./assets/6.jpeg)

![](./assets/11.jpeg)

![](./assets/13.jpeg)

![](./assets/14.jpeg)

![](./assets/15.jpeg)

![](./assets/17.jpeg)

![](./assets/18.jpeg)

## License

See [LICENSE](./LICENSE) for details.
