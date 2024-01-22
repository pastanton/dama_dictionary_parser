from pypdf import PdfReader
from csv import writer
from spellchecker import SpellChecker
from typing import Optional
from collections import OrderedDict

# Change the order text to match the order text in the PDF
ORDER_TEXT = 'Order 12345 by Your_Name on January 01, 1970'
PDF_FILE = 'DAMA_Dictionary_of_Data_Management_2nd_Ed.pdf'
# Change the output file name to whatever you want
OUTPUT_CSV_FILE = 'dama_dict_clean.csv'

def remove_word_spaces(s:str, ignore_words: Optional[set[str]] = None) -> str:
    """Remove spaces between words that are not in the dictionary, but in the dictionary if combined.

    Args:
        s (str): string to clean up
        ignore_words (Optional[set[str]], optional): Set of words to ignore. Used in recursion. 
        Defaults to None.

    Returns:
        str: Cleaned up string
    """
    sc = SpellChecker()
    word_array = s.split()
    if not sc.unknown(word_array):
        return s
    if not ignore_words:
        ignore_words = set()        
    for i in range(len(word_array) - 1):
        if word_array[i] in ignore_words:
            continue
        # Check if combined word is in the dictionary
        if not sc.unknown([word_array[i] + word_array[i + 1]]):
            # Replace the two words with the combined word
            s = s.replace(word_array[i] + ' ', word_array[i])
            # Check again.
            ignore_words.add(word_array[i])
            return remove_word_spaces(s, ignore_words)

    return s

def fix_hyphen_mess(s:str) -> str:
    """ The hyphens are all such a mess!!

    Args:
        s (str): Hyphenated madness!

    Returns:
        str: Cleaner result - hopefully.
    """
    if '-' not in s:
        return s
    
    s = s.replace(' - ', '--').replace(' -', '-').replace('- ', '-')
    while '---' in s:
        s = s.replace('---', '--')
    s = s.replace('--', ' - ')
    return s

pdf = PdfReader(PDF_FILE)
s = ''
for page in pdf.pages[17:]:
    page_text = page.extract_text()
    page_text = page_text.replace(ORDER_TEXT, '\n').replace('\r','')
    for line in page_text.split('\n'):
        line = line.strip()
        if line.startswith('Copyright © 2011') or line.startswith('DAMA Dictionary of Data Management 2nd Edition') or len(line) <= 1:
            s+= '\n'
            continue
        s += line + '\n'

clean_terms:OrderedDict[str,str] = OrderedDict()
terms = s.split('\n\n')
for term in terms:
    term = term.strip()
    if '\n' not in term:
        continue
    k, v = term.split('\n', 1)
    
    clean_def = v.strip().replace(' ”', '”').replace(' .', '.').replace(' ,', ',').replace(' ;', ';').replace(' :', ':').replace(' )', ')')
    while '  ' in clean_def:
        clean_def = clean_def.replace('  ', ' ')
    while ' \n' in clean_def:
        clean_def = clean_def.replace(' \n', '\n')
    clean_def = fix_hyphen_mess(clean_def)
    clean_def = remove_word_spaces(clean_def)
    clean_term = k.strip().replace('Alternate forms:', '\nAlternate forms:')
    clean_term = clean_term.replace('Alternate form:', '\nAlternate form:')
    while '  ' in clean_term:
        clean_term = clean_term.replace('  ', ' ')
    while ' \n' in clean_term:
        clean_term = clean_term.replace(' \n', '\n')
    clean_term = fix_hyphen_mess(clean_term)
    clean_terms[clean_term] = clean_def

# Clean up "SEE ALSO" entries
for a,b in clean_terms.items():
    b = b.strip()
    if b.startswith('SEE '):
        for c,d in clean_terms.items():
            see_also = b.replace('SEE ', '').strip()
            if ';' in see_also:
                for e in see_also.split(';'):
                    if e.strip() in c:
                        clean_terms[c] += f'\nRelated: {a.strip()}'
            if see_also in c:
                clean_terms[c] += f'\nRelated: {a.strip()}'
    
cleaner_terms:OrderedDict[str,str] = OrderedDict()

for a,b in clean_terms.items():
    if b.startswith('SEE '):
        continue
    cleaner_terms[a] = b

with open (OUTPUT_CSV_FILE, 'w+', encoding='utf-8') as f:
    c = writer(f, 'unix')
    c.writerow(['term', 'definition'])
    c.writerows([(k,v) for k,v in cleaner_terms.items()])