import QtQuick
import QtQuick.Controls.Material
import QtQuick.Controls

/*
  DoubleSpinBox — a simple float input field with +/- buttons.
  Properties: realValue (real), realFrom (real), realTo (real)
  Signal:     valueModified()  — emitted when user commits a change
*/
Item {
    id: control

    property real realValue: 1.0
    property real realFrom:  0.0
    property real realTo:    10.0

    signal valueModified()

    implicitHeight: 28
    implicitWidth: 100

    // Sync display when realValue is set externally (e.g. config reload)
    onRealValueChanged: {
        if (!field.activeFocus)
            field.text = realValue.toFixed(3)
    }

    Row {
        anchors.fill: parent
        spacing: 0

        // Decrement button
        Rectangle {
            width: 22; height: parent.height
            color: decMa.containsMouse ? Qt.rgba(1,1,1,0.10) : Qt.rgba(1,1,1,0.05)
            radius: 3
            Label {
                anchors.centerIn: parent
                text: "−"
                font.pixelSize: 14
                color: "#90a4ae"
            }
            MouseArea {
                id: decMa
                anchors.fill: parent
                hoverEnabled: true
                onClicked: {
                    const next = Math.max(control.realFrom, control.realValue - 0.1)
                    control.realValue = Math.round(next * 1000) / 1000
                    field.text = control.realValue.toFixed(3)
                    control.valueModified()
                }
            }
        }

        // Text field
        TextField {
            id: field
            width: parent.width - 44
            height: parent.height
            text: control.realValue.toFixed(3)
            font.pixelSize: 11
            font.family: "monospace"
            horizontalAlignment: Text.AlignHCenter
            leftPadding: 4; rightPadding: 4

            validator: DoubleValidator {
                bottom: control.realFrom
                top:    control.realTo
                decimals: 3
                notation: DoubleValidator.StandardNotation
            }

            background: Rectangle {
                color: Qt.rgba(1,1,1,0.06)
                border.color: field.activeFocus ? Material.accentColor : Qt.rgba(1,1,1,0.12)
                border.width: field.activeFocus ? 2 : 1
            }

            onEditingFinished: {
                const v = parseFloat(text)
                if (!isNaN(v)) {
                    control.realValue = Math.max(control.realFrom, Math.min(control.realTo, v))
                    text = control.realValue.toFixed(3)
                    control.valueModified()
                }
            }
        }

        // Increment button
        Rectangle {
            width: 22; height: parent.height
            color: incMa.containsMouse ? Qt.rgba(1,1,1,0.10) : Qt.rgba(1,1,1,0.05)
            radius: 3
            Label {
                anchors.centerIn: parent
                text: "+"
                font.pixelSize: 14
                color: "#90a4ae"
            }
            MouseArea {
                id: incMa
                anchors.fill: parent
                hoverEnabled: true
                onClicked: {
                    const next = Math.min(control.realTo, control.realValue + 0.1)
                    control.realValue = Math.round(next * 1000) / 1000
                    field.text = control.realValue.toFixed(3)
                    control.valueModified()
                }
            }
        }
    }
}
