import QtQuick
import QtQuick.Controls.Material
import QtQuick.Controls
import QtQuick.Layouts

/*
  TargetRow — one OSC output target row.
  Required property: targetIndex (int 0-3)
*/
Item {
    id: root

    required property int targetIndex

    property var targetData: Bridge.config.osc_output.targets[targetIndex] ?? {}

    height: col.implicitHeight + 16
    width: parent ? parent.width : 300

    Connections {
        target: Bridge
        function onConfigChanged() {
            root.targetData = Bridge.config.osc_output.targets[root.targetIndex] ?? {}
        }
    }

    Column {
        id: col
        anchors { left: parent.left; right: parent.right; top: parent.top; topMargin: 8 }
        spacing: 6

        // Row 1: enable toggle + IP + port + test button
        RowLayout {
            width: parent.width
            spacing: 6

            Switch {
                id: enableSwitch
                checked: root.targetData.enabled ?? false
                onToggled: Bridge.setTargetEnabled(root.targetIndex, checked)
                Material.accent: Material.Teal
            }

            Label {
                text: "Target " + (root.targetIndex + 1)
                font.pixelSize: 12
                font.bold: true
                color: enableSwitch.checked ? "#e0f2f1" : "#546e7a"
                Layout.preferredWidth: 56
            }

            TextField {
                id: ipField
                text: root.targetData.ip ?? "127.0.0.1"
                placeholderText: "IP address"
                font.pixelSize: 12
                font.family: "monospace"
                enabled: enableSwitch.checked
                Layout.fillWidth: true
                onEditingFinished: Bridge.setTargetIp(root.targetIndex, text)
                background: Rectangle {
                    color: ipField.enabled ? Qt.rgba(1,1,1,0.06) : Qt.rgba(1,1,1,0.02)
                    radius: 4
                    border.color: ipField.activeFocus ? Material.accentColor : Qt.rgba(1,1,1,0.15)
                    border.width: ipField.activeFocus ? 2 : 1
                }
            }

            SpinBox {
                id: portSpin
                value: root.targetData.port ?? 7000
                from: 1
                to: 65535
                stepSize: 1
                enabled: enableSwitch.checked
                editable: true
                Layout.preferredWidth: 90
                font.pixelSize: 12
                onValueModified: Bridge.setTargetPort(root.targetIndex, value)
                contentItem: TextInput {
                    text: portSpin.textFromValue(portSpin.value, portSpin.locale)
                    font: portSpin.font
                    color: portSpin.enabled ? "#e0e0e0" : "#546e7a"
                    horizontalAlignment: Qt.AlignHCenter
                    verticalAlignment: Qt.AlignVCenter
                    readOnly: !portSpin.editable
                    validator: portSpin.validator
                    inputMethodHints: Qt.ImhFormattedNumbersOnly
                }
            }

            Button {
                text: "Test"
                flat: true
                enabled: enableSwitch.checked
                Layout.preferredWidth: 48
                font.pixelSize: 11
                Material.accent: Material.Teal
                onClicked: {
                    const ok = Bridge.sendTestMessage(root.targetIndex)
                    testFeedback.visible = ok
                    testFeedbackTimer.restart()
                }
                ToolTip.visible: hovered
                ToolTip.text: "Send a test OSC message"
            }
        }

        // Test feedback flash
        Label {
            id: testFeedback
            visible: false
            text: "✓ Sent /tuio/bridge/test"
            font.pixelSize: 10
            color: "#80cbc4"
            leftPadding: 62
            Timer {
                id: testFeedbackTimer
                interval: 2000
                onTriggered: testFeedback.visible = false
            }
        }

        // Row 2: transforms (only when enabled)
        TransformGroup {
            visible: enableSwitch.checked
            width: parent.width
            targetIndex: root.targetIndex
            targetData: root.targetData
        }
    }

    // Separator line
    Rectangle {
        anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
        height: 1
        color: Qt.rgba(1,1,1,0.07)
    }
}
