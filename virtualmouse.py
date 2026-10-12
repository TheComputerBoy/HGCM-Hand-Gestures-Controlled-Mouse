import HandTrackingModule as htm
import cv2 as cv
import numpy as np
import autopy
import time
import ctypes
###########################
wCam , hCam = 640,480
wScr , hScr =autopy.screen.size()
frameR = 100
smootheing = 5
plocX , plocY = 0, 0
clocX , clocY = 0,0
# 12. cooldowns + prev positions for new gestures
lastLeft, lastRight = 0, 0
lastScroll, lastVol, lastMin, lastMedia, lastDesk = 0, 0, 0, 0, 0
prevScrollY, prevVolY, prevNineX = 0, 0, 0
openHoldT, openHoldX, openHoldY = 0, 0, 0
openArmed = False
pinchPrev, lastTapT, dblT, leftDown = False, 0, 0, False
##########################

def _wheel(amount):
    try:
        ctypes.windll.user32.mouse_event(0x0800, 0, 0, amount, 0)
    except:
        pass

def _volkey(vk):
    try:
        u = ctypes.windll.user32
        u.keybd_event(vk, 0, 0, 0)
        u.keybd_event(vk, 0, 2, 0)
    except:
        pass

def _left(down):
    try:
        ctypes.windll.user32.mouse_event(0x0002 if down else 0x0004, 0, 0, 0, 0)
    except:
        pass

def _minimize():
    try:
        u = ctypes.windll.user32
        u.keybd_event(0x5B, 0, 0, 0)  # win down
        u.keybd_event(0x4D, 0, 0, 0)  # m
        u.keybd_event(0x4D, 0, 2, 0)
        u.keybd_event(0x5B, 0, 2, 0)
    except:
        pass
    time.sleep(0.3)
    _restoreSelf()  # pop our preview back; everything else stays minimized

def _pinTop(stick=False):
    try:
        cv.setWindowProperty("result", cv.WND_PROP_TOPMOST, 1)
    except:
        pass
    try:  # TOPMOST + TOOLWINDOW + NOACTIVATE: visible, no taskbar/Alt-Tab, never steals focus
        u = ctypes.windll.user32
        h = u.FindWindowA(None, b"result")
        if h:
            ex = u.GetWindowLongA(h, -20)
            u.SetWindowLongA(h, -20, ex | 0x00000080 | 0x08000000)
            u.SetWindowPos(h, -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010)
            if stick:  # snap small preview to top-right, out of the way
                try:
                    cv.resizeWindow("result", 320, 240)
                    cv.moveWindow("result", max(0, wScr - 360), 30)
                except:
                    pass
    except:
        pass

def _restoreSelf():
    try:
        h = ctypes.windll.user32.FindWindowA(None, b"result")
        if h and ctypes.windll.user32.IsIconic(h):
            ctypes.windll.user32.ShowWindow(h, 9)  # SW_RESTORE
    except:
        pass
    _pinTop()

def _mediatoggle():
    _volkey(0xB3)  # VK_MEDIA_PLAY_PAUSE

def _desktop(right):
    try:
        u = ctypes.windll.user32
        vk = 0x27 if right else 0x25
        u.keybd_event(0x5B, 0, 0, 0)  # win down
        time.sleep(0.03)
        u.keybd_event(0x11, 0, 0, 0)  # ctrl down
        time.sleep(0.03)
        u.keybd_event(vk, 0, 0, 0)
        time.sleep(0.05)
        u.keybd_event(vk, 0, 2, 0)
        u.keybd_event(0x11, 0, 2, 0)
        u.keybd_event(0x5B, 0, 2, 0)
    except:
        pass
cap = cv.VideoCapture(0)
cap.set(3,wCam)
cap.set(4,hCam)
detector = htm.HandDetector()

