CODE ATLAS for psf/requests — where past issues were actually fixed
(from this system's own resolved runs; treat as evidence, verify by reading — past fixes suggest, they do not decide)

- method = builtin_str(method) problem
    -> requests/models.py, requests/sessions.py
- Allow lists in the dict values of the hooks argument
    -> requests/models.py
- Uncertain about content/text vs iter_content(decode_unicode=True/False)
    -> requests/utils.py
- `Session.resolve_redirects` copies the original request for all subsequent requests, can cause incor
    -> requests/sessions.py
