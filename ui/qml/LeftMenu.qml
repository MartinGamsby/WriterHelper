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
            desc: root.backend? root.backend.data().slug : "Loading"
            
            TextField {
                id: titleEdit
                Layout.fillWidth: true
                text: "Title"
                                    
                onEditingFinished: {
                    root.backend.data().set_title(text)
                }
            }
        }
        Rectangle {
            width: parent.width
            height: 400
            TextArea {
                id: contentEdit
                anchors.fill: parent
                text: "Content"
                                    
                onEditingFinished: {
                    root.backend.data().set_content(text)
                }
            }
        }        
        
        Setting { 
            name: "Posts path"
            Layout.fillWidth: true
            
            TextField {
                id: postsPathEdit
                Layout.fillWidth: true
                text: "."
                
                Connections {
                    target: backend

                    function onInitialized() {
                        postsPathEdit.text = root.backend.data().get_posts_folder()
                    }
                }
                                    
                onEditingFinished: {
                    root.backend.data().set_posts_path(text)
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
                    root.backend.data().set_int_select(value)
                }            
            }
        }
        Setting { 
            name: "Enable bool"
            
            CheckBox {
                Layout.fillWidth: true
                checked: true
                                    
                onToggled: {
                    root.backend.data().set_bool(checked)
                }            
            }
        }
        
        Label {
                Layout.fillHeight: true            
        }
        Timer {
            id: timer
            interval: 1000 // 3000
            running: true
            repeat: true
            onTriggered: {
                contentEdit.onEditingFinished()
                titleEdit.onEditingFinished()
            }
        }
    }
}