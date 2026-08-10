- Old checkouts (2017-2019) predate much of the modern API: check the
  actual signature with inspect before calling; do not trust memory of
  current sklearn. Test paths from the modern layout often do not exist.
- Numeric assertions need tolerances: use numpy.testing.assert_allclose
  with rtol, never ==, or a correct fix can stay red on float noise.
- Estimator bugs usually need fit() called before the buggy attribute or
  method exists -- a reproduction that skips fit observes nothing.
