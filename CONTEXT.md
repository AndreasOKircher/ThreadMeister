# ThreadMeister

Autodesk Fusion add-in that cuts Bores for heat-set threaded inserts in 3D-printed parts.
The user picks a Target Body and one or more Sketch Points; ThreadMeister cuts one Bore per
point, sized from the chosen Insert Spec.

## Language

### Inserts

**Insert**:
A heat-set threaded insert (brass, melted into a printed part with a soldering iron).
_Avoid_: nut, threaded insert (in code), heat insert

**Insert Spec**:
The three numbers that define one Insert size: hole diameter, insert length, minimum wall
thickness — all in mm. Stored as `name = diameter, length, min_wall` in `config.ini`
`[Inserts]` and held at runtime in `tm_state.INSERT_SPECS` as `(hole_dia_mm, insert_len_mm, min_wall_mm)`.
_Avoid_: insert data, size entry

**Insert Library**:
The set of Insert Specs offered in the dialog's Insert Size dropdown — the `[Inserts]`
section of `config.ini` (defaults: CNC Kitchen metric sizes plus one 1/4"-20 camera thread).
_Avoid_: insert list, catalogue

**Minimum Wall Thickness**:
The third Insert Spec value: the plastic wall the insert needs around it. Currently stored
but not used by any geometry.
_Avoid_: min wall, wall

### Geometry

**Target Body**:
The solid body the Bores are cut into. Selected in the dialog (`bodySelect`).
_Avoid_: part, model

**Sketch Point**:
A point in a user sketch that marks a Bore centre. Selected in the dialog (`pointSelect`);
several points may come from different sketches.
_Avoid_: hole point, centre point

**Parent Sketch**:
The user's sketch that owns a Sketch Point. ThreadMeister never modifies it.
_Avoid_: user sketch, source sketch

**Temp Sketch**:
The clean sketch ThreadMeister creates per Sketch Point with `addWithoutEdges`, holding only
the projected point and the Bore circle. Named `TM_<insert>_P<n>`. See ADR-0001.
_Avoid_: helper sketch, bore sketch

**Sketch Plane**:
The plane a sketch lies on. Either a construction plane (origin or user plane) or a planar
face of a body. Only the body-face case is affected by ADR-0002.
_Avoid_: reference plane (that is the Fusion property name, not the concept)

**Bore**:
The cylindrical cut for one Insert: an extrude-cut of the Bore circle into the Target Body.
_Avoid_: hole cut, pocket

**Blind Hole**:
A Bore with a fixed depth: insert length + `blind_hole_extra_depth` + Chamfer size (if
Chamfer is on). See `calc_blind_hole_depth_mm()`.
_Avoid_: pocket, closed hole

**Through Hole**:
A Bore that cuts all the way through the Target Body.
_Avoid_: open hole

**Extrude Direction**:
Which side of the Sketch Plane the Bore goes into — the side where the Target Body is.
Computed by `findExtrudeDirectionFromSketch()`.

**Chamfer**:
Optional bevel on the Bore's entry edge (`chamfer_size`), to guide the Insert in.
_Avoid_: countersink

**Bottom Radius**:
Optional fillet on the floor edge of a Blind Hole (`bottom_radius_size`).
_Avoid_: bottom fillet (in UI text), rounding

### Fusion model

**Timeline Group**:
The timeline group ThreadMeister wraps all features of one run in, named
`(<count>x <insert name>)`.
_Avoid_: feature group, folder

**Body Face**:
A face of a solid body (Fusion API: `BRepFace`, shown in some errors as "BRefFace").
_Avoid_: surface, BRef

### Configuration

**config.ini**:
The user-editable settings file next to the add-in. Sections: `[Settings]` (design
parameters), `[Inserts]` (Insert Library), `[UI State]` (remembered dialog state, auto-saved),
`[Developer]` (debug flags). Details: `docs/development-notes.md`.

**Debug Export**:
Developer option that writes a Temp Sketch's profiles and curves to JSON under
`debug_exports/`, used to build test fixtures. Hidden unless `enable_debug_export = True`.
