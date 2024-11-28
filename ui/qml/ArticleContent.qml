import QtQuick 2.15
import QtQuick.Layouts
import QtQuick.Controls

import QtQuick.Controls.Material 2.12

Flickable {
    id: menu
    //Layout.fillWidth: true
    //Layout.fillHeight: true
    
    boundsBehavior: Flickable.StopAtBounds
    contentHeight: columnLayout.height
    
    required property string hl
    
    property QtObject hl_model: root.backend ? root.backend.article(hl) : null
    
    property int contentMargin: 9
    property string outputName: "richTextArea_" + menu.hl
    property int outputId: 0
    
    property bool centeredName: false//vertically
    property bool nameAtTop: false
    
    function grabCallback(result) {
        outputId += 1
        console.log(outputId.toString())
        result.saveToFile(outputName+outputId.toString()+".png") 
        if( !contentFlickable.atYEnd )
        {
            contentFlickable.contentY += ( contentFlickable.height - 1.8*contentMargin - outputLabel.anchors.bottomMargin - outputLabel.anchors.topMargin  )//3.8?
            
            contentBg.anchors.bottomMargin = contentFlickable.atYEnd ? contentMargin : -3
            contentBg.anchors.topMargin = contentFlickable.atYBeginning ? contentMargin : -3
            richTextArea.grabToImage( grabCallback )
        }
        else
        {            
            contentBg.anchors.bottomMargin = contentMargin
            contentBg.anchors.topMargin = contentMargin
            outputId = 0
        }
    }
    // where -- string
    function render() {
        //var i = 0
        //var found = false
        //for (i = 0; i < columnLayout.children.length; i++) {
        //    if (columnLayout.children[i].objectName === what) {
        //        // We found respective item
        //        found = true
        //        break
        //    }
        //}
       // if (found) {
            //console.log("We found item " + richTextArea + ". Grabbing it to " + where)
            // Grab image and save it (via callback f-ion)
            
            //contentFlickable.forceActiveFocus()
            contentFlickable.contentY = 0
            
            if( !contentFlickable.atYEnd )
            {
                contentBg.anchors.bottomMargin = -3
            }
            
            console.log(outputId.toString())
            richTextArea.grabToImage( grabCallback )
        //} else {
        //    console.warn("No item called " + what)
        //}
    }
    function adjust() {
        
        contentFlickable.contentY = 0
        while( contentFlickable.atYEnd && sbHeight.value > sbHeight.from )
        {
            sbHeight.value -= sbHeight.stepSize
        }
        while( !contentFlickable.atYEnd && sbHeight.value < sbHeight.to )
        {
            sbHeight.value += sbHeight.stepSize
        }
        sbHeight.value += sbHeight.stepSize
    }
    
    Column
    {
        id: columnLayout
        //anchors.fill: parent
        anchors.margins: 0
        width: menu.width
            
        RowLayout {
            anchors.left: parent.left
            anchors.right: parent.right
            Label {
                text: hl_model ? hl_model.p_mini ? "Mini" : hl_model.p_medium ? "Medium" : "Short" : "..."
            }
            Label {
                text: menu.hl + " Article"
                width: parent.width
                horizontalAlignment: Text.AlignHCenter
                font.pointSize: 15
                padding: 5
            }
            Label {
                text: contentEdit.text.length + " characters, " + contentEdit.text.trim().split(/\s+/).length + " words"
            }
        
                TextField {
                    id: postsPathEdit
                    Layout.fillWidth: true
                    text: hl_model ? hl_model.p_posts_folder : "..."
                           
                    onEditingFinished: {
                        hl_model.set_posts_folder(text)
                    }
                }
                TextField {
                    Layout.fillWidth: true
                    text: hl_model ? hl_model.p_website_url : "..."                           
                    onEditingFinished: {
                        hl_model.set_website_url(text)
                    }
                }
            //}
            
        }
        Setting { 
            //name: "Title"
            desc: hl_model ? hl_model.p_slug : "..."
            //enabled: !cbTitle.checked
            
            ColumnLayout {
                TextField {
                    id: titleEdit
                    Layout.fillWidth: true
                    text: hl_model ? hl_model.p_title : "..."
                                        
                    onEditingFinished: {
                        hl_model.set_title(text)
                    }
                }
                RowLayout {
                    CheckBox {   
                        id: cbDate
                        checked: false
                        text: "Date override"
                    }
                    TextField {
                        Layout.fillWidth: true
                        enabled: cbDate.checked//TODO: visible instead of enabled
                        text: hl_model ? hl_model.p_date : "..."
                        onEditingFinished: {
                            hl_model.set_date(text)
                        }
                    }
                }
            }
        }

        Rectangle {
            width: menu.width
            height: 320
            color: "white"//cbContent.checked ? "#aaa" : "white"
            Flickable {
              id: flickable
              flickableDirection: Flickable.VerticalFlick
              anchors.fill: parent

              TextArea.flickable: TextArea {
                  id: contentEdit
                  //textFormat: Qt.RichText
                  wrapMode: TextArea.Wrap
                  //focus: true
                  selectByMouse: true
                  persistentSelection: true
                  leftPadding: 6
                  rightPadding: 6
                  topPadding: 6
                  bottomPadding: 6
                  //background: null
                  
                  text: hl_model ? hl_model.p_content : "..."
            
                  onEditingFinished: {
                      hl_model.set_content(text)
                  }
                  //MouseArea {
                  //    acceptedButtons: Qt.RightButton
                  //    anchors.fill: parent
                  //    onClicked: contextMenu.open()
                  //}
              }

              ScrollBar.vertical: ScrollBar {}
            }
        }        
        
        RowLayout {
            //ColumnLayout {
                RowLayout {
                    Label {
                        text: "Font:"
                    }
                    SpinBox {
                        id: sbFontSize
                        value: 14
                        from: 8
                        to: 48
                        stepSize: 2
                        editable: true
                    }
                }
                RowLayout {
                    CheckBox {
                        id: cbGreen
                        text: "G"
                        checked: hl_model ? hl_model.p_green : true
                        onToggled: { 
                            hl_model.set_green(checked)
                        }
                    }
                    CheckBox {
                        id: cbBlack
                        text: "B"
                        checked: hl_model ? hl_model.p_black : true
                        onToggled: { 
                            hl_model.set_black(checked)
                        }
                    }
                }
            //}
            Label {
                text: "W/H:"
            }
            ColumnLayout {
                SpinBox {
                    id: sbWidth
                    visible: false
                    value: 640
                    from: 320
                    to: 1280
                    stepSize: 32
                    editable: true
                }
                SpinBox {
                    id: sbHeight
                    value: 906
                    from: 32
                    to: 12800
                    stepSize: 32
                    editable: true
                }
            }
            CheckBox {
                id: cbCentered
                checked: false
                text: "Center"
            }
            // TODO: Add "add image"
            Button {
                text: "Grab"
                onClicked: { 
                    render()
                }
            }
            Button {
                text: "Adjust"
                onClicked: { 
                    adjust()
                }
            }
        }
        Rectangle {
            width: sbWidth.visible ? sbWidth.value : menu.width
            height: sbHeight.value
            color: "white"//"#333"
            visible: false
            Flickable {
              flickableDirection: Flickable.VerticalFlick
              anchors.fill: parent

              TextArea.flickable: TextArea {
                  color: "#000033"//"#aaa"
                  font.pointSize: sbFontSize.value
                  wrapMode: TextArea.Wrap
                  readOnly: true
                  selectByMouse: true
                  persistentSelection: true
                  textFormat: TextEdit.RichText
                  
                  verticalAlignment: TextEdit.AlignVCenter
                  horizontalAlignment: cbCentered.checked ? TextEdit.AlignHCenter : TextEdit.AlignLeft
                  
                  text: hl_model ? hl_model.p_content_md_rich : "..."
              }
              ScrollBar.vertical: ScrollBar {}
            }
        }
        Rectangle {
            id: richTextArea
            width: sbWidth.visible ? sbWidth.value : menu.width
            height: sbHeight.value
            color: cbGreen.checked ? "#24475b" : (cbBlack.checked ? "black":"white")//"#7a9295"//"#455b55"//"#767679"
                
            Rectangle {
                id: contentBg
                anchors.fill: parent
                anchors.margins: contentMargin
                //radius: 5
                
                color: cbGreen.checked ? "#24475b" : (cbBlack.checked ? "black":"white")//"#003d2b"//"#182c25"//"#262626"
                Flickable {
                  id: contentFlickable
                  flickableDirection: Flickable.VerticalFlick
                  anchors.fill: parent
                  anchors.margins: 0

                  TextArea.flickable: TextArea {
                      color: cbGreen.checked ? "white" : (cbBlack.checked ? "white":"#000033")//"#ade6b9"//"#306844"//"#ffffff"//"#003939"
                      background: null
                      font.pointSize: sbFontSize.value
                      wrapMode: TextArea.Wrap
                      readOnly: true
                      selectByMouse: true
                      persistentSelection: true
                      textFormat: TextEdit.RichText
                       
                      //bottomInset: 0
                      anchors.rightMargin: 18//9
                      
                      verticalAlignment: TextEdit.AlignVCenter
                      horizontalAlignment: cbCentered.checked ? TextEdit.AlignHCenter : TextEdit.AlignLeft
                      
                      text: hl_model ? hl_model.p_content_md_separators : "..."
                  }
                  ScrollBar.vertical: ScrollBar {}
                }
                Rectangle {
                    //visible: false // TODO
                    color: centeredName ? "#24475b" : "transparent"
                    anchors.right: parent.right; 
                    anchors.top: nameAtTop ? parent.top : undefined
                    anchors.bottom: nameAtTop ? undefined : parent.bottom
                                        
                    anchors.topMargin: 0
                    anchors.bottomMargin: 0
                    anchors.rightMargin: centeredName ? 21 : 0
                    
                    width: myName.implicitWidth + 12 // rightMargin*2
                    height: 10
                    Text {
                        id: myName
                        color: centeredName ? "silver" : (cbGreen.checked ? "#7a9295" : "silver")//"#1d3853"
                        anchors.right: parent.right; 
                        anchors.top: nameAtTop ? parent.top : undefined
                        anchors.bottom: nameAtTop ? undefined : parent.bottom
                        
                        anchors.topMargin: centeredName ? -9 : 0
                        anchors.bottomMargin: centeredName ? -9 : 0
                        anchors.rightMargin: 6
                        text: menu.hl == "en" ? "linktr.ee/Gamsby" : "linktr.ee/MGamsby"
                        font.pointSize: sbFontSize.value - 1
                    }
                }
                Text {
                    id: outputLabel
                    color: cbGreen.checked ? "#ade6b9" : (cbBlack.checked ? "#000033":"white")
                    anchors.right: parent.right; anchors.bottom: parent.bottom
                    anchors.topMargin: 3 -contentBg.anchors.topMargin + contentMargin
                    anchors.rightMargin: 4
                    anchors.bottomMargin: -contentBg.anchors.bottomMargin + contentMargin
                    visible: !(contentFlickable.atYEnd && contentFlickable.atYBeginning)
                    text: outputId+1
                }
            }
        }
        
        Rectangle {
            width: parent.width
            height: 200//sbHeight.value
            color: "white"//"#333"
            Flickable {
              flickableDirection: Flickable.VerticalFlick
              anchors.fill: parent

              TextArea.flickable: TextArea {
                  color: "#000033"//"#aaa"
                  font.pointSize: sbFontSize.value
                  wrapMode: TextArea.Wrap
                  readOnly: true
                  selectByMouse: true
                  persistentSelection: true
                  textFormat: TextEdit.RichText
                  
                  verticalAlignment: TextEdit.AlignVCenter
                  horizontalAlignment: cbCentered.checked ? TextEdit.AlignHCenter : TextEdit.AlignLeft
                  
                  text: hl_model ? hl_model.p_content_md_separators_br : "..."
              }
              ScrollBar.vertical: ScrollBar {}
            }
        }

        Flickable {
          width: parent.width
          height: 120
          flickableDirection: Flickable.VerticalFlick

          TextArea.flickable: TextArea {
              wrapMode: TextArea.Wrap
              readOnly: true
              
              text: hl_model ? hl_model.p_content_md : "..."
          }
          ScrollBar.vertical: ScrollBar {}
        }
        Label {
                Layout.fillHeight: true            
        }
        Timer {
            id: timer
            interval: 2000 // 3000
            running: true
            repeat: true
            onTriggered: {
                if( titleEdit.activeFocus )
                    hl_model.set_title(titleEdit.text)
                
                if( contentEdit.activeFocus )
                    hl_model.set_content(contentEdit.text)
            }
        }
    }
}