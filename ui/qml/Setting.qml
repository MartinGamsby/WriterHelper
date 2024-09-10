import QtQuick 2.15
import QtQuick.Layouts
import QtQuick.Controls

import QtQuick.Controls.Material 2.12

Rectangle {
    id: setting
    property int margin: 6
    property int smallMargin: 6
    
    property string name
    property string desc
    
    implicitWidth: delegateLayout.width+margin*2+smallMargin*2
    implicitHeight: delegateLayout.height+margin*2+smallMargin*2
    
    color: "white"//#eee"
    
    default property alias content: rowLayout.children
    
    Rectangle {
        color: "#eee"//#ceb640
        radius: 5
        
        implicitWidth: delegateLayout.width
        implicitHeight: delegateLayout.height
        anchors.centerIn: parent
        ColumnLayout {
            id: delegateLayout
            width: todoList.width-margin*2-smallMargin-2//1:border right
            
            ColumnLayout {
                spacing: 0//9
                Layout.margins: smallMargin
                Label {
                    text: setting.name
                    Layout.fillWidth: true
                    color: "black"
                    font.pointSize: 12
                    visible: setting.name
                }
                RowLayout {
                    id: rowLayout
                    Layout.fillWidth: true
                    spacing: 9
                    Layout.margins: smallMargin
                }
                Label {
                    text: setting.desc
                    color: "gray"
                    padding: 5
                    visible: setting.desc
                }
            }
          //Rectangle { color: "silver"; height: 1; Layout.fillWidth: true }//SEPARATOR!!
         }
    }
}