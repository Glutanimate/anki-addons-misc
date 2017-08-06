# -*- coding: utf-8 -*-
"""
Anki Add-on: Progress Bar

Shows progress in the Reviewer in terms of passed cards per session.

Copyright:  (c) Unknown author (nest0r/Ja-Dark?) 2017
            (c) Glutanimate 2017 <https://glutanimate.com/>
License: GNU AGPLv3 or later <https://www.gnu.org/licenses/agpl.html>
"""

# Do not modify the following lines
from __future__ import unicode_literals
from anki.hooks import addHook
from aqt import mw
from aqt.qt import *

__version__ = '1.2.0'

############## USER CONFIGURATION START ##############

# CARD TALLY CALCULATION

# Which queues to include in the progress calculation (all True by default)
includeNew = True
includeRev = True
includeLrn = True

# Only include new cards once reviews are exhausted.
includeNewAfterRevs = True

# PROGRESS BAR APPEARANCE

showPercent = False # Show the progress text percentage or not.s

qtxt = "aliceblue" # Percentage color, if text visible.
qbg = "#18adab" # Background color of progress bar.
qfg = "#38e3b2" # Foreground color of progress bar.
qbr = 0 # Border radius (> 0 for rounded corners).

# optionally restricts progress bar width
maxWidth = ""  # (e.g. "5px". default: "")

orientationHV = Qt.Horizontal # Show bar horizontally (side to side). Use with top/bottom dockArea.
# orientationHV = Qt.Vertical # Show bar vertically (up and down). Use with right/left dockArea.

invertTF = False # If set to True, inverts and goes from right to left or top to bottom.

dockArea = Qt.TopDockWidgetArea # Shows bar at the top. Use with horizontal orientation.
#dockArea = Qt.BottomDockWidgetArea # Shows bar at the bottom. Use with horizontal orientation.
#dockArea = Qt.RightDockWidgetArea # Shows bar at right. Use with vertical orientation.
#dockArea = Qt.LeftDockWidgetArea # Shows bar at left. Use with vertical orientation.

pbStyle = "" # Stylesheet used only if blank. Else uses QPalette + theme style.
'''pbStyle options (insert a quoted word above):
    -- "plastique", "windowsxp", "windows", "windowsvista", "motif", "cde", "cleanlooks"
    -- "macintosh", "gtk", or "fusion" might also work
    -- "windowsvista" unfortunately ignores custom colors, due to animation?
    -- Some styles don't reset bar appearance fully on undo. An annoyance.
    -- Themes gallery: http://doc.qt.io/qt-4.8/gallery.html'''

##############  USER CONFIGURATION END  ##############

## Set up variables

nm = 0
failed = 0
progressBar = None
mx = 0

pbdStyle = QStyleFactory.create("%s" % (pbStyle)) # Don't touch.

#Defining palette in case needed for custom colors with themes.
palette = QPalette()
palette.setColor(QPalette.Base, QColor(qbg))
palette.setColor(QPalette.Highlight, QColor(qfg))
palette.setColor(QPalette.Button, QColor(qbg))
palette.setColor(QPalette.WindowText, QColor(qtxt))
palette.setColor(QPalette.Window, QColor(qbg))

if maxWidth:
    if orientationHV == Qt.Horizontal:
        restrictSize = "max-height: %s;" % maxWidth
    else:
        restrictSize = "max-width: %s;" % maxWidth
else:
    restrictSize = ""

try:
    # Remove that annoying separator strip if we have Night Mode, avoiding conflicts with this add-on.
    import Night_Mode
    Night_Mode.nm_css_menu \
    += Night_Mode.nm_css_menu \
    + '''
        QMainWindow::separator
    {
        width: 0px;
        height: 0px;
    }
    '''
except ImportError:
    failed = 1


def nmc():
    """Checks whether Night_Mode is disabled:
        if so, we remove the separator here."""
    global nm
    if not failed:
        nm = Night_Mode.nm_state_on
    if not nm:
        mw.setStyleSheet(
    '''
        QMainWindow::separator
    {
        width: 0px;
        height: 0px;
    }
    ''')


def _dock(pb):
    """Dock for the progress bar. Giving it a blank title bar,
        making sure to set focus back to the reviewer."""
    dock = QDockWidget()
    tWidget = QWidget()
    dock.setObjectName("pbDock")
    dock.setWidget(pb)
    dock.setTitleBarWidget( tWidget )
    mw.addDockWidget(dockArea, dock)
    if qbr > 0 or pbdStyle != None:
        # Matches background for round corners.
        # Also handles background for themes' percentage text.
        mw.setPalette(palette)
    mw.web.setFocus()
    return dock


def pb():
    """Initialize and set parameters for progress bar, adding it to the dock."""
    mx = max(1, getMX())
    progressBar = QProgressBar()
    progressBar.setRange(0, mx)
    progressBar.setTextVisible(showPercent)
    progressBar.setInvertedAppearance(invertTF)
    progressBar.setOrientation(orientationHV)
    if pbdStyle == None:
        progressBar.setStyleSheet(
        '''
                    QProgressBar
                {
                    text-align:center;
                    color:%s;
                    background-color: %s;
                    border-radius: %dpx;
                    %s
                }
                    QProgressBar::chunk
                {
                    background-color: %s;
                    margin: 0px;
                    border-radius: %dpx;
                }
                ''' % (qtxt, qbg, qbr, restrictSize, qfg, qbr))
    else:
        progressBar.setStyle(pbdStyle)
        progressBar.setPalette(palette)
    _dock(progressBar)
    return progressBar, mx


def getMX():
    """Get deck's card counts for progress bar updates."""
    rev = nu = lrn = 0
    if includeRev:
        rev = mw.col.sched.totalRevForCurrentDeck()
    if includeLrn:
        try:
            lrn = mw.col.sched.lrnCount
        except AttributeError:
            pass
    if includeNew or (includeNewAfterRevs and rev == 0):
        nu = mw.col.sched.totalNewForCurrentDeck()
    total = rev + nu + lrn
    return total


def _updatePB():
    """Update progress bar; hiding/showing prevents flashing bug."""
    global mx
    if progressBar:
        nmc()
        total = getMX()
        if total > mx:
            mx = total
            progressBar.setRange(0, mx)
        curr = (mx - total)
        progressBar.hide()
        progressBar.setValue(curr)
        progressBar.show()



def _renderBar(state, oldState):
    global mx, progressBar
    if state == "overview":
        # Set up progress bar at deck's overview page: initialize or modify.
        if not progressBar: progressBar, mx = pb()
        else: rrenderPB()
        progressBar.show()
        nmc()
    elif state == "deckBrowser":
        # Hide the progress bar at deck list. Not deleted, so we just modify later.
        if progressBar:
            mx = 0
            progressBar.hide()


def rrenderPB():
    """Modify progress bar if it was already initialized."""
    global mx
    if getMX() >= 1:
        if mx > getMX(): _updatePB()
        else:
            mx = getMX()
            progressBar.setRange(0, mx)
            progressBar.reset()
    else: progressBar.setValue(mx)


addHook("afterStateChange", _renderBar)
addHook("showQuestion", _updatePB)