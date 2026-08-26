import pathlib
import unicodedata

for p in pathlib.Path('knowledge_base').rglob('*.txt'):
    text = p.read_text(encoding='utf-8')
    
    # Normalize unicode to standard ASCII equivalents
    cleaned = (
        text.replace('\u2011', '-')
            .replace('\u2013', '-')
            .replace('\u2014', '-')
            .replace('\u2018', "'")
            .replace('\u2019', "'")
            .replace('\u201c', '"')
            .replace('\u201d', '"')
            .replace('\u202f', ' ')
            .replace('\u00a0', ' ')
            .replace('\u200b', '')
            .replace('\u20b9', 'INR ')
    )
    # Further ensure standard ASCII characters
    cleaned = unicodedata.normalize('NFKD', cleaned)
    
    if cleaned != text:
        p.write_text(cleaned, encoding='utf-8')
        print(f'Cleaned: {p.name}')

print('Sanitization completed successfully.')
