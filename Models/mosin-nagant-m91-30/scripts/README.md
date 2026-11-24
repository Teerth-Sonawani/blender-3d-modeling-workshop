# No scripts preserved

This model has no `bpy` phase scripts on disk. The geometry, materials, bake and export code
ran inline through the bridge during the session and was never written out, so the build is
not reproducible from files.

That is a gap against `AGENTS.md` §6 ("keep the exact Python used for each phase in
`Models/<slug>/scripts/`"). If this asset is revisited, write each phase to a numbered script
in this folder as it runs.