def Mouse(img):
    global frameR
    global smootheing
    global plocX
    global plocY
    global clocX
    global clocY
    global wScr
    global wCam
    global hScr
    global hCam
    global lastLeft, lastRight
    global lastScroll, lastVol, lastMin, lastMedia, lastDesk
    global prevScrollY, prevVolY, prevNineX
    global openHoldT, openHoldX, openHoldY
    global openArmed
    global pinchPrev, lastTapT, dblT, leftDown
    # finding hands
    detector.findhands(img)
    lmlist, bbox = detector.findPosition(img)

    cv.rectangle(img, (frameR, frameR), (wCam - frameR, hCam - frameR), (255, 0, 255), 2)

    # 2. get the tip of index and midel finger
    if len(lmlist) != 0:
        Xindex, Yindex = lmlist[8][1], lmlist[8][2]
        Xmidel, Ymidel = lmlist[12][1], lmlist[12][2]
        # 3. check which one is up?
        fingers = detector.fingersUp()
        # 4. index only: moving mode
        if fingers[1] == 1 and fingers[2] == 0 and fingers[3] == 0 and fingers[4] == 0:
            # 5. cordinates the position (cam :640*480) to (screen :2560 × 1600)
            xMOUSE = np.interp(Xindex, (frameR, wCam - frameR), (0, wScr))
            yMOUSE = np.interp(Yindex, (frameR, hCam - frameR), (0, hScr))
            # 6. smoothen value
            clocX = plocX + (xMOUSE - plocX) / smootheing
            clocY = plocY + (yMOUSE - plocY) / smootheing
            # 7. move mouse
            autopy.mouse.move(clocX, clocY)
            cv.circle(img, (Xindex, Yindex), 15, (20, 180, 90), cv.FILLED)
            plocY, plocX = clocY, clocX
            # 8. thumb-index pinch in move mode: right click
            rlen, _ = detector.findDistance(4, 8, img, draw=False)
            if rlen < 35 and time.time() - lastRight > 1:
                autopy.mouse.click(autopy.mouse.Button.RIGHT)
                lastRight = time.time()

        # 9. index + middle up: tap=click, double-tap=double-click (drag moved to index+ring)
        if fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0 and fingers[4] == 0:
            # 10. finding distance
            length, _ = detector.findDistance(8, 12, img)
            now = time.time()
            pinched = length < 40
            if pinched and not pinchPrev:  # rising edge: new tap
                if dblT == 0 and lastTapT != 0 and now - lastTapT < 0.28:
                    dblT, lastTapT = now, 0  # 2nd tap
                elif dblT == 0 and lastTapT == 0:
                    lastTapT = now  # 1st tap
            if not pinched and pinchPrev and dblT != 0 and now - dblT < 0.25:
                autopy.mouse.click()
                autopy.mouse.click()  # 2nd tap quick release: double-click
                dblT = 0
                prevScrollY = Ymidel
            elif not pinched and lastTapT != 0 and now - lastTapT > 0.3:
                autopy.mouse.click()  # single tap, no 2nd tap came
                lastTapT = 0
                prevScrollY = Ymidel
            # 12. open fingers + vertical move: scroll
            elif length > 70 and dblT == 0:
                if prevScrollY == 0:
                    prevScrollY = Ymidel
                dy = Ymidel - prevScrollY
                if abs(dy) > 8 and time.time() - lastScroll > 0.08:
                    _wheel(-120 if dy > 0 else 120)
                    lastScroll = time.time()
                    prevScrollY = Ymidel
            elif not pinched:
                prevScrollY = Ymidel
            pinchPrev = pinched
        else:
            if dblT != 0:  # 2nd tap cut off = treat as release
                autopy.mouse.click()
                autopy.mouse.click()
            elif lastTapT != 0:  # single tap cut off = still count it
                autopy.mouse.click()
            pinchPrev, lastTapT, dblT = False, 0, 0

        # 12b. index + middle + pinky up, thumb-ring bent pinched: grab to drag & drop
        if fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0 and fingers[4] == 1:
            rlen, _ = detector.findDistance(4, 16, img, draw=False)
            if not leftDown and not openArmed and rlen < 60:
                _left(True)
                leftDown = True
            if leftDown:  # move with index while grabbed
                xMOUSE = np.interp(Xindex, (frameR, wCam - frameR), (0, wScr))
                yMOUSE = np.interp(Yindex, (frameR, hCam - frameR), (0, hScr))
                clocX = plocX + (xMOUSE - plocX) / smootheing
                clocY = plocY + (yMOUSE - plocY) / smootheing
                autopy.mouse.move(clocX, clocY)
                plocY, plocX = clocY, clocX
                cv.circle(img, (Xindex, Yindex), 15, (20, 180, 90), cv.FILLED)
                if rlen > 70:
                    _left(False)
                    leftDown = False
        else:
            if leftDown:
                _left(False)
                leftDown = False

        # 13. index + middle + ring up, pinky down: volume by vertical move
        if fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1 and fingers[4] == 0:
            if prevVolY == 0:
                prevVolY = Yindex
            dy = Yindex - prevVolY
            if abs(dy) > 12 and time.time() - lastVol > 0.25:
                _volkey(0xAF if dy < 0 else 0xAE)  # up : down
                lastVol = time.time()
                prevVolY = Yindex
            cv.circle(img, (Xindex, Yindex), 15, (255, 0, 0), cv.FILLED)

        # 14. open palm hold ~0.5s then fist: minimize (win+m)
        if fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1 and fingers[4] == 1:
            palmX = sum([p[1] for p in lmlist]) // len(lmlist)
            palmY = sum([p[2] for p in lmlist]) // len(lmlist)
            now = time.time()
            if openHoldT == 0:
                openHoldT, openHoldX, openHoldY = now, palmX, palmY
                openArmed = False
            elif abs(palmX - openHoldX) > 40 or abs(palmY - openHoldY) > 40:
                openHoldT, openHoldX, openHoldY = now, palmX, palmY  # moved, restart hold
                openArmed = False
            elif now - openHoldT >= 0.5:
                openArmed = True  # steady hold complete; fist now minimizes
        elif sum(fingers[1:]) == 0 and openArmed and time.time() - lastMin > 1.5:
            _minimize()
            lastMin = time.time()
            openHoldT = 0
            openArmed = False
            prevNineX = 0  # don't carry fist position into desktop-swipe
        elif openHoldT != 0 and time.time() - openHoldT > 2.0:
            openHoldT = 0  # stale arm expired; flicker/intermediate frames no longer reset it
            openArmed = False

        # 15. both hands, all 10 up: media play/pause toggle
        c0 = sum(fingers)
        f0 = sum(fingers[1:])  # fist = 4 fingers down, thumb ignored (folds unpredictably)
        c1 = -1
        f1 = -1
        total = c0
        xs = [p[1] for p in lmlist]
        for h in (1,):
            lm, _ = detector.findPosition(img, handsNo=h)
            if len(lm) != 0:
                f = detector.fingersUp()
                c1 = sum(f)
                f1 = sum(f[1:])
                total += c1
                xs += [p[1] for p in lm]
        if total == 10 and time.time() - lastMedia > 1:
            _mediatoggle()
            lastMedia = time.time()
            prevNineX = 0
        # 16. single fist (4 fingers down, 2nd hand absent/closed) + swipe: switch desktop
        elif f0 == 0 and f1 <= 0:
            palmX = sum(xs) // len(xs)
            if prevNineX == 0:
                prevNineX = palmX
            dx = palmX - prevNineX
            if abs(dx) > 40 and time.time() - lastDesk > 1.0:
                _desktop(right=True if dx > 0 else False)  # move right -> right desk
                lastDesk = time.time()
                prevNineX = palmX
        else:
            prevNineX = 0
    else:
        if openHoldT != 0 and time.time() - openHoldT > 2.0:
            openHoldT = 0  # expire stale arm; brief tracking loss keeps it
            openArmed = False
        if leftDown:
            _left(False)
        elif dblT != 0:
            autopy.mouse.click()
            autopy.mouse.click()
        elif lastTapT != 0:
            autopy.mouse.click()
        leftDown = False
        pinchPrev, lastTapT, dblT = False, 0, 0
    return img


def main():
    cv.namedWindow("result", cv.WINDOW_NORMAL)
    _pinTop(stick=True)
    while True:
        sucess, img = cap.read()
        img = cv.flip(img, 1)

        img = Mouse(img)

        # 11. display

        cv.imshow("result", img)
        _restoreSelf()  # re-assert TOPMOST + un-minimize self only; never steals focus
        if cv.waitKey(1) & 0xFF == ord('q'):
            break

if __name__=='__main__':
    main()
