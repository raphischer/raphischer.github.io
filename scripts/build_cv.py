import argparse
import json
import sys
from pathlib import Path

TEX_HEADER = r"""\documentclass[12pt]{letter}
\usepackage[utf8]{inputenc}
\usepackage[bottommargin=1in]{TLCcoverletter}
\usepackage{graphicx}
\usepackage{tabularx}
\usepackage{xcolor}
\usepackage[hidelinks]{hyperref}
\usepackage{enumitem}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\setlist[itemize]{leftmargin=1.2em,noitemsep,topsep=0pt}
\definecolor{highlight}{RGB}{88,166,255}
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


def render_personal_header(personal):
    lines = [r'\\begin{minipage}[c]{0.7\\textwidth}']
    lines.append(
        r'    \\textbf{\\LARGE ' + escape_latex(personal.get('name', '')) +
        r'~{\\color{highlight}|} Curriculum Vitae}\\vspace{0.5em}\\'
    )
    role = escape_latex(personal.get('role', ''))
    affiliation = escape_latex(personal.get('affiliation', ''))
    if role and affiliation:
        lines.append(f'    {role} at {affiliation}\\')
    elif role:
        lines.append(f'    {role}\\')
    birthinfo = escape_latex(personal.get('birthinfo', ''))
    nationality = escape_latex(personal.get('nationality', ''))
    if birthinfo or nationality:
        lines.append(f'    Born {birthinfo}. Nationality: {nationality}\\')
    email = personal.get('email', '')
    if email:
        lines.append(f'    Email: \\href{{mailto:{escape_latex(email)}}}{{{escape_latex(email)}}}\\')
    website = personal.get('webpage', '')
    linkedin = personal.get('linkedin', '')
    if website and linkedin:
        lines.append(
            f'    To learn about my ongoing activities, visit my \\href{{{escape_latex(website)}}}{{webpage}} and \\href{{{escape_latex(linkedin)}}}{{LinkedIn}}\\'
        )
    elif website:
        lines.append(f'    Website: \\href{{{escape_latex(website)}}}{{webpage}}\\')
    scholar = personal.get('scholar', '')
    github = personal.get('github', '')
    if scholar and github:
        lines.append(
            f'    My publications and software are listed on \\href{{{escape_latex(scholar)}}}{{Google Scholar}} and \\href{{{escape_latex(github)}}}{{GitHub}}\\'
        )
    elif scholar:
        lines.append(f'    Google Scholar: \\href{{{escape_latex(scholar)}}}{{link}}\\')
    elif github:
        lines.append(f'    GitHub: \\href{{{escape_latex(github)}}}{{link}}\\')
    lines.append(r'\\end{minipage}\hfill%')
    picture = personal.get('picture', '')
    if picture:
        lines.append(r'\\begin{minipage}[c]{0.29\\textwidth}')
        lines.append(r'    \\includegraphics[width=.7\\linewidth]{' + escape_latex(picture) + r'}')
        lines.append(r'\\end{minipage}')
    return '\n'.join(lines)


def render_section(section):
    lines = [f'\\section{{{escape_latex(section.get("heading", ""))}}}']
    for item in section.get('items', []):
        period = escape_latex(item.get('period', ''))
        title = escape_latex(item.get('title', ''))
        organization = escape_latex(item.get('organization', ''))
        lines.append(r'\\begin{tabularx}{\\textwidth}{p{0.14\\textwidth}@{\\hspace{1em}}X@{}}')
        if organization:
            lines.append(f'  \\textbf{{{period}}} & \\textbf{{{title}}} @ {organization}\\[-0.9em]')
        else:
            lines.append(f'  \\textbf{{{period}}} & \\textbf{{{title}}}\\[-0.9em]')
        highlights = item.get('highlights', []) or item.get('details', [])
        if highlights:
            lines.append(r'    & \\footnotesize \\begin{itemize}[leftmargin=1.2em,noitemsep,topsep=0pt]')
            for bullet in highlights:
                lines.append(f'        \\item {escape_latex(bullet)}')
            lines.append(r'      \\end{itemize}')
        lines.append(r'\\end{tabularx}')
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
    import subprocess
    import sys
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
        print('On Windows: Install MiKTeX or TeX Live')
        print('On macOS: brew install mactex')
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
    args = parser.parse_args()

    path = Path(args.input)
    if not path.exists():
        raise FileNotFoundError(f'Input file not found: {path}')

    with path.open('r', encoding='utf-8') as handle:
        data = json.load(handle)

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
