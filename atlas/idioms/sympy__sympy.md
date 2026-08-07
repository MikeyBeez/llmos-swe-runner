- Arithmetic and operator methods on Expr subclasses must return SymPy
  objects, never bare Python numbers. `return 1` is a bug even when the
  math is right: callers test identity with `is S.One`. Use
  `from sympy.core.singleton import S` and return S.One / S.Zero / S.Half.
- When one operator method (__mul__) has a bug, its siblings in the same
  class (__truediv__, __rmul__, __pow__) usually carry the same pattern --
  read them and apply the same fix there too, in the same patch.
- Fixes in this package are usually MULTI-HUNK: the issue reports one
  symptom, the accepted fix touches 2-3 places in the same file. After
  your reproduction goes green, look for the other places.
