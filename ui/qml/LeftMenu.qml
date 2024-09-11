import QtQuick 2.15
import QtQuick.Layouts
import QtQuick.Controls

import QtQuick.Controls.Material 2.12

Flickable {
    id: todoList
    Layout.fillWidth: true
    Layout.fillHeight: true
    
    boundsBehavior: Flickable.StopAtBounds
    contentHeight: 2000// I don't have time for this shit columnLayout.height

    Connections {
        target: backend

        function onInitialized() {
            postsPathEdit.text = root.backend.data().get_posts_folder()
            imageEdit.text = root.backend.data().get_excerpt_image()
        }
    }
                 
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
            enabled: !cbTitle.checked
            
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
            color: cbContent.checked ? "#aaa" : "white"
            TextArea {
                id: contentEdit
                anchors.fill: parent
                text: "Content"
                readOnly: cbContent.checked
                                    
                onEditingFinished: {
                    root.backend.data().set_content(text)
                }
            }
        }
        Button {
            text: "Translate"
            enabled: !cbTranslate.checked
            onClicked: { 
                root.backend.data().translate()
            }
        }
        // TODO: Translate tags
        Setting { 
            name: "Tags"
            Layout.fillWidth: true            
            desc: root.backend? root.backend.get_used_tags() : "Loading"
            TextField {
                id: tagsEdit
                Layout.fillWidth: true
                text: ""                                    
                onEditingFinished: {
                    root.backend.data().set_tags(text)
                }
            }
        }
        Setting { 
            name: "Links"
            
            GridLayout {
                columns: 2
                Label { text: "Medium" }
                TextField {
                    Layout.fillWidth: true
                    text: ""
                                        
                    onEditingFinished: {
                        root.backend.data().set_link("Medium", text)
                    }
                }
                Label { text: "X" }
                TextField {
                    Layout.fillWidth: true
                    text: ""
                                        
                    onEditingFinished: {
                        root.backend.data().set_link("Version courte: X/Twitter", text)
                    }
                }
                Label { text: "[EN] Typeshare" }
                TextField {
                    Layout.fillWidth: true
                    text: ""
                                        
                    onEditingFinished: {
                        root.backend.data().set_link("Version anglaise: Typeshare", text)
                    }
                }
            }
        }
        Setting { 
            name: "Image"
            Layout.fillWidth: true
            
            desc: root.backend? root.backend.data().excerpt_img : "Loading"
            //Image{
            //    source : root.backend.data().excerpt_img_local()
            //    width: 100
            //    height: 100
            //}
            TextField {
                id: imageEdit
                Layout.fillWidth: true
                text: ""                                    
                onEditingFinished: {
                    root.backend.data().set_excerpt_image(text)
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
                       
                onEditingFinished: {
                    root.backend.data().set_posts_folder(text)
                }
            }
        }
        
        //Setting { 
        //    name: "Int select"
        //    desc: "0==x, 1==y"
        //    
        //    SpinBox {
        //        Layout.fillWidth: true
        //        from: 0
        //        to: 1
        //        value: 0
        //        stepSize: 1
        //                            
        //        onValueModified: {
        //            root.backend.data().set_int_select(value)
        //        }            
        //    }
        //}
        //Setting { 
        //    name: "Enable bool"
        //    
        //    CheckBox {
        //        Layout.fillWidth: true
        //        checked: true
        //                            
        //        onToggled: {
        //            root.backend.data().set_bool(checked)
        //        }            
        //    }
        //}
        
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