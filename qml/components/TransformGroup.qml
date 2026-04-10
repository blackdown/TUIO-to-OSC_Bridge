import QtQuick
import QtQuick.Controls.Material
import QtQuick.Controls
import QtQuick.Layouts

/*
  TransformGroup — flip/swap/scale/offset controls for one OSC target.
  Required properties: targetIndex (int), targetData (var)
*/
Item {
    id: root
    required property int targetIndex
    required property var targetData

    height: grid.implicitHeight + 4

    GridLayout {
        id: grid
        anchors { left: parent.left; right: parent.right; leftMargin: 62 }
        columns: 4
        columnSpacing: 8
        rowSpacing: 4

        // --- Flip / Swap row ---
        CheckBox {
            id: flipXBox
            text: "Flip X"
            checked: root.targetData.flip_x ?? false
            font.pixelSize: 11
            onToggled: Bridge.setTargetFlipX(root.targetIndex, checked)
            Material.accent: Material.Teal
        }
        CheckBox {
            id: flipYBox
            text: "Flip Y"
            checked: root.targetData.flip_y ?? false
            font.pixelSize: 11
            onToggled: Bridge.setTargetFlipY(root.targetIndex, checked)
            Material.accent: Material.Teal
        }
        CheckBox {
            id: swapBox
            text: "Swap X↔Y"
            checked: root.targetData.swap_axes ?? false
            font.pixelSize: 11
            onToggled: Bridge.setTargetSwapAxes(root.targetIndex, checked)
            Material.accent: Material.Teal
            Layout.columnSpan: 2
        }

        // --- Scale row ---
        Label { text: "Scale X"; font.pixelSize: 11; color: "#90a4ae" }
        DoubleSpinBox {
            id: scaleXSpin
            realValue: root.targetData.scale_x ?? 1.0
            Layout.fillWidth: true
            onValueModified: Bridge.setTargetScaleX(root.targetIndex, realValue)
        }
        Label { text: "Scale Y"; font.pixelSize: 11; color: "#90a4ae" }
        DoubleSpinBox {
            id: scaleYSpin
            realValue: root.targetData.scale_y ?? 1.0
            Layout.fillWidth: true
            onValueModified: Bridge.setTargetScaleY(root.targetIndex, realValue)
        }

        // --- Offset row ---
        Label { text: "Offset X"; font.pixelSize: 11; color: "#90a4ae" }
        DoubleSpinBox {
            id: offsetXSpin
            realValue: root.targetData.offset_x ?? 0.0
            realFrom: -100.0
            realTo: 100.0
            Layout.fillWidth: true
            onValueModified: Bridge.setTargetOffsetX(root.targetIndex, realValue)
        }
        Label { text: "Offset Y"; font.pixelSize: 11; color: "#90a4ae" }
        DoubleSpinBox {
            id: offsetYSpin
            realValue: root.targetData.offset_y ?? 0.0
            realFrom: -100.0
            realTo: 100.0
            Layout.fillWidth: true
            onValueModified: Bridge.setTargetOffsetY(root.targetIndex, realValue)
        }
    }

    // Update when config reloads
    Connections {
        target: Bridge
        function onConfigChanged() {
            flipXBox.checked       = root.targetData.flip_x   ?? false
            flipYBox.checked       = root.targetData.flip_y   ?? false
            swapBox.checked        = root.targetData.swap_axes ?? false
            scaleXSpin.realValue   = root.targetData.scale_x  ?? 1.0
            scaleYSpin.realValue   = root.targetData.scale_y  ?? 1.0
            offsetXSpin.realValue  = root.targetData.offset_x ?? 0.0
            offsetYSpin.realValue  = root.targetData.offset_y ?? 0.0
        }
    }
}
