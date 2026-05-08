import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

TEX_HEADER = r"""\documentclass[12pt]{letter}
\usepackage[utf8]{inputenc}
\usepackage[bottommargin=1in]{CustomCoverletter}

\begin{document}
"""

TEX_FOOTER = r"""
\end{document}
"""


def escape_latex(value):
    if not isinstance(value, str):
        return str(value)
    return (
        value
        .replace('\\', r'\\textbackslash{}')
        .replace('&', r'\\&')
        .replace('%', r'\\%')
        .replace('$', r'\\$')
        .replace('#', r'\\#')
        .replace('_', r'\\_')
        .replace('{', r'\\{')
        .replace('}', r'\\}')
    )


def parse_css_variables(paths):
    variables = {}
    for path in paths:
        css_path = Path(path)
        if not css_path.exists():
            continue
        content = css_path.read_text(encoding='utf-8')
        root_match = re.search(r':root\s*\{([\s\S]*?)\}', content)
        block = root_match.group(1) if root_match else content
        for var, value in re.findall(r'(--[\w-]+)\s*:\s*([^;]+);', block):
            variables[var.strip()] = value.strip()
    return variables


def resolve_css_value(value, variables, depth=0):
    if depth > 5 or not isinstance(value, str):
        return value
    var_match = re.match(r'var\(\s*(--[\w-]+)\s*\)', value)
    if var_match:
        referenced = var_match.group(1)
        return resolve_css_value(variables.get(referenced, value), variables, depth + 1)
    return value


def parse_hex_color(value):
    value = value.lstrip('#')
    if len(value) == 3:
        value = ''.join(ch * 2 for ch in value)
    if len(value) == 4:
        value = value[:3]
    if len(value) == 8:
        value = value[:6]
    if len(value) != 6:
        raise ValueError(f'Invalid hex color: {value}')
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def parse_rgb_color(value):
    nums = re.findall(r'\d{1,3}', value)
    if len(nums) >= 3:
        return tuple(int(n) for n in nums[:3])
    raise ValueError(f'Invalid rgb color: {value}')


def parse_hsl_color(value):
    parts = re.findall(r'[-+]?[0-9]*\.?[0-9]+%?', value)
    if len(parts) < 3:
        raise ValueError(f'Invalid hsl color: {value}')
    h = float(parts[0]) % 360
    s = float(parts[1].rstrip('%')) / 100.0
    l = float(parts[2].rstrip('%')) / 100.0
    c = (1 - abs(2 * l - 1)) * s
    x = c * (1 - abs((h / 60.0) % 2 - 1))
    m = l - c / 2
    if h < 60:
        rp, gp, bp = c, x, 0
    elif h < 120:
        rp, gp, bp = x, c, 0
    elif h < 180:
        rp, gp, bp = 0, c, x
    elif h < 240:
        rp, gp, bp = 0, x, c
    elif h < 300:
        rp, gp, bp = x, 0, c
    else:
        rp, gp, bp = c, 0, x
    return tuple(round((v + m) * 255) for v in (rp, gp, bp))


def parse_color_value(value, variables):
    value = resolve_css_value(value, variables)
    if isinstance(value, str):
        value = value.strip()
        if value.startswith('#'):
            return parse_hex_color(value)
        if value.startswith('rgb(') or value.startswith('rgba('):
            return parse_rgb_color(value)
        if value.startswith('hsl(') or value.startswith('hsla('):
            return parse_hsl_color(value)
    raise ValueError(f'Unsupported color format: {value}')


def pick_highlight_color(variables):
    candidates = ['--accent', '--highlight', '--pale-amber', '--olive-leaf', '--powder-blue']
    for key in candidates:
        if key in variables:
            try:
                return parse_color_value(variables[key], variables)
            except ValueError:
                continue
    return (88, 166, 255)


def format_address(personal):
    address = personal.get('address')
    if isinstance(address, list):
        lines = [str(line) for line in address]
    elif isinstance(address, str):
        lines = [line.strip() for line in address.splitlines() if line.strip()]
    elif personal.get('location'):
        lines = [str(personal.get('location'))]
    else:
        lines = []
    return ' \\\\ '.join(escape_latex(line) for line in lines)


def generate_style_file(data, style_path, highlight_rgb):
    personal = data.get('personal', {})
    address_lines = format_address(personal)
    
    # Define template with {{ }} for LaTeX braces and {placeholder} for substitutions
    style_template = r"""\NeedsTeXFormat{{LaTeX2e}}
\ProvidesPackage{{CustomCoverletter}}[Generated cover letter package]

\RequirePackage[T1]{{fontenc}}
\RequirePackage[default,semibold]{{sourcesanspro}}
\RequirePackage[12pt]{{moresize}}
\usepackage{{anyfontsize}}
\RequirePackage{{csquotes}}

% MARGINS AND SPACING
\newcommand*\TLC@bottommargin{{2in}} % default value
\DeclareOptionX{{bottommargin}}{{%
  \renewcommand*\TLC@bottommargin{{#1}}%
}}

% Process options
\ProcessOptionsX

% --- Geometry setup ---
\RequirePackage[
  margin=.5in,
  bottom=\TLC@bottommargin
]{{geometry}}

\setlength{{\parskip}}{{1em}}
%\setlength{{\parindent}}{{1in}}

% COLOR
\RequirePackage{{xcolor}}
\definecolor{{highlight}}{{RGB}}{{{color_rgb}}}

% LINKS
\RequirePackage{{hyperref}}
\hypersetup{{
  colorlinks=true,
  urlcolor=highlight,
  linkcolor=highlight,
  citecolor=highlight
}}

% TABLES
\RequirePackage{{tabularx}}
\RequirePackage{{array}}
\RequirePackage{{enumitem}}
\renewcommand{{\arraystretch}}{{1.05}}

% BOLD COMMAND
\newcommand{{\bold}}[1]{{ {{\bfseries #1}}}}

% NO PAGE NUMBER
\pagenumbering{{gobble}}

% SUBFILES IMPORTING
\RequirePackage{{standalone}}
\RequirePackage{{import}}

% FOR TEMPLATE FILLER
\RequirePackage[english]{{babel}}
\RequirePackage{{blindtext}}

% ----------------------------------------------------------------------
% Section heading redefinitions (supporting \section and \section*)
% ----------------------------------------------------------------------
\makeatletter

\providecommand{{\section}}{{%
  \@ifstar{{\TLC@sectionStar}}{{\TLC@section}}}}

\newcommand{{\TLC@section}}[1]{{%
  \par\vspace{{0.1em}}%
  {{\Large\textbf{{#1}}}}\par%
}}

\newcommand{{\TLC@sectionStar}}[1]{{%
  \par\vspace{{0.1em}}%
  {{\Large\textbf{{#1}}}}\par%
}}

\providecommand{{\subsection}}{{%
  \@ifstar{{\TLC@subsectionStar}}{{\TLC@subsection}}}}

\newcommand{{\TLC@subsection}}[1]{{%
  \par\vspace{{0.1em}}%
  {{\large\textbf{{#1}}}}\par%
}}

\newcommand{{\TLC@subsectionStar}}[1]{{%
  \par\vspace{{0.1em}}%
  {{\large\textbf{{#1}}}}\par%
}}

\makeatother

% publications
\RequirePackage[backend=biber,style=alphabetic,sorting=ydnt]{{biblatex}}
\addbibresource{{publications.bib}}
\DeclareBibliographyCategory{{peerreviewed}}
\DeclareBibliographyCategory{{preprint}}
\DeclareBibliographyCategory{{videotalks}}

% categories
\AtDataInput{{%
  \ifkeyword{{peerreviewed}}{{%
    \addtocategory{{peerreviewed}}{{\thefield{{entrykey}}}}%
  }}{{}}
  \ifkeyword{{videotalk}}{{%
    \addtocategory{{videotalks}}{{\thefield{{entrykey}}}}%
  }}{{}}
  \ifkeyword{{preprint}}{{%
    \addtocategory{{preprint}}{{\thefield{{entrykey}}}}%
  }}{{}}
}}

% Hide some fields
\AtEveryBibitem{{%
  \clearfield{{month}}
  \clearfield{{note}}
  \clearlist{{publisher}}
  \clearlist{{language}}
  \clearlist{{location}}
  \clearname{{editor}}%
  \ifboolexpr{{not test {{\iffieldundef{{doi}}}}}}{{%
    \clearfield{{url}}
  }}{{}}
}}

\def\name{{{name}}}
\signature{{\name}}
\address{{{address}}}
\def\birthinfo{{{birthinfo}}}
\def\linkedin{{{linkedin}}}
\def\mail{{{email}}}
\def\website{{{webpage}}}
\def\role{{{role}}}
\def\github{{{github}}}
\def\scholar{{{scholar}}}
\def\nationality{{{nationality}}}
"""
    
    # Prepare values for template substitution
    format_values = {
        'color_rgb': f'{highlight_rgb[0]},{highlight_rgb[1]},{highlight_rgb[2]}',
        'name': escape_latex(personal.get('name', '')),
        'address': address_lines,
        'birthinfo': escape_latex(personal.get('birthinfo', '')),
        'linkedin': escape_latex(personal.get('linkedin', '')),
        'email': escape_latex(personal.get('email', '')),
        'webpage': escape_latex(personal.get('webpage', '')),
        'role': escape_latex(personal.get('role', '')),
        'github': escape_latex(personal.get('github', '')),
        'scholar': escape_latex(personal.get('scholar', '')),
        'nationality': escape_latex(personal.get('nationality', '')),
    }
    
    style_content = style_template.format(**format_values)
    
    style_path.parent.mkdir(parents=True, exist_ok=True)
    style_path.write_text(style_content, encoding='utf-8')
    print(f'Generated {style_path}')


