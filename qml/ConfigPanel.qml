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
                        highlighted: !Bridge.isRunning
                        Material.accent: Bridge.isRunning ? Material.Red : Material.Teal
                        font.pixelSize: 12
                        Layout.preferredWidth: 72
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
                        font.pixelSize: 12
                        Layout.fillWidth: true
                        onValueModified: Bridge.setTuioPort(value)
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
                        model: ["both", "2Dcur", "2Dobj"]
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
                        Layout.fillWidth: true
                        onValueModified: Bridge.setTuioMaxObjects(value)
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
                    model: 4
                    TargetRow {
                        width: parent.width
                        targetIndex: index
                    }
                }
            }

            // ---------------------------------------------------------------
            // Config file actions
            // ---------------------------------------------------------------
            SectionHeader { text: "Config File" }

            RowLayout {
                width: parent.width
                leftPadding: 12; rightPadding: 12; topPadding: 8; bottomPadding: 16
                spacing: 8

                Button {
                    text: "Save Config"
                    flat: false
                    highlighted: true
                    Material.accent: Material.Teal
                    font.pixelSize: 12
                    Layout.fillWidth: true
                    onClicked: Bridge.saveConfig()
                }
                Button {
                    text: "Load Config"
                    flat: true
                    font.pixelSize: 12
                    Layout.fillWidth: true
                    onClicked: Bridge.loadConfig()
                }
            }
        }
    }
}
