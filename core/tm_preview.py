"""
tm_preview.py – Bore Preview: PreviewHandler for the command's executePreview event.

Runs the same Bore code as OK (tm_execute.runBores). Fusion rolls the features back when the
preview ends. The removed material (body before - body after) is drawn translucent red.
Silent: no message boxes, no Timeline Group, no config save.
"""
import adsk.core, adsk.fusion
from . import tm_state
from . import tm_ridge
from .tm_execute import BoreParams, runBores

PREVIEW_RED = (255, 0, 0, 255)
PREVIEW_OPACITY = 0.4


def removedMaterial(before, after):
    """Return before - after as a temporary BRepBody, or None when nothing was removed."""
    brepMgr = adsk.fusion.TemporaryBRepManager.get()
    if not brepMgr.booleanOperation(
            before, after, adsk.fusion.BooleanTypes.DifferenceBooleanType):
        return None
    return before


def drawRemoved(component, removed):
    """Draw the removed material red and translucent in a CustomGraphicsGroup."""
    group = component.customGraphicsGroups.add()
    graphicsBody = group.addBRepBody(removed)
    graphicsBody.color = adsk.fusion.CustomGraphicsSolidColorEffect.create(
        adsk.core.Color.create(*PREVIEW_RED))
    graphicsBody.setOpacity(PREVIEW_OPACITY, True)


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

            brepMgr = adsk.fusion.TemporaryBRepManager.get()
            before = brepMgr.copy(targetBody)

            params = BoreParams(inputs)
            params.shouldExport = False
            result = runBores(targetBody, points, params)
            if result.successCount == 0:
                return

            after = brepMgr.copy(targetBody)
            removed = removedMaterial(before, after)
            if removed is not None:
                drawRemoved(targetBody.parentComponent, removed)
        except Exception:
            # Silent by design (D4): errors are reported only on OK.
            pass
