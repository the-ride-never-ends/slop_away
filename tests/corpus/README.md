# Validation corpus

`bad/` holds source snapshots and cases with known findings.
`expected.json` lists their exact native codes. A changed code set fails
the test and names the affected file.

`fixed/` holds clean examples after automatic fixes and manual edits.
`good/` holds clean inputs. Both groups run with all native rules.

`sources.json` records the source revision for repository snapshots.
The protected source documents stay unchanged.

`drafts/` holds the automatic safe-fix results. These files can still have
findings. `drafts/remaining.json` lists the work for owner review.
Drafts do not count as clean fixed examples.

## References

Run the setup once after installing development dependencies:

```bash
bash tests/differential/install_references.sh .venv
```

This installs checksum-pinned Vale 3.28.1 for Linux x86-64. It also prepares
the same CMU data edition for the independent textstat reference. Test
runs do not download tools or dictionaries.

Readability tests compare each eligible section within 0.5 grade. Vale
tests compare codes and source lines for four authored rule types.
The Vale input masks the source spans that project policy excludes.