def render_personal_header(personal):
    lines = [r'\begin{minipage}[c]{0.7\textwidth}']
    lines.append(
        r'    \textbf{\LARGE ' + escape_latex(personal.get('name', '')) +
        r'~{\color{highlight}|} Curriculum Vitae}\vspace{0.5em}\\'
    )
    role = escape_latex(personal.get('role', ''))
    affiliation = escape_latex(personal.get('affiliation', ''))
    if role and affiliation:
        lines.append(f'    {role} at {affiliation}\\\\')
    elif role:
        lines.append(f'    {role}\\\\')
    birthinfo = escape_latex(personal.get('birthinfo', ''))
    nationality = escape_latex(personal.get('nationality', ''))
    if birthinfo or nationality:
        lines.append(f'    Born {birthinfo}. Nationality: {nationality}\\\\')
    email = personal.get('email', '')
    if email:
        lines.append(f'    Email: \\href{{mailto:{escape_latex(email)}}}{{{escape_latex(email)}}}\\\\')
    website = personal.get('webpage', '')
    linkedin = personal.get('linkedin', '')
    if website and linkedin:
        lines.append(
            f'    To learn about my ongoing activities, visit my \\href{{{escape_latex(website)}}}{{webpage}} and \\href{{{escape_latex(linkedin)}}}{{LinkedIn}}\\\\'
        )
    elif website:
        lines.append(f'    Website: \\href{{{escape_latex(website)}}}{{webpage}}\\\\')
    scholar = personal.get('scholar', '')
    github = personal.get('github', '')
    if scholar and github:
        lines.append(
            f'    My publications and software are listed on \\href{{{escape_latex(scholar)}}}{{Google Scholar}} and \\href{{{escape_latex(github)}}}{{GitHub}}\\\\'
        )
    elif scholar:
        lines.append(f'    Google Scholar: \\href{{{escape_latex(scholar)}}}{{link}}\\\\')
    elif github:
        lines.append(f'    GitHub: \\href{{{escape_latex(github)}}}{{link}}\\\\')
    lines.append(r'\end{minipage}\hfill%')
    picture = personal.get('picture', '')
    if picture:
        lines.append(r'\begin{minipage}[c]{0.29\textwidth}')
        lines.append(r'    \includegraphics[width=.7\linewidth]{' + escape_latex(picture) + r'}')
        lines.append(r'\end{minipage}')
    return '\n'.join(lines)


