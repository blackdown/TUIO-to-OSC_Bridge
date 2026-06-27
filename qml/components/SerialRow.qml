import QtQuick
import QtQuick.Controls.Material
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    property var serialData: Bridge.config.serial_output ?? {}

    height: col.implicitHeight + 16
    width: parent ? parent.width : 300

    Connections {
        target: Bridge
        function onConfigChanged() {
            root.serialData = Bridge.config.serial_output ?? {}
        }
    }

    Column {
        id: col
        anchors {
            left: parent.left; right: parent.right
            leftMargin: 8; rightMargin: 8; top: parent.top; topMargin: 8
        }
        spacing: 12

        // Row 1: enable toggle + label
        RowLayout {
            width: parent.width
            spacing: 4

            Switch {
                id: enableSwitch
                checked: root.serialData.enabled ?? false
                onToggled: Bridge.setSerialEnabled(checked)
                Material.accent: Material.Teal
                scale: 0.65
                Layout.preferredWidth: implicitWidth * scale
                Layout.preferredHeight: implicitHeight * scale
            }

            Label {
                text: "Serial Output"
                font.pixelSize: 12
                font.bold: true
                color: enableSwitch.checked ? "#e0f2f1" : "#546e7a"
                Layout.fillWidth: true
            }
        }

        // Row 2: port selector + refresh
        RowLayout {
            width: parent.width
            spacing: 4
            enabled: enableSwitch.checked

            ComboBox {
                id: portCombo
                model: Bridge.serialPorts.length > 0 ? Bridge.serialPorts : ["(no ports)"]
                currentIndex: {
                    const p = root.serialData.port ?? ""
                    const idx = Bridge.serialPorts.indexOf(p)
                    return idx >= 0 ? idx : 0
                }
                font.pixelSize: 12
                font.family: "monospace"
                Layout.fillWidth: true
                onActivated: {
                    if (Bridge.serialPorts.length > 0)
                        Bridge.setSerialPort(currentText)
                }
                Connections {
                    target: Bridge
                    function onSerialPortsChanged() {
                        portCombo.model = Bridge.serialPorts.length > 0
                            ? Bridge.serialPorts : ["(no ports)"]
                        const p = root.serialData.port ?? ""
                        const idx = Bridge.serialPorts.indexOf(p)
                        portCombo.currentIndex = idx >= 0 ? idx : 0
                    }
                    function onConfigChanged() {
                        const p = root.serialData.port ?? ""
                        const idx = Bridge.serialPorts.indexOf(p)
                        portCombo.currentIndex = idx >= 0 ? idx : 0
                    }
                }
            }

            // Refresh ports button
            Rectangle {
                width: 32; height: 32
                radius: 4
                color: refreshArea.containsMouse ? "#00695c" : Qt.rgba(1,1,1,0.06)
                border.color: Qt.rgba(1,1,1,0.15)
                border.width: 1
                Label {
                    anchors.centerIn: parent
                    text: "↻"
                    font.pixelSize: 16
                    color: "#80cbc4"
                }
                MouseArea {
                    id: refreshArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: Bridge.refreshSerialPorts()
                    ToolTip.visible: containsMouse
                    ToolTip.text: "Refresh port list"
                }
            }
        }

        // Row 3: baud rate
        RowLayout {
            width: parent.width
            spacing: 4
            enabled: enableSwitch.checked

            Label {
                text: "Baud"
                font.pixelSize: 12
                color: "#90a4ae"
                Layout.preferredWidth: 40
            }

            ComboBox {
                id: baudCombo
                model: [9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]
                currentIndex: {
                    const b = root.serialData.baud_rate ?? 115200
                    return model.indexOf(b)
                }
                font.pixelSize: 12
                Layout.fillWidth: true
                onActivated: Bridge.setSerialBaud(parseInt(currentText))
                Connections {
                    target: Bridge
                    function onConfigChanged() {
                        const b = root.serialData.baud_rate ?? 115200
                        baudCombo.currentIndex = baudCombo.model.indexOf(b)
                    }
                }
            }
        }

        // Format note
        Label {
            width: parent.width
            text: 'Format: {"a":"/tuio/cursor/0/x","v":0.42} — one JSON line per message'
            font.pixelSize: 10
            color: "#546e7a"
            wrapMode: Text.WordWrap
            visible: enableSwitch.checked
        }
    }

    Rectangle {
        anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
        height: 1
        color: Qt.rgba(1,1,1,0.07)
    }
}
