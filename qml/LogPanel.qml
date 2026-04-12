import QtQuick
import QtQuick.Controls.Material
import QtQuick.Controls
import QtQuick.Layouts

Pane {
    id: root
    padding: 0
    background: Rectangle { color: "#141e25" }

    property bool paused: false

    Column {
        anchors.fill: parent

        // ---- Panel title bar ----
        Rectangle {
            width: parent.width
            height: 48
            color: "#263238"

            RowLayout {
                anchors { fill: parent; leftMargin: 12; rightMargin: 8 }
                spacing: 6

                Label {
                    text: "OSC Log"
                    font.pixelSize: 14
                    font.weight: Font.Medium
                    color: "#e0f2f1"
                    Layout.fillWidth: true
                }

                Label {
                    text: Bridge.msgPerSec.toFixed(0) + " msg/s"
                    font.pixelSize: 11
                    color: "#546e7a"
                }

                // Pause toggle
                Button {
                    text: root.paused ? "▶" : "⏸"
                    flat: true
                    font.pixelSize: 14
                    Layout.preferredWidth: 36
                    ToolTip.visible: hovered
                    ToolTip.text: root.paused ? "Resume log" : "Pause log"
                    onClicked: {
                        root.paused = !root.paused
                        Bridge.logModel.setPaused(root.paused)
                    }
                }

                // Clear button
                Button {
                    text: "✕"
                    flat: true
                    font.pixelSize: 13
                    Layout.preferredWidth: 36
                    ToolTip.visible: hovered
                    ToolTip.text: "Clear log"
                    onClicked: Bridge.logModel.clear()
                }
            }
        }

        // ---- Filter bar ----
        Rectangle {
            width: parent.width
            height: 36
            color: "#1a2228"

            RowLayout {
                anchors { fill: parent; leftMargin: 10; rightMargin: 10 }
                spacing: 6

                Label {
                    text: "Filter:"
                    font.pixelSize: 11
                    color: "#546e7a"
                }

                TextField {
                    id: filterField
                    placeholderText: "e.g. /tuio/cursor"
                    font.pixelSize: 11
                    font.family: "monospace"
                    Layout.fillWidth: true
                    height: 26
                    onTextChanged: Bridge.logModel.setFilter(text)
                    background: Rectangle {
                        color: Qt.rgba(1,1,1,0.05)
                        radius: 3
                        border.color: filterField.activeFocus ? Material.accentColor : Qt.rgba(1,1,1,0.12)
                        border.width: filterField.activeFocus ? 2 : 1
                    }
                }

                // Clear filter
                Button {
                    visible: filterField.text.length > 0
                    text: "✕"
                    flat: true
                    font.pixelSize: 11
                    Layout.preferredWidth: 28
                    onClicked: filterField.text = ""
                }
            }

            Rectangle {
                anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
                height: 1
                color: Qt.rgba(1,1,1,0.06)
            }
        }

        // ---- Log list ----
        ListView {
            id: logList
            width: parent.width
            height: root.height - 48 - 36
            model: Bridge.logModel
            clip: true
            verticalLayoutDirection: ListView.BottomToTop   // newest at bottom

            // Empty state
            Label {
                anchors.centerIn: parent
                visible: logList.count === 0
                text: Bridge.isRunning ? "No OSC messages yet..." : "Start the bridge to see OSC output."
                font.pixelSize: 12
                color: "#2e3f4a"
            }

            add: Transition {
                NumberAnimation { property: "opacity"; from: 0; to: 1; duration: 80 }
            }

            delegate: Rectangle {
                id: logRow
                required property int index
                required property string address
                required property string value
                required property string timestamp

                width: logList.width
                height: 22
                color: logRow.index % 2 === 0 ? "#141e25" : "#111b22"

                RowLayout {
                    anchors { fill: parent; leftMargin: 8; rightMargin: 8 }
                    spacing: 8

                    Label {
                        text: logRow.timestamp
                        font.pixelSize: 10
                        font.family: "monospace"
                        color: "#37474f"
                        Layout.preferredWidth: 60
                    }

                    Label {
                        text: logRow.address
                        font.pixelSize: 11
                        font.family: "monospace"
                        color: "#4db6ac"
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                    }

                    Label {
                        text: logRow.value
                        font.pixelSize: 11
                        font.family: "monospace"
                        color: "#b0bec5"
                        Layout.preferredWidth: 80
                        horizontalAlignment: Text.AlignRight
                        elide: Text.ElideLeft
                    }
                }
            }

            // Auto-scroll to newest (bottom) unless user scrolled up
            onCountChanged: {
                if (!root.paused) {
                    logList.positionViewAtBeginning()  // BottomToTop: "beginning" = bottom visually
                }
            }

            ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
        }
    }
}
