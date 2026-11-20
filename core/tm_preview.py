"""
tm_preview.py – Bore Preview: PreviewHandler for the command's executePreview event.

Runs the same Bore code as OK (tm_execute.runBores). Fusion shows the real cut as its own
preview and rolls the features back when the preview ends.
Silent: no message boxes, no Timeline Group, no config save.
"""
import adsk.core
from . import tm_ridge
from .tm_execute import BoreParams, runBores

def inputsReady(inputs):
    """Show Preview on, a Target Body and a Sketch Point selected, Ridge depth usable."""
    showPreview = inputs.itemById('showPreview')
    if showPreview is None or not showPreview.value:
        return False
    if inputs.itemById('bodySelect').selectionCount == 0:
        return False
    if inputs.itemById('pointSelect').selectionCount == 0:
        return False
    isBlind = inputs.itemById('holeType').selectedItem.name == 'Blind Hole'
    if (inputs.itemById('boreType').selectedItem.name == tm_ridge.BORE_TYPE_RIDGE
            and isBlind and inputs.itemById('ridgeDepth').value <= 0):
        return False
    return True


class PreviewHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            inputs = args.command.commandInputs
            if not inputsReady(inputs):
                return

            targetBody = inputs.itemById('bodySelect').selection(0).entity
            pointSelect = inputs.itemById('pointSelect')
            points = [pointSelect.selection(i).entity for i in range(pointSelect.selectionCount)]

            params = BoreParams(inputs)
            params.shouldExport = False
            # The Bores stay in the design while the preview runs: Fusion draws them
            # itself and rolls them back when the preview ends (no zebra stripes).
            runBores(targetBody, points, params)
        except Exception:
            # Silent by design (D4): errors are reported only on OK.
            pass
