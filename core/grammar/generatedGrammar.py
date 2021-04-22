patterns = {
  ('hashtag',): comment,
  ('singleQuote',): string,
  ('doubleQuote',): string,
  ('var', 'underline', 'var'): var,
  ('underline', 'var'): var,
  ('var', 'underline'): var,
  ('underline',): var,
  ('value', 'dot', 'value'): floatNumber,
}