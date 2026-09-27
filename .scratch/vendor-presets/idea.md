# vendor-presets

The Insert Library only has the CNC Kitchen metric set plus one camera thread. Ruthex,
McMaster-Carr and E-Z Lok publish different recommended bore sizes, and US users want
#4-40, #6-32, #8-32, #10-24. Idea: one `[Inserts]`-style section per vendor (or bundled preset
files) and a vendor selector in the dialog. Ruthex recommends tapered bores — possible
optional bore style.

## Open questions

- Presets in `config.ini` sections, or separate bundled files (e.g. `presets/ruthex.ini`)?
- How do user-added custom inserts coexist with vendor presets on upgrade?
- Source and verification of each vendor's numbers (datasheet links in the file)?
- Tapered bore: in scope here or its own feature?

Source: feature proposals, session "Feature proposals for repo" (2026-06-11); selected 2026-09-27.
