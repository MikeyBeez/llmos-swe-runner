- Django never removes behaviour abruptly. If the issue asks to forbid,
  prevent, or drop something, the accepted fix DEPRECATES first: raise
  RemovedInDjangoXXWarning (from django.utils.deprecation) now, error in a
  later release -- not an immediate TypeError/ValueError, unless the issue
  explicitly says the deprecation cycle is done.
- When changing how querysets compose (filtering over annotated or
  aggregated queries, subquery wrapping, sliced querysets), the INNER
  query's GROUP BY and ORDER BY must survive into the outer SQL. Print
  str(qs.query) before and after your change and compare those clauses --
  a fix that alters them breaks other callers even when your case passes.
- django.utils.http date parsing handles THREE formats (RFC 1123, RFC 850,
  asctime); match the format to the function and exercise all three.
  Two-digit years are interpreted relative to the CURRENT date (RFC 7231:
  a date more than 50 years in the future means the previous century) --
  never hardcode a century split, and never call datetime methods the
  tests cannot mock (use datetime.datetime.now(), not a cached value).
