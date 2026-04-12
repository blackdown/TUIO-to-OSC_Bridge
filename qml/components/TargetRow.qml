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

    property int targetIndex: 0

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
        anchors { left: parent.left; right: parent.right; leftMargin: 8; rightMargin: 8; top: parent.top; topMargin: 8 }
        spacing: 12

        // Row 1: enable toggle + label + test button
        RowLayout {
            width: parent.width
            spacing: 4

            Switch {
                id: enableSwitch
                checked: root.targetData.enabled ?? false
                onToggled: Bridge.setTargetEnabled(root.targetIndex, checked)
                Material.accent: Material.Teal
                scale: 0.65
                Layout.preferredWidth: implicitWidth * scale
                Layout.preferredHeight: implicitHeight * scale
            }

            Label {
                text: "Target " + (root.targetIndex + 1)
                font.pixelSize: 12
                font.bold: true
                color: enableSwitch.checked ? "#e0f2f1" : "#546e7a"
                Layout.fillWidth: true
            }

            Rectangle {
                width: 44; height: 24
                radius: 4
                opacity: enableSwitch.checked ? 1.0 : 0.35
                color: testArea.containsMouse && enableSwitch.checked ? "#00695c" : "#00796b"
                border.color: "#80cbc4"
                border.width: 1
                Label {
                    anchors.centerIn: parent
                    text: "Test"
                    font.pixelSize: 11
                    font.bold: true
                    color: "#ffffff"
                }
                MouseArea {
                    id: testArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: enableSwitch.checked ? Qt.PointingHandCursor : Qt.ArrowCursor
                    enabled: enableSwitch.checked
                    onClicked: {
                        const ok = Bridge.sendTestMessage(root.targetIndex)
                        testFeedback.visible = ok
                        testFeedbackTimer.restart()
                    }
                    ToolTip.visible: containsMouse
                    ToolTip.text: "Send a test OSC message"
                }
            }
            Rectangle {
                width: 24; height: 24
                radius: 4
                color: removeArea.containsMouse ? "#b71c1c" : "#c62828"
                border.color: "#ef9a9a"
                border.width: 1
                Label {
                    anchors.centerIn: parent
                    text: "✕"
                    font.pixelSize: 12
                    font.bold: true
                    color: "#ffffff"
                }
                MouseArea {
                    id: removeArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: Bridge.removeTarget(root.targetIndex)
                    ToolTip.visible: containsMouse
                    ToolTip.text: "Remove this target"
                }
            }
        }

        // Row 2: IP + Port
        RowLayout {
            width: parent.width
            spacing: 4
            enabled: enableSwitch.checked

            TextField {
                id: ipField
                text: root.targetData.ip ?? "127.0.0.1"
                placeholderText: "IP"
                font.pixelSize: 12
                font.family: "monospace"
                Layout.fillWidth: true
                implicitHeight: 32
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
                editable: true
                locale: Qt.locale("C")
                Layout.preferredWidth: 110
                implicitHeight: 32
                font.pixelSize: 12
                onValueModified: Bridge.setTargetPort(root.targetIndex, value)
                Component.onCompleted: {
                    if (up.indicator)   up.indicator.implicitWidth   = 24
                    if (down.indicator) down.indicator.implicitWidth = 24
                }
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
        }

        // Test feedback flash
        Label {
            id: testFeedback
            visible: false
            text: "✓ Sent /tuio/bridge/test"
            font.pixelSize: 10
            color: "#80cbc4"
            Timer {
                id: testFeedbackTimer
                interval: 2000
                onTriggered: testFeedback.visible = false
            }
        }

        // Row 3: transforms (only when enabled)
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
