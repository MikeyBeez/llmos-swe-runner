CODE ATLAS for sphinx-doc/sphinx — where past issues were actually fixed
(from this system's own resolved runs; treat as evidence, verify by reading — past fixes suggest, they do not decide)

- autodoc isn't able to resolve struct.Struct type annotations
    -> sphinx/util/inspect.py, sphinx/util/typing.py
- autodoc: The annotation only member in superclass is treated as "undocumented"
    -> setup.py, sphinx/ext/autodoc/__init__.py, tox.ini
- Using rst_prolog removes top level headings containing a domain directive
    -> sphinx/util/rst.py, tox.ini
- inherited-members should support more than one class
    -> sphinx/ext/autodoc/__init__.py, tox.ini
- overescaped trailing underscore on attribute with napoleon
    -> setup.py, sphinx/ext/napoleon/docstring.py, tox.ini
- autodoc_type_aliases does not effect to variables and attributes
    -> setup.py, sphinx/ext/autodoc/__init__.py, tox.ini
- napoleon_use_param should also affect "other parameters" section
    -> setup.py, sphinx/ext/napoleon/docstring.py, tox.ini
- viewcode creates pages for epub even if `viewcode_enable_epub=False` on `make html epub`
    -> setup.py, sphinx/ext/viewcode.py, tox.ini
- autodoc: empty __all__ attribute is ignored
    -> setup.py, sphinx/ext/autodoc/__init__.py, tox.ini
