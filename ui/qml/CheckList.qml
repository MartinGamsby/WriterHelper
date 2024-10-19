import QtQuick 2.15
import QtQuick.Layouts
import QtQuick.Controls
import "."

import QtQuick.Controls.Material 2.12

Rectangle {
    clip: true
    ColumnLayout {
        WordWrapCheckBox { text: "Write the content"; id: cbContent  }
        WordWrapCheckBox { text: "Start an image generation (or find it)" }
        WordWrapCheckBox { text: "Proofread" }
        WordWrapCheckBox { text: "Translate (And proofread\nin french if the translation is bad)"; id: cbTranslate }
        WordWrapCheckBox { text: "Find/write tags" }
        
        Label { text: "Share to <a href='https://typeshare.co/martingamsby'>Typeshare</a>"; onLinkActivated: function(link) { Qt.openUrlExternally(link) } }
        WordWrapCheckBox { text: "- COPY LINK of Typeshare here" }
        WordWrapCheckBox { text: "- COPY IMAGE URL of Typeshare here" }
        
        Label { text: "Share to <a href='https://x.com/'>X/Twitter</a> (EVENTUALLY/IF APPLICABLE: Adapt it for X)"; onLinkActivated: function(link) { Qt.openUrlExternally(link) } }
        WordWrapCheckBox { text: "-> COPY LINK of X here" }
        Label { text: "Share to <a href='https://bsky.app/profile/martin-gamsby.bsky.social'>Bluesky</a>"; onLinkActivated: function(link) { Qt.openUrlExternally(link) } }
        WordWrapCheckBox { text: "-> COPY LINK of Bluesky here" }
        Label { text: "Share to <a href='https://facebook.com/'>Facebook</a>"; onLinkActivated: function(link) { Qt.openUrlExternally(link) } }
        WordWrapCheckBox { text: "- Share in facebook if relevant?" }
        WordWrapCheckBox { text: "-> COPY LINK of Facebook here" }
        
        //Label { text: "Share to <a href='https://medium.com/new-story'>Medium</a>"; onLinkActivated: function(link) { Qt.openUrlExternally(link) } }
        //WordWrapCheckBox { text: "Paste the link MEDIUM here" }
        
        
        WordWrapCheckBox { text: "GITHUB: Upload the article!" }
    }
}