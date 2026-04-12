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
            text: "Swap X\u2194Y"
            checked: root.targetData.swap_axes ?? false
            font.pixelSize: 11
            onToggled: Bridge.setTargetSwapAxes(root.targetIndex, checked)
            Material.accent: Material.Teal
            Layout.columnSpan: 2
        }

        // --- Scale row ---
        Label { text: "Scale X"; font.pixelSize: 11; color: "#90a4ae" }
        FloatField {
            id: scaleXField
            value: root.targetData.scale_x ?? 1.0
            Layout.fillWidth: true
            onCommitted: (v) => Bridge.setTargetScaleX(root.targetIndex, v)
        }
        Label { text: "Scale Y"; font.pixelSize: 11; color: "#90a4ae" }
        FloatField {
            id: scaleYField
            value: root.targetData.scale_y ?? 1.0
            Layout.fillWidth: true
            onCommitted: (v) => Bridge.setTargetScaleY(root.targetIndex, v)
        }

        // --- Offset row ---
        Label { text: "Offset X"; font.pixelSize: 11; color: "#90a4ae" }
        FloatField {
            id: offsetXField
            value: root.targetData.offset_x ?? 0.0
            minValue: -100.0
            maxValue: 100.0
            Layout.fillWidth: true
            onCommitted: (v) => Bridge.setTargetOffsetX(root.targetIndex, v)
        }
        Label { text: "Offset Y"; font.pixelSize: 11; color: "#90a4ae" }
        FloatField {
            id: offsetYField
            value: root.targetData.offset_y ?? 0.0
            minValue: -100.0
            maxValue: 100.0
            Layout.fillWidth: true
            onCommitted: (v) => Bridge.setTargetOffsetY(root.targetIndex, v)
        }
    }

    // Update when config reloads
    Connections {
        target: Bridge
        function onConfigChanged() {
            flipXBox.checked    = root.targetData.flip_x    ?? false
            flipYBox.checked    = root.targetData.flip_y    ?? false
            swapBox.checked     = root.targetData.swap_axes ?? false
            scaleXField.value   = root.targetData.scale_x   ?? 1.0
            scaleYField.value   = root.targetData.scale_y   ?? 1.0
            offsetXField.value  = root.targetData.offset_x  ?? 0.0
            offsetYField.value  = root.targetData.offset_y  ?? 0.0
        }
    }

    // -----------------------------------------------------------------------
    // Inline float input component (no external dependency)
    // -----------------------------------------------------------------------
    component FloatField: TextField {
        property real value: 0.0
        property real minValue: 0.0
        property real maxValue: 10.0
        signal committed(real v)

        text: value.toFixed(3)
        font.pixelSize: 11
        font.family: "monospace"
        horizontalAlignment: Text.AlignHCenter
        height: 26

        validator: DoubleValidator {
            bottom: minValue
            top: maxValue
            decimals: 3
            notation: DoubleValidator.StandardNotation
        }

        onEditingFinished: {
            const v = parseFloat(text)
            if (!isNaN(v)) {
                const clamped = Math.max(minValue, Math.min(maxValue, v))
                value = clamped
                text = clamped.toFixed(3)
                committed(clamped)
            }
        }

        onValueChanged: {
            if (!activeFocus)
                text = value.toFixed(3)
        }

        background: Rectangle {
            color: Qt.rgba(1,1,1,0.06)
            radius: 3
            border.color: parent.activeFocus ? Material.accentColor : Qt.rgba(1,1,1,0.12)
            border.width: parent.activeFocus ? 2 : 1
        }
    }
}
