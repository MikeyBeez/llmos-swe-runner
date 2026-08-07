CODE ATLAS for pylint-dev/pylint — where past issues were actually fixed
(from this system's own resolved runs; treat as evidence, verify by reading — past fixes suggest, they do not decide)

- Linting fails if module contains module of the same name
    -> pylint/lint/expand_modules.py
- "--notes" option ignores note tags that are entirely punctuation
    -> pylint/checkers/misc.py, pylint/lint/run.py
- `--recursive=y` ignores `ignore-paths`
    -> pylint/lint/pylinter.py
- Using custom braces in message template does not work
    -> pylint/lint/run.py, pylint/reporters/text.py
