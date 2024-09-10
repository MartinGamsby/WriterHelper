import QtQuick 2.15
import QtQuick.Layouts
import QtQuick.Controls

import QtQuick.Controls.Material 2.12

Flickable {
    id: todoList
    Layout.fillWidth: true
    Layout.fillHeight: true
    
    boundsBehavior: Flickable.StopAtBounds
    contentHeight: 1000// I don't have time for this shit columnLayout.height
    
    ColumnLayout
    {
        id: columnLayout
        anchors.fill: parent
        anchors.margins: 0
        Label {
            text: "Settings"
            width: parent.width
            horizontalAlignment: Text.AlignHCenter
            font.pointSize: 15
            padding: 5
        }
        
        Setting { 
            name: "Title"
            Layout.fillWidth: true            
            //desc: ""
            
            TextInput {
                Layout.fillWidth: true
                text: "text"
                                    
                onEditingFinished: {
                    root.backend.set_title(text)
                }
            }
        }
        
        Setting { 
            name: "Int select"
            desc: "0==x, 1==y"
            
            SpinBox {
                Layout.fillWidth: true
                from: 0
                to: 1
                value: 0
                stepSize: 1
                                    
                onValueModified: {
                    root.backend.set_int_select(value)
                }            
            }
        }
        Setting { 
            name: "Enable bool"
            
            CheckBox {
                Layout.fillWidth: true
                checked: true
                                    
                onToggled: {
                    root.backend.set_bool(checked)
                }            
            }
        }
        
        Label {
                Layout.fillHeight: true            
        }
    }
}