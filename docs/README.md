# Building the documentation

The documentation is generated with Sphinx. Install the documentation-only
dependencies and build the HTML site from the repository root:

```powershell
py -m pip install -r .\docs\requirements.txt
py -m sphinx -b html .\docs\source .\docs\build\html
```

Open `docs\build\html\index.html` in a browser after a successful build.

## Theme colours

Edit `docs\source\theme_colors.py` to change the documentation palette.
The `PRIMARY` value is the BaseCam accent colour used for navigation, headings,
and links. `SIDEBAR_BACKGROUND`, `SIDEBAR_LINK`, and `TEXT` control the left
navigation panel. Rebuild the site after changing a colour.

Use strict mode in CI or before publishing to treat broken links and warnings
as errors:

```powershell
py -m sphinx -E -W --keep-going -b html .\docs\source .\docs\build\html
```
