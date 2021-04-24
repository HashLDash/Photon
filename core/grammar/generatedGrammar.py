patterns = {
  ('hashtag',): comment,
  ('singleQuote',): string,
  ('doubleQuote',): string,
  ('var', 'underline', 'var'): var,
  ('underline', 'var'): var,
  ('var', 'underline'): var,
  ('underline',): var,
  ('num', 'dot', 'num'): floatNumber,
  ('print', 'lparen', 'expr', 'rparen'): printFunction,
  ('print', 'lparen', 'num', 'rparen'): printFunction,
}