import QtQuick
import QtQuick.Controls.Material
import QtQuick.Controls
import QtQuick.Layouts

Pane {
    id: root
    padding: 0
    background: Rectangle { color: "#18222a" }

    Column {
        anchors.fill: parent

        // ---- Panel title bar ----
        Rectangle {
            width: parent.width
            height: 48
            color: "#263238"

            RowLayout {
                anchors { fill: parent; leftMargin: 16; rightMargin: 16 }
                Label {
                    text: "Live Monitor"
                    font.pixelSize: 14
                    font.weight: Font.Medium
                    color: "#e0f2f1"
                    Layout.fillWidth: true
                }
                Label {
                    text: "Active: " + Bridge.activeCount + " / " +
                          (Bridge.config.tuio_input?.max_objects ?? 20)
                    font.pixelSize: 12
                    color: "#80cbc4"
                }
            }
        }

        // ---- Column headers ----
        Rectangle {
            width: parent.width
            height: 28
            color: "#1a2228"

            Row {
                anchors { fill: parent; leftMargin: 8 }
                spacing: 0

                Repeater {
                    model: [
                        { label: "ID",       width: 50 },
                        { label: "Type",     width: 52 },
                        { label: "X",        width: 70 },
                        { label: "Y",        width: 70 },
                        { label: "X Vel",    width: 70 },
                        { label: "Y Vel",    width: 70 },
                        { label: "Accel",    width: 70 },
                        { label: "Angle",    width: 70 },
                        { label: "Class",    width: 52 },
                        { label: "Life (s)", width: 64 },
                    ]
                    Label {
                        width: modelData.width
                        height: 28
                        text: modelData.label
                        font.pixelSize: 11
                        font.weight: Font.Medium
                        font.letterSpacing: 0.8
                        color: "#4db6ac"
                        verticalAlignment: Text.AlignVCenter
                        elide: Text.ElideRight
                    }
                }
            }

            Rectangle {
                anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
                height: 1
                color: Qt.rgba(1,1,1,0.10)
            }
        }

        // ---- Data rows ----
        ListView {
            id: listView
            width: parent.width
            height: root.height - 48 - 28
            model: Bridge.cursorModel
            clip: true

            // Empty state
            Label {
                anchors.centerIn: parent
                visible: listView.count === 0
                text: Bridge.isRunning
                    ? "Waiting for touch input..."
                    : "Bridge stopped.\nPress Start to begin listening."
                font.pixelSize: 13
                color: "#37474f"
                horizontalAlignment: Text.AlignHCenter
                lineHeight: 1.5
            }

            add: Transition {
                NumberAnimation { property: "opacity"; from: 0; to: 1; duration: 120 }
                NumberAnimation { property: "y"; from: y - 8; duration: 120; easing.type: Easing.OutCubic }
            }
            remove: Transition {
                NumberAnimation { property: "opacity"; to: 0; duration: 100 }
            }
            displaced: Transition {
                NumberAnimation { properties: "y"; duration: 120; easing.type: Easing.OutCubic }
            }

            delegate: Rectangle {
                id: rowDelegate
                required property int index
                required property int sessionId
                required property string objectType
                required property real posX
                required property real posY
                required property real xVel
                required property real yVel
                required property real accel
                required property real angle
                required property int classId
                required property real lifetime

                width: listView.width
                height: 32
                color: rowDelegate.index % 2 === 0 ? "#1e2d36" : "#192430"

                Row {
                    anchors { fill: parent; leftMargin: 8 }

                    // ID
                    Label { width: 50;  height: rowDelegate.height; text: rowDelegate.sessionId.toString(); font.pixelSize: 12; font.family: "monospace"; color: "#80cbc4"; verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight }
                    // Type
                    Label { width: 52;  height: rowDelegate.height; text: rowDelegate.objectType; font.pixelSize: 12; font.family: "monospace"; color: rowDelegate.objectType === "object" ? "#ffb74d" : "#90caf9"; verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight }
                    // X
                    Label { width: 70;  height: rowDelegate.height; text: rowDelegate.posX.toFixed(4); font.pixelSize: 12; font.family: "monospace"; color: "#cfd8dc"; verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight }
                    // Y
                    Label { width: 70;  height: rowDelegate.height; text: rowDelegate.posY.toFixed(4); font.pixelSize: 12; font.family: "monospace"; color: "#cfd8dc"; verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight }
                    // X Vel
                    Label { width: 70;  height: rowDelegate.height; text: rowDelegate.xVel.toFixed(4); font.pixelSize: 12; font.family: "monospace"; color: "#cfd8dc"; verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight }
                    // Y Vel
                    Label { width: 70;  height: rowDelegate.height; text: rowDelegate.yVel.toFixed(4); font.pixelSize: 12; font.family: "monospace"; color: "#cfd8dc"; verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight }
                    // Accel
                    Label { width: 70;  height: rowDelegate.height; text: rowDelegate.accel.toFixed(4); font.pixelSize: 12; font.family: "monospace"; color: "#cfd8dc"; verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight }
                    // Angle
                    Label { width: 70;  height: rowDelegate.height; text: rowDelegate.angle.toFixed(4); font.pixelSize: 12; font.family: "monospace"; color: "#cfd8dc"; verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight }
                    // Class
                    Label { width: 52;  height: rowDelegate.height; text: rowDelegate.classId >= 0 ? rowDelegate.classId.toString() : "—"; font.pixelSize: 12; font.family: "monospace"; color: "#cfd8dc"; verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight }
                    // Lifetime
                    Label { width: 64;  height: rowDelegate.height; text: rowDelegate.lifetime.toFixed(1) + "s"; font.pixelSize: 12; font.family: "monospace"; color: "#546e7a"; verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight }
                }

                // Row separator
                Rectangle {
                    anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
                    height: 1
                    color: Qt.rgba(1,1,1,0.04)
                }
            }

            ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
        }
    }
}
