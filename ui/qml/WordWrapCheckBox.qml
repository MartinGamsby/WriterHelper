import QtQuick 2.15
import QtQuick.Layouts
import QtQuick.Controls
import "."

// not Material...
import QtQuick.Controls.Imagine 2.12

CheckBox {    
    id: myCheckBox
    implicitWidth: parent.parent.width
    Layout.leftMargin: 6
    Layout.topMargin: 3
    contentItem: Label {
        text: myCheckBox.text
        font: myCheckBox.font
        horizontalAlignment: Text.AlignLeft
        verticalAlignment: Text.AlignVCenter
        //padding: 0
        leftPadding: myCheckBox.indicator.width + myCheckBox.spacing
        wrapMode: Label.Wrap
    }
}