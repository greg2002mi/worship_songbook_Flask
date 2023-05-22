import re

# def transpose_chord(chord, key):
#     notes = 'C C# D D# E F F# G G# A A# B'.split()
#     note, suffix = re.match(r'([A-Ga-g#]+)(.*)', chord).groups()
#     index = notes.index(note.upper())
#     new_index = (index + notes.index(key.upper())) % len(notes)
#     new_note = notes[new_index]
#     return f'{new_note.lower()}{suffix}'

# def transpose_chordpro(chordpro_text, key):
#     # Define regular expressions for chordpro elements
#     chord_regex = r'\[([^\]]+)\]'
#     newline_regex = r'\n'
#     section_regex = r'^(chorus:|verse \d+|bridge:|intro:)\s*(.*)$'

#     # Replace chordpro elements with HTML tags
#     html_text = re.sub(chord_regex, r'<span class="chord" data-chord="\1"></span>', chordpro_text)
#     html_text = re.sub(newline_regex, r'<br>', html_text)

#     # Wrap the entire text in a <pre> tag to preserve whitespace
#     html_text = f'<pre>{html_text}</pre>'

#     # Transpose chords to new key
#     transposed_text = re.sub(chord_regex, lambda m: f'[{transpose_chord(m.group(1), key):s}]', html_text)

#     # Move chords to the top of the lyrics
#     lines = transposed_text.split('<br>')
#     html_lines = []
#     for line in lines:
#         chords = re.findall(chord_regex, line)
#         if chords:
#             line = re.sub(chord_regex, '', line)
#             line = '<span class="chord">' + '</span><span class="lyrics">'.join(chords) + '</span>' + line

#             # Insert non-breaking space between consecutive chords
#             line = re.sub(r'(<span class="chord">.+?</span>)\s*(?=<span class="chord">)', r'\1&nbsp;', line)
#         else:
#             section_match = re.match(section_regex, line, re.IGNORECASE)
#             if section_match:
#                 section_label = section_match.group(1).lower()
#                 section_content = section_match.group(2)
#                 line = f'<span class="section {section_label} chord">{section_label.capitalize()}:</span> {section_content}'

#         html_lines.append(line)
#     html_text = '<br>'.join(html_lines)

#     return html_text

# def transpose_chord(chord, key='C'):
#     notes = 'C C# D D# E F F# G G# A A# B'.split()
#     note, suffix = re.match(r'([A-Ga-g#]+)(.*)', chord).groups()
#     index = notes.index(note.upper())
#     new_index = (index + notes.index(key.upper())) % len(notes)
#     new_note = notes[new_index]
#     return f'{new_note.lower()}{suffix}'

# def transpose_chordpro(chordpro_text, key='C'):
#     # Define regular expressions for chordpro elements
#     chord_regex = r'\[([^\]]+)\]'
#     newline_regex = r'\n'
#     section_regex = r'^(chorus:|verse \d+|bridge:|intro:)\s*(.*)$'

#     # Replace chordpro elements with HTML tags
#     html_text = re.sub(chord_regex, r'<span class="chord" data-chord="\1"></span>', chordpro_text)
#     html_text = re.sub(newline_regex, r'<br>', html_text)

#     # Wrap the entire text in a <pre> tag to preserve whitespace
#     html_text = f'<pre>{html_text}</pre>'

#     # Transpose chords to new key
#     transposed_text = re.sub(chord_regex, lambda m: f'[{transpose_chord(m.group(1), key):s}]', html_text)

#     # Move chords to the top of the lyrics
#     lines = transposed_text.split('<br>')
#     html_lines = []
#     for line in lines:
#         chords = re.findall(chord_regex, line)
#         if chords:
#             line = re.sub(chord_regex, '', line)
#             line = '<span class="lyrics">' + line + '</span>'
#             chords_html = ''
#             for chord in chords:
#                 chords_html += f'<span class="chord" data-chord="{chord}">{chord}</span>'
#             line = f'{chords_html}{line}'
#         else:
#             section_match = re.match(section_regex, line, re.IGNORECASE)
#             if section_match:
#                 section_label = section_match.group(1).lower()
#                 section_content = section_match.group(2)
#                 line = f'<span class="section {section_label}">{section_label.capitalize()}:</span> {section_content}'

#         html_lines.append(line)
#     html_text = '<br>'.join(html_lines)

#     return html_text

def transpose_chord(chord, key):
    notes = 'C C# D D# E F F# G G# A A# B'.split()
    note, suffix = re.match(r'([A-Ga-g#]+)(.*)', chord).groups()
    index = notes.index(note.upper())
    new_index = (index + notes.index(key.upper())) % len(notes)
    new_note = notes[new_index]
    return f'{new_note.lower()}{suffix}'

def transpose_chordpro(chordpro_text, key):
    # Define regular expressions for chordpro elements
    chord_regex = r'\[([^\]]+)\]'
    newline_regex = r'\n'
    section_regex = r'^(chorus:|verse \d+|bridge:|intro:)\s*(.*)$'

    # Replace chordpro elements with HTML tags
    html_text = re.sub(chord_regex, r'<chord>\1</chord>', chordpro_text)
    html_text = re.sub(newline_regex, r'<br>', html_text)

    # Wrap the entire text in a <pre> tag to preserve whitespace
    html_text = f'<pre>{html_text}</pre>'

    # Transpose chords to new key
    transposed_text = re.sub(chord_regex, lambda m: f'[{transpose_chord(m.group(1), key):s}]', html_text)

    # Move chords to the top of the lyrics
    lines = transposed_text.split('<br>')
    html_lines = []
    for line in lines:
        chords = re.findall(chord_regex, line)
        if chords:
            line = re.sub(chord_regex, '', line)
            line = '<span class="lyrics">' + line + '</span>'
            chords_html = ''
            for chord in chords:
                chords_html += f'<span class="chord">{chord}</span>'
            line = f'{chords_html}{line}'
        else:
            section_match = re.match(section_regex, line, re.IGNORECASE)
            if section_match:
                section_label = section_match.group(1).lower()
                section_content = section_match.group(2)
                line = f'<span class="section {section_label}">{section_label.capitalize()}:</span> {section_content}'

        html_lines.append(line)
    html_text = '<br>'.join(html_lines)

    return html_text