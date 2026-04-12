import QtQuick
import QtQuick.Controls.Material
import QtQuick.Controls
import QtQuick.Layouts
import "components"

Pane {
    id: root
    padding: 0
    Material.elevation: 2
    background: Rectangle { color: "#1e2730" }

    // Array of indices — rebuilt whenever target count changes
    property var targetIndices: (function() {
        var a = []; for (var i = 0; i < Bridge.targetCount; i++) a.push(i); return a
    })()
    Connections {
        target: Bridge
        function onTargetCountChanged() {
            var a = []; for (var i = 0; i < Bridge.targetCount; i++) a.push(i)
            root.targetIndices = a
        }
    }

    // -----------------------------------------------------------------------
    // Local helper component: section header bar
    // -----------------------------------------------------------------------
    component SectionHeader: Rectangle {
        property alias text: label.text
        width: parent.width
        height: 32
        color: "#1a2228"

        Label {
            id: label
            anchors { left: parent.left; leftMargin: 12; verticalCenter: parent.verticalCenter }
            font.pixelSize: 11
            font.weight: Font.Medium
            font.letterSpacing: 1.2
            color: "#4db6ac"
            text: ""
        }
        Rectangle {
            anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
            height: 1
            color: Qt.rgba(1,1,1,0.06)
        }
    }

    ScrollView {
        anchors.fill: parent
        contentWidth: availableWidth
        clip: true

        Column {
            width: parent.width
            spacing: 0

            // ---------------------------------------------------------------
            // Header
            // ---------------------------------------------------------------
            Rectangle {
                width: parent.width
                height: 48
                color: "#263238"

                RowLayout {
                    anchors { fill: parent; leftMargin: 16; rightMargin: 8 }
                    Label {
                        text: "Configuration"
                        font.pixelSize: 14
                        font.weight: Font.Medium
                        color: "#e0f2f1"
                        Layout.fillWidth: true
                    }
                    // Start / Stop button
                    Button {
                        text: Bridge.isRunning ? "Stop" : "Start"
                        flat: false
                        highlighted: true
                        Material.accent: Bridge.isRunning ? Material.Red : Material.Teal
                        font.pixelSize: 12
                        font.bold: true
                        Layout.preferredWidth: 100
                        onClicked: Bridge.isRunning ? Bridge.stopBridge() : Bridge.startBridge()
                    }
                }
            }

            // ---------------------------------------------------------------
            // TUIO Input section
            // ---------------------------------------------------------------
            SectionHeader { text: "TUIO Input" }

            Column {
                width: parent.width
                padding: 12
                spacing: 10

                // Port
                RowLayout {
                    width: parent.width - 24
                    Label { text: "Port"; font.pixelSize: 12; color: "#90a4ae"; Layout.preferredWidth: 100 }
                    SpinBox {
                        id: portSpin
                        value: Bridge.config.tuio_input?.port ?? 3333
                        from: 1; to: 65535; stepSize: 1; editable: true
                        locale: Qt.locale("C")
                        font.pixelSize: 12
                        implicitHeight: 32
                        Layout.fillWidth: true
                        onValueModified: Bridge.setTuioPort(value)
                        Component.onCompleted: {
                            if (up.indicator)   up.indicator.implicitWidth   = 24
                            if (down.indicator) down.indicator.implicitWidth = 24
                        }
                        Connections {
                            target: Bridge
                            function onConfigChanged() { portSpin.value = Bridge.config.tuio_input?.port ?? 3333 }
                        }
                    }
                }

                // Listen address
                RowLayout {
                    width: parent.width - 24
                    Label { text: "Listen On"; font.pixelSize: 12; color: "#90a4ae"; Layout.preferredWidth: 100 }
                    TextField {
                        id: addressField
                        text: Bridge.config.tuio_input?.address ?? "0.0.0.0"
                        font.pixelSize: 12
                        font.family: "monospace"
                        Layout.fillWidth: true
                        onEditingFinished: Bridge.setTuioAddress(text)
                        Connections {
                            target: Bridge
                            function onConfigChanged() { addressField.text = Bridge.config.tuio_input?.address ?? "0.0.0.0" }
                        }
                        background: Rectangle {
                            color: Qt.rgba(1,1,1,0.06)
                            radius: 4
                            border.color: addressField.activeFocus ? Material.accentColor : Qt.rgba(1,1,1,0.15)
                            border.width: addressField.activeFocus ? 2 : 1
                        }
                    }
                }

                // Profile
                RowLayout {
                    width: parent.width - 24
                    Label { text: "Profile"; font.pixelSize: 12; color: "#90a4ae"; Layout.preferredWidth: 100 }
                    ComboBox {
                        id: profileCombo
                        model: ["all", "2Dcur", "2Dobj", "2Dblb", "25Dcur", "25Dobj", "25Dblb", "3Dcur", "3Dobj", "3Dblb"]
                        currentIndex: {
                            const p = Bridge.config.tuio_input?.profile ?? "both"
                            return model.indexOf(p) >= 0 ? model.indexOf(p) : 0
                        }
                        font.pixelSize: 12
                        Layout.fillWidth: true
                        onActivated: Bridge.setTuioProfile(currentText)
                        Connections {
                            target: Bridge
                            function onConfigChanged() {
                                const p = Bridge.config.tuio_input?.profile ?? "both"
                                profileCombo.currentIndex = profileCombo.model.indexOf(p) >= 0
                                    ? profileCombo.model.indexOf(p) : 0
                            }
                        }
                    }
                }

                // Max objects
                RowLayout {
                    width: parent.width - 24
                    Label { text: "Max Objects"; font.pixelSize: 12; color: "#90a4ae"; Layout.preferredWidth: 100 }
                    SpinBox {
                        id: maxObjSpin
                        value: Bridge.config.tuio_input?.max_objects ?? 20
                        from: 1; to: 100; stepSize: 1; editable: true
                        font.pixelSize: 12
                        implicitHeight: 32
                        Layout.fillWidth: true
                        onValueModified: Bridge.setTuioMaxObjects(value)
                        Component.onCompleted: {
                            if (up.indicator)   up.indicator.implicitWidth   = 24
                            if (down.indicator) down.indicator.implicitWidth = 24
                        }
                        Connections {
                            target: Bridge
                            function onConfigChanged() { maxObjSpin.value = Bridge.config.tuio_input?.max_objects ?? 20 }
                        }
                    }
                }
            }

            // ---------------------------------------------------------------
            // OSC Output section
            // ---------------------------------------------------------------
            SectionHeader { text: "OSC Output" }

            Column {
                width: parent.width
                padding: 12
                spacing: 10

                // Address template
                RowLayout {
                    width: parent.width - 24
                    Label { text: "Address"; font.pixelSize: 12; color: "#90a4ae"; Layout.preferredWidth: 100 }
                    TextField {
                        id: templateField
                        text: Bridge.config.osc_output?.address_template ?? "/tuio/cursor/{id}"
                        font.pixelSize: 11
                        font.family: "monospace"
                        Layout.fillWidth: true
                        onEditingFinished: Bridge.setAddressTemplate(text)
                        Connections {
                            target: Bridge
                            function onConfigChanged() {
                                templateField.text = Bridge.config.osc_output?.address_template ?? "/tuio/cursor/{id}"
                            }
                        }
                        background: Rectangle {
                            color: Qt.rgba(1,1,1,0.06)
                            radius: 4
                            border.color: templateField.activeFocus ? Material.accentColor : Qt.rgba(1,1,1,0.15)
                            border.width: templateField.activeFocus ? 2 : 1
                        }
                    }
                }

                Label {
                    width: parent.width - 24
                    text: "{id} is replaced with the session ID. The object variant replaces 'cursor' with 'object'."
                    font.pixelSize: 10
                    color: "#546e7a"
                    wrapMode: Text.WordWrap
                }
            }

            // Target rows
            SectionHeader { text: "Targets" }

            Column {
                width: parent.width

                Repeater {
                    model: root.targetIndices
                    TargetRow {
                        width: parent.width
                        targetIndex: modelData
                    }
                }

                // Add target button
                Item {
                    width: parent.width
                    height: 40
                    visible: Bridge.targetCount < 8
                    Button {
                        anchors { left: parent.left; right: parent.right; leftMargin: 8; rightMargin: 8; verticalCenter: parent.verticalCenter }
                        text: "+ Add Target"
                        flat: true
                        font.pixelSize: 12
                        Material.accent: Material.Teal
                        onClicked: Bridge.addTarget()
                    }
                }
            }

            // ---------------------------------------------------------------
            // Config file actions
            // ---------------------------------------------------------------
            SectionHeader { text: "Config File" }

            Item {
                width: parent.width
                height: row.implicitHeight + 24  // 8 top + 16 bottom
                RowLayout {
                    id: row
                    anchors { left: parent.left; right: parent.right; top: parent.top
                              leftMargin: 12; rightMargin: 12; topMargin: 8 }
                    spacing: 8

                    Button {
                        id: saveBtn
                        text: saveTimer.running ? "✓ Saved" : "Save Config"
                        flat: false
                        highlighted: true
                        Material.accent: saveTimer.running ? Material.Green : Material.Teal
                        font.pixelSize: 12
                        Layout.fillWidth: true
                        onClicked: { Bridge.saveConfig(); saveTimer.restart() }
                        Timer { id: saveTimer; interval: 1500 }
                    }
                    Button {
                        id: loadBtn
                        text: loadTimer.running ? "✓ Loaded" : "Load Config"
                        flat: true
                        font.pixelSize: 12
                        Layout.fillWidth: true
                        onClicked: { Bridge.loadConfig(); loadTimer.restart() }
                        Timer { id: loadTimer; interval: 1500 }
                    }
                }
            }

            // ---------------------------------------------------------------
            // Credits
            // ---------------------------------------------------------------
            Rectangle {
                width: parent.width
                height: creditCol.implicitHeight + 20
                color: "transparent"

                Column {
                    id: creditCol
                    anchors { left: parent.left; right: parent.right; top: parent.top
                              leftMargin: 12; rightMargin: 12; topMargin: 10 }
                    spacing: 4

                    Label {
                        text: "© 2026 Antony Bailey"
                        font.pixelSize: 10
                        color: "#546e7a"
                    }
                    Label {
                        text: "github.com/blackdown"
                        font.pixelSize: 10
                        color: "#4db6ac"
                        font.underline: true
                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: Qt.openUrlExternally("https://github.com/blackdown")
                        }
                    }
                }
            }
        }
    }
}