def render_section(section):
    lines = [f'\\section{{{escape_latex(section.get("heading", ""))}}}']
    for item in section.get('items', []):
        period = escape_latex(item.get('period', ''))
        title = escape_latex(item.get('title', ''))
        organization = escape_latex(item.get('organization', ''))
        lines.append(r'\begin{tabularx}{\textwidth}{p{0.14\textwidth}@{\hspace{1em}}X@{}}')
        if organization:
            lines.append(f'  \\textbf{{{period}}} & \\textbf{{{title}}} @ {organization}\\[-0.9em]')
        else:
            lines.append(f'  \\textbf{{{period}}} & \\textbf{{{title}}}\\[-0.9em]')
        highlights = item.get('highlights', []) or item.get('details', [])
        if highlights:
            lines.append(r'    & \footnotesize \begin{itemize}[leftmargin=1.2em,noitemsep,topsep=0pt]')
            for bullet in highlights:
                lines.append(f'        \\item {escape_latex(bullet)}')
            lines.append(r'      \end{itemize}')
        lines.append(r'\end{tabularx}')
    return '\n'.join(lines)


def build_tex(data):
    personal = data.get('personal', {})
    lines = [TEX_HEADER]
    lines.append(render_personal_header(personal))
    lines.append('')
    statement = data.get('statement', '')
    if statement:
        lines.append(escape_latex(statement))
        lines.append('')
    for section in data.get('sections', []):
        lines.append(render_section(section))
        lines.append('')
    lines.append(TEX_FOOTER)
    return '\n'.join(lines)


def compile_pdf(tex_file, pdf_file):
    try:
        result = subprocess.run(
            ['latexmk', '-pdf', '-interaction=nonstopmode', '-halt-on-error', str(tex_file)],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            print(f'Compiled {pdf_file}')
            return True
        else:
            print(f'LaTeX compilation failed:\n{result.stdout}\n{result.stderr}', file=sys.stderr)
            return False
    except FileNotFoundError:
        print('latexmk not found. Install TeX Live to compile PDFs locally.', file=sys.stderr)
        print('On Windows: Install MiKTeX or TeX Live', file=sys.stderr)
        print('On macOS: brew install mactex', file=sys.stderr)
        print('On Linux: sudo apt-get install texlive-latex-base texlive-latex-extra', file=sys.stderr)
        return False
    except subprocess.TimeoutExpired:
        print('LaTeX compilation timed out', file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description='Generate a LaTeX CV from JSON data.')
    parser.add_argument('--input', '-i', default='data/cv.json', help='Input JSON file for CV content.')
    parser.add_argument('--output', '-o', default='cv.tex', help='Output LaTeX file path.')
    parser.add_argument('--no-compile', action='store_true', help='Skip PDF compilation.')
    parser.add_argument('--css', default='styles.css', help='CSS file to read palette colors from.')
    args = parser.parse_args()

    path = Path(args.input)
    if not path.exists():
        raise FileNotFoundError(f'Input file not found: {path}')

    with path.open('r', encoding='utf-8') as handle:
        data = json.load(handle)

    css_variables = parse_css_variables([args.css, 'colors.css'])
    highlight_rgb = pick_highlight_color(css_variables)
    style_path = Path(args.output).parent / 'CustomCoverletter.sty'
    generate_style_file(data, style_path, highlight_rgb)

    tex = build_tex(data)
    tex_path = Path(args.output)
    with tex_path.open('w', encoding='utf-8') as handle:
        handle.write(tex)
    print(f'Generated {args.output}')

    if not args.no_compile:
        pdf_file = tex_path.with_suffix('.pdf')
        compile_pdf(tex_path, pdf_file)


if __name__ == '__main__':
    main()
