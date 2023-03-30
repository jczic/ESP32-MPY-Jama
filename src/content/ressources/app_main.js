
/*============================================= #
#                                               #
# Copyright © 2023 JC`zic (Jean-Christophe Bos) #
#             jczic.bos@gmail.com               #
#                                               #
# =============================================*/

const GITHUB_REPOSITORY_URL   = "https://github.com/jczic/ESP32-MPY-Jama";
const GITHUB_LAST_RELEASE_URL = "https://api.github.com/repos/jczic/ESP32-MPY-Jama/releases/latest";

const PRC_NONE                = 0;
const PRC_TRANSFER            = 1;
const PRC_EXEC_CODE           = 2;
const PRC_EXEC_JAMA           = 3;

var websocket                 = null;
var wsConnected               = false;
var toastTimeout              = null;
var boxDialogFunc             = null;
var boxDialogGenericParentElm = null;
var canCloseWindow            = true;

var appTitle                  = "";
var appVer                    = "";
var osName                    = "";

var currentPort               = null;
var connectionState           = false;
var processing                = PRC_NONE;

var showConnPortsDialog       = false;
var showNetworksInfoPage      = false;

var pinsList                  = { }
var networkMiniInfos          = null

var keepConfig                = { };

var flashRootPath             = "";
var browsePath                = "";
var sdcardMountPoint          = null;

var codeMirrorTerm            = null;
var codeMirrorJamaTerm        = null;
var termTextBuffer            = '';
var termLastWriteMS           = 0;

var cmdHistory                = [ ];
var cmdHistoryNav             = [""];
var cmdHistoryIdx             = 0;

var counterNewFile            = 1;

var contentBytesArr           = [ ];
var contentRemotePath         = "";

var keepTabCodeElm            = null;
var keepCloseTabCodeElm       = false;

var execAnimShowTime          = null;

var execJamaFuncConfig        = null;
var execJamaStopTimeout       = null;

var pinoutModels              = [ "ESP32-C6-DevKitC-1 (C6-WROOM-1)",
                                  "ESP32-C3-DevKitM-1 (C3-MINI-1)",
                                  "ESP32-C3-DevKitC-02 (C3-WROOM-02)",
                                  "ESP32-S3-DevKitM-1 (S3-MINI-1)",
                                  "ESP32-S3-DevKitC-1 (S3-WROOM-1)",
                                  "ESP32-S2-DevKitM-1 (S2-MINI-1)",
                                  "ESP32-S2-Saola-1 (S2-WROVER)",,
                                  "ESP32-S2-DevKitC-1 (S2-SOLO)",
                                  "ESP32-PICO-KIT (PICO-D4)",
                                  "ESP32-DevKitM-1 (MINI-1)",
                                  "ESP32-DevKitC (WROOM)" ];

function getElmById(id)
{ return document.getElementById(id); }

function getElmsByClass(className)
{return document.getElementsByClassName(className); }

function newElm(tagName, id, classArray) {
    var elm = document.createElement(tagName);
    if (elm) {
        if (id)
            elm.id = id;
        if (classArray)
            for (var className of classArray)
                elm.classList.add(className);
    }
    return elm;
}

function delElm(elm) {
    if (elm.parentElement)
        return (elm.parentElement.removeChild(elm) != null);
    return false;
}

function classToggle(elm, classA, classB) {
    var x = elm.classList.contains(classA);
    elm.classList.remove(x ? classA : classB);
    elm.classList.add(x ? classB : classA);
    return x;
}

function setMultiClass(elm, classArray) {
    while (elm.classList.length > 0)
        elm.classList.remove(elm.classList[0]);
    for (var className of classArray)
        elm.classList.add(className);
}

function getEventTarget(e) {
    e = e || window.event;
    var targ = e.target || e.srcElement || e;
    if (targ.nodeType == 3) targ = targ.parentNode;
    return targ;
}

function getSubElm(rootElm, classNameToFind) {
    try        { return rootElm.getElementsByClassName(classNameToFind)[0]; }
    catch (ex) { return null; }
}

function showElm(elm)
{ elm.style.display = 'block'; }

function showElmInline(elm)
{ elm.style.display = 'inline'; }

function hideElm(elm)
{ elm.style.display = 'none'; }

function show(id)
{ showElm(getElmById(id)); }

function showInline(id)
{ showElmInline(getElmById(id)); }

function hide(id)
{ hideElm(getElmById(id)); }

function rmElmChildren(id) {
    var elm = getElmById(id)
    while (elm.firstChild)
        elm.removeChild(elm.firstChild);
}

function textToHTML(text) {
    return text.replaceAll("\n", "<br />").replaceAll('  ', ' &nbsp;');
}

function toastInfo(text) {
    var toastElm = getElmById("toast-elm-id");
    if (toastElm)
        delElm(toastElm);
    if (toastTimeout)
        clearTimeout(toastTimeout);
    toastElm = newElm("div", "toast-elm-id", ["toast-info"]);
    toastElm.innerText = text;
    document.body.appendChild(toastElm);
    toastTimeout = setTimeout(
        function() {
            delElm(toastElm);
            toastTimeout = null;
        },
        5000 );
}

function getUptimeStr(uptimeMin) {
    var d = Math.floor(uptimeMin/60/24);
    var h = Math.floor(uptimeMin/60 - d*24);
    var m = uptimeMin % 60;
    return d + "j, " + h + "h, " + m + "m";
}

function setTextTag(id, text, success) {
    var elm = getElmById(id);
    elm.innerText = text;
    elm.className = (success ? "info-tag-success" : success == false ? "info-tag-error" : "");
}

function showInfo(text) {
    boxDialogAlert("😉 Information", text);
}

function showError(text) {
    boxDialogAlert("😭 Error", text);
}

function showPage(id) {
    var actPage = getActivePage();
    if (!actPage || actPage.id != id) {
        var pages = getElmsByClass("page-container");
        for (var i = 0; i < pages.length; i++) {
            var page = pages[i];
            if (page.id == id) {
                show(page.id);
                page.scrollTop = 0;
            }
            else
                hide(page.id);
        }
    }
}

function getActivePage() {
    var pages = getElmsByClass("page-container");
    for (var i = 0; i < pages.length; i++)
        if (pages[i].style.display == "block")
            return pages[i];
    return null;
}

function onWSOpen(evt)
{
    refreshJamaFuncs();
}

function onWSClose(evt)
{
    if (!connectWS())
        setConnectionState(false);
}

function onWSMessage(evt)
{
    var o = JSON.parse(evt.data);
    switch (o.CMD)
    {
        case "APP-INFO" :
            setAppInfo(o.ARG);
            break;
        case "SHOW-ALERT" :
            toastInfo(o.ARG);
            break;
        case "SHOW-INFO" :
            showInfo(o.ARG);
            break;
        case "SHOW-ERROR" :
            showError(o.ARG);
            break;
        case "SHOW-WAIT" :
            boxDialogWait(o.ARG);
            break;
        case "HIDE-WAIT" :
            boxDialogWaitClose();
            break;
        case "SHOW-PROGRESS" :
            boxDialogProgress(o.ARG["text"], o.ARG["percent"]);
            break;
        case "HIDE-PROGRESS" :
            boxDialogProgressClose();
            break;
        case "SERIAL-PORTS" :
            setSerialPorts(o.ARG);
            break;
        case "SERIAL-CONNECTION" :
            setSerialConnection(o.ARG);
            break;
        case "EXEC-CODE-BEGIN" :
            execCodeBegin();
            break;
        case "EXEC-CODE-RECV" :
            execCodeRecv(o.ARG);
            break;
        case "EXEC-CODE-ERROR" :
            execCodeError(o.ARG);
            break;
        case "EXEC-CODE-STOPPED" :
            execCodeStopped();
            break;
        case "EXEC-CODE-END" :
            execCodeEnd(o.ARG);
            break;
        case "FLASH-ROOT-PATH" :
            setFlashRootPath(o.ARG);
            break;
        case "PINS-LIST" :
            setPinsList(o.ARG);
            break;
        case "LIST-DIR" :
            setListDirAndFiles(o.ARG["path"], o.ARG["entries"]);
            break;
        case "END-OF-GET-FILE-CONTENT" :
            endOfGetFileContent();
            break;
        case "FILE-CONTENT-DATA" :
            recvFileContentData(o.ARG);
            break;
        case "END-OF-FILE-CONTENT-DATA" :
            endOfFileContentData();
            break;
        case "JAMA-FUNC-CONFIG" :
            recvJamaFuncConfig(o.ARG);
            break;
        case "JAMA-FUNC-IMPORTED" :
            recvJamaFuncImported(o.ARG);
            break;
        case "JAMA-FUNC-DELETED" :
            recvJamaFuncDeleted(o.ARG);
            break;
        case "DEVICE-RESET" :
            deviceReset();
            break;
        case "SYS-INFO" :
            setSystemInfo(o.ARG);
            break;
        case "NETWORKS-INFO" :
            setNetworksInfo(o.ARG);
            break;
        case "NETWORKS-MIN-INFO" :
            setNetworksMinInfo(o.ARG);
            break;
        case "AP-CLI-ADDR" :
            showAPClientsAddr(o.ARG);
            break;
        case "WIFI-NETWORKS" :
            setWiFiNetworks(o.ARG);
            break;
        case "MODULES" :
            importModules(o.ARG);
            break;
        case "ESPTOOL-VER" :
            setEsptoolPage(o.ARG);
            break;
        case "SDCARD-CONF" :
            setSDCardConf(o.ARG)
            break;
        case "MCU-SETTING-UPDATED" :
            mcuSettingUpdated();
            break;        
        case "WIFI-CONNECTED" :
            wifiConnected();
            break;
        case "WIFI-AP-OPENED" :
            wifiAPOpened();
            break;
        case "ETH-INITIALIZED" :
            ethInitialized();
            break;
        case "SD-CARD-MOUNTED" :
            sdCardMounted();
            break;
        case "DEVICE-INFO" :
            setDeviceInfo(o.ARG);
            break;
        case "AUTO-INFO" :
            setAutoInfo(o.ARG);
            break;
        case "WANT-CLOSE-SOFTWARE" :
            wantCloseSoftware();
    }
}

function onWSError(evt)
{
    showError("Fatal internal error..!")
}

function wsSendCmd(cmdName, oArg) {
    try {
        var o = { "CMD" : cmdName, "ARG" : oArg };
        websocket.send(JSON.stringify(o));
        return true;
    }
    catch (ex) {
        return false;
    }
}

function closeBoxDialog(box) {
    if (box.classList.contains("center-container-show")) {
        classToggle(box, "center-container-show", "hide");
        getElmById("protect-layer").classList.add("hide");
    }
}

function boxDialogCloseClick(e) {
    var t = getEventTarget(e);
    closeBoxDialog(t.parentNode.parentNode.parentNode);
}

function hideExistingBoxesDialog() {
    for (var box of document.getElementsByClassName("center-container-show"))
        classToggle(box, "center-container-show", "hide");
    getElmById("protect-layer").classList.add("hide");
}

function boxDialogAlert(title, text) {
    hideExistingBoxesDialog();
    var box = getElmById("box-dialog-alert");
    getSubElm(box, "box-dialog-title").innerText = title;
    getSubElm(box, "box-dialog-text").innerHTML  = textToHTML(text);
    getElmById("protect-layer").classList.remove("hide");
    classToggle(box, "hide", "center-container-show");
    getSubElm(box, "box-dialog-btn").focus();
}

function boxDialogYesNo(title, text, callbackFunc) {
    hideExistingBoxesDialog();
    var box = getElmById("box-dialog-yesno");
    getSubElm(box, "box-dialog-title").innerText = title;
    getSubElm(box, "box-dialog-text").innerHTML  = textToHTML(text);
    getElmById("protect-layer").classList.remove("hide");
    classToggle(box, "hide", "center-container-show");
    getSubElm(box, "box-dialog-btn").focus();
    boxDialogFunc = callbackFunc;
}

function boxDialogYesNoClick(e, yes) {
    var t   = getEventTarget(e);
    var box = t.parentNode.parentNode.parentNode;
    closeBoxDialog(box);
    if (boxDialogFunc)
        boxDialogFunc(yes);
}

function boxDialogQuery(title, text, value, callbackFunc, pwd) {
    hideExistingBoxesDialog();
    var box = getElmById("box-dialog-query");
    getSubElm(box, "box-dialog-title").innerText = title;
    getSubElm(box, "box-dialog-text").innerHTML  = textToHTML(text);
    var input = getSubElm(box, "box-dialog-input");
    input.value = value;
    input.setAttribute("type", (pwd ? "password" : ""));
    getElmById("protect-layer").classList.remove("hide");
    classToggle(box, "hide", "center-container-show");
    input.focus();
    boxDialogFunc = callbackFunc;
}

function boxDialogQueryOkClick(e) {
    var t   = getEventTarget(e);
    var box = t.parentNode.parentNode.parentNode;
    closeBoxDialog(box);
    if (boxDialogFunc)
        boxDialogFunc(getSubElm(box, "box-dialog-input").value);
}

function boxDialogGeneric(title, text, elmID, callbackFunc, hideCancel, btnOkText) {
    hideExistingBoxesDialog();
    boxDialogGenericReplaceObject();
    var elm = getElmById(elmID);
    var box = getElmById("box-dialog-generic");
    boxDialogGenericParentElm = elm.parentElement;
    boxDialogFunc             = callbackFunc;
    getSubElm(box, "box-dialog-title").innerText = title;
    getSubElm(box, "box-dialog-text").innerHTML  = textToHTML(text);
    getSubElm(box, "box-dialog-object").appendChild(elm);
    elm.classList.remove("hide");
    if (hideCancel)
        hide("box-dialog-generic-btn-cancel");
    else
        showInline("box-dialog-generic-btn-cancel");
    getElmById("box-dialog-generic-btn-ok").value = (btnOkText ? btnOkText : "Ok");
    getElmById("protect-layer").classList.remove("hide");
    classToggle(box, "hide", "center-container-show");
}

function boxDialogGenericReplaceObject() {
    if (boxDialogGenericParentElm) {
        var box = getElmById("box-dialog-generic");
        if (box) {
            var elm = getSubElm(box, "box-dialog-object").firstElementChild;
            elm.classList.add("hide");
            boxDialogGenericParentElm.appendChild(elm);
        }
        boxDialogGenericParentElm = null;
    }
}

function boxDialogGenericClick(e, ok) {
    var t   = getEventTarget(e);
    var box = t.parentNode.parentNode.parentNode;
    closeBoxDialog(box);
    boxDialogGenericReplaceObject();
    if (ok && boxDialogFunc)
        boxDialogFunc();
}

function boxDialogList(title, text, itemsConf, onClickCallback) {
    hideExistingBoxesDialog();
    var box = getElmById("box-dialog-list");
    getSubElm(box, "box-dialog-title").innerText = title;
    getSubElm(box, "box-dialog-text").innerHTML  = textToHTML(text);
    rmElmChildren("box-dialog-list-items");
    var list  = getElmById("box-dialog-list-items")
    var model = getElmById("list-item-model");
    for (var i = 0; i < itemsConf.length; i++) {
        var itemElm      = model.cloneNode(true);
        itemElm.id       = "";
        itemElm["ObjCB"] = itemsConf[i]["Value"];
        itemElm.addEventListener( "click", function(e) {
            e.preventDefault();
            closeBoxDialog(getElmById("box-dialog-list"));
            onClickCallback(e.currentTarget["ObjCB"]);
        } );
        getSubElm(itemElm, "picto1").classList.add(itemsConf[i]["Picto1"]);
        getSubElm(itemElm, "list-item-text").innerHTML = textToHTML(itemsConf[i]["Text"]);
        getSubElm(itemElm, "picto2").classList.add(itemsConf[i]["Picto2"]);
        itemElm.classList.remove("hide");
        list.appendChild(itemElm);
    }
    getElmById("protect-layer").classList.remove("hide");
    classToggle(box, "hide", "center-container-show");
    getSubElm(box, "box-dialog-btn").focus();
}

function boxDialogWait(text) {
    hideExistingBoxesDialog();
    var box = getElmById("box-dialog-wait");
    getSubElm(box, "box-dialog-text").innerHTML = textToHTML(text);
    if (box.classList.contains("hide")) {
        getElmById("protect-layer").classList.remove("hide");
        classToggle(box, "hide", "center-container-show");
    }
}

function boxDialogWaitClose() {
    var box = getElmById("box-dialog-wait");
    closeBoxDialog(box);
}

function boxDialogProgress(text, percent) {
    hideExistingBoxesDialog();
    var box = getElmById("box-dialog-progress");
    getSubElm(box, "box-dialog-text").innerHTML = textToHTML(text);
    var w = percent + "%";
    getSubElm(box, "progress-inner").style.width = w;
    getSubElm(box, "progress-text").innerText    = w;
    if (box.classList.contains("hide")) {
        getElmById("protect-layer").classList.remove("hide");
        classToggle(box, "hide", "center-container-show");
    }
}

function boxDialogProgressClose() {
    var box = getElmById("box-dialog-progress");
    closeBoxDialog(box);
}

function clearTerminal(cmTerm) {
    cmTerm._addLineBefore = null;
    cmTerm.setValue("");
    cmTerm.refresh();
}

function writeTextInTerminal(text, colorClass) {
    if (termTextBuffer != '') {
        var buf        = termTextBuffer;
        termTextBuffer = '';
        writeTextInTerminal(buf);
    }
    var ctnr   = getElmById( processing == PRC_EXEC_JAMA ? "elm-jama-func-terminal-container" : "terminal-container" );
    var cm     = ( processing == PRC_EXEC_JAMA ? codeMirrorJamaTerm : codeMirrorTerm );
    var doc    = cm.getDoc();
    var lCount = doc.lineCount();
    if (lCount >= 1100) {
        doc.replaceRange("", { line: 0 }, { line: lCount-1000 });
        lCount = doc.lineCount();
    }
    text = text.replaceAll("\r", "");
    if (cm._addLineBefore)
        text = "\n" + text;
    cm._addLineBefore = text.endsWith("\n");
    if (cm._addLineBefore)
        text = text.substring(0, text.length-1);
    doc.replaceRange(text, { line: Infinity });
    if (colorClass)
        for (var i = lCount; i < doc.lineCount(); i++)
            doc.addLineClass(i, "text", colorClass);
    ctnr.scrollTop = ctnr.scrollHeight;
    cm.refresh();
    termLastWriteMS = performance.now();
}

function eraseFlashClick(e) {
    boxDialogYesNo( "⚠️ ERASE?",
                    "Are you sure you want to erase all the flash memory on your device?",
                    function(yes) {
                        if (yes)
                            wsSendCmd("ERASE-FLASH", getElmById("select-esptool-port").value);
                    } );
}

function writeFirmwareClick(e) {
    wsSendCmd("WRITE-FIRMWARE", getElmById("select-esptool-port").value);
}

function setAppInfo(o) {
    appTitle = o.AppTitle;
    appVer   = o.AppVer;
    osName   = o.OSName;
    
    getElmById("menubar-title").innerText   = appTitle;
    getElmById("label-ver-on-os").innerText = "Version "+appVer+" on "+osName;
    
    setTimeout(checkUpdate, 7000);
}

function setSerialPorts(list) {
    if (showConnPortsDialog) {
        showConnPortsDialog = false;
        var itemsConf = [ ];
        for (var i = 0; i < list.length; i++)
            itemsConf.push( {
                "Value"  : list[i]["Device"],
                "Picto1" : ( list[i]["Device"]
                             ? ( list[i]["USB"]
                                 ? "list-item-picto-usb"
                                 : "list-item-picto-serial" )
                             : "list-item-picto-search" ),
                "Text"   : list[i]["Name"],
                "Picto2" : null
            } );
        boxDialogList( "😀 Connection to ESP32",
                       "Select the USB/serial port connected to the device:",
                       itemsConf,
                       function(value) {
                            wsSendCmd("CONNECT-SERIAL", value);
                       } );
    }
    rmElmChildren("select-esptool-port");
    var selElm = getElmById("select-esptool-port");
    for (var i = 0; i < list.length; i++) {
        var optElm   = newElm("option", null, null);
        optElm.value = list[i]["Device"];
        optElm.text  = list[i]["Name"];
        selElm.appendChild(optElm);
    }
    selElm.value = (currentPort != null ? currentPort : "");
}

function execCodeBegin() {
    if (processing == PRC_EXEC_CODE || processing == PRC_EXEC_JAMA) {
        refreshExecAndStopBtns();
        if (processing == PRC_EXEC_JAMA) {
            var name = execJamaFuncConfig.info.name;
            var ver  = String(execJamaFuncConfig.info.version).replaceAll(",", ".");
            boxDialogGeneric( "🚀 " + name + " (v" + ver + ")",
                              "",
                              "elm-jama-func-terminal-container",
                              null,
                              true,
                              "Close" );
            hide("jama-func-stop-btn");
            getElmById("box-dialog-generic-btn-ok").setAttribute("disabled", "true");
            setTimeout( function() {
                            clearTerminal(codeMirrorJamaTerm);
                            writeTextInTerminal("\n* Jama Func started.\n\n", "terminal-SeaGreen");
                        },
                        1 );
            var timeoutSec = execJamaFuncConfig.timeout;
            if (!timeoutSec && timeoutSec != 0)
                timeoutSec = 5;
            if (timeoutSec)
                execJamaStopTimeout = setTimeout( function() {
                    execJamaStopTimeout = null;
                    show("jama-func-stop-btn");
                },
                timeoutSec * 1000 );    
        }
        execAnimShowTime = setTimeout( function() {
            execAnimShowTime = null;
            showInline("img-processing");
        },
        500 );
    }

}

function execCodeRecv(text) {
    if (performance.now() - termLastWriteMS > 50)
        writeTextInTerminal(text);
    else
        termTextBuffer += text;
}

function execCodeError(error) {
    writeTextInTerminal(error + "\n", "terminal-IndianRed");
}

function execCodeStopped() {
    writeTextInTerminal("\n* The program has been interrupted!\n", "terminal-IndianRed");
}

function execCodeEnd(normalFinished) {
    if (processing == PRC_EXEC_CODE || processing == PRC_EXEC_JAMA) {
        if (processing == PRC_EXEC_JAMA) {
            getElmById("box-dialog-generic-btn-ok").removeAttribute("disabled");
            hide("jama-func-stop-btn");
            if (execJamaStopTimeout != null)
                clearInterval(execJamaStopTimeout);
            if (normalFinished)
                writeTextInTerminal("\n* Jama Func finished.\n", "terminal-SeaGreen");
        }
        if (execAnimShowTime != null)
            clearInterval(execAnimShowTime);
        writeTextInTerminal("\n");
        processing = PRC_NONE;
        refreshExecAndStopBtns();
        hide("img-processing");
        show("terminal-bar");
        getElmById("terminal-input-cmd").focus();
        if (connectionState)
            wsSendCmd("GET-LIST-DIR", browsePath);
    }
}

function setFlashRootPath(path) {
    flashRootPath = path;
    browsePath    = path;
}

function setPinsList(pList) {
    pinsList = pList;
    var actPage = getActivePage();
    if (actPage && actPage.id == "page-system-info") {
        rmElmChildren("sysnfo-pins-left");
        rmElmChildren("sysnfo-pins-right");
        var listLeftElm  = getElmById("sysnfo-pins-left");
        var listRightElm = getElmById("sysnfo-pins-right");
        var right        = false;
        for (var pin in pinsList) {
            var s     = (pinsList[pin] ? "up" : "down");
            var picto = newElm("div", null, ["list-item-picto", "left", "list-item-picto-pin-"+s]);
            var text  = newElm("div", null, ["list-item-text-float"]);
            text.innerHTML   = "GPIO-<b>" + pin + "</b> " + s;
            text.style.float = "none";
            if (right) {
                listRightElm.appendChild(picto);
                listRightElm.appendChild(text);
            }
            else {
                listLeftElm.appendChild(picto);
                listLeftElm.appendChild(text);
            }
            right = !right;
        }
        wsSendCmd("GET-PINS-LIST", true);
    }    
}

function deviceReset() {
    writeTextInTerminal("\n* ESP32 has been reset!\n\n", "terminal-IndianRed");
    var actPage = getActivePage();
    if (actPage)
        if (actPage.id == "page-system-info") {
            wsSendCmd("GET-SYS-INFO", true);
            wsSendCmd("GET-PINS-LIST", true);
        }
        if (actPage.id == "page-networks-info") {
            wsSendCmd("GET-NETWORKS-INFO", true);
            networkMiniInfos = { };
            wsSendCmd("GET-NETWORKS-MIN-INFO", null);
        }
        if (actPage.id == "page-sdcard")
            wsSendCmd("GET-SDCARD-CONF", true);
}

function showGPIOInfos() {
    var itemsConf = [ ];
    for (var i in pinoutModels)
        itemsConf.push( { "Value"  : pinoutModels[i],
                          "Picto1" : "list-item-picto-pins",
                          "Text"   : pinoutModels[i],
                          "Picto2" : null } );
    boxDialogList( "💡 GPIO pinout memo",
                   "Choose an Espressif board model to display the GPIO pinout memo:",
                   itemsConf,
                   function(value) {
                       setPinoutInfoImg(value);
                       getElmById("elm-list-pinout-info").value = value;
                       boxDialogGeneric( "💡 GPIO pinout of Espressif " + value,
                                         "",
                                         "elm-pinout-info",
                                         null,
                                         true,
                                         "Close" );
                   } );
}

function recvJamaFuncConfig(config) {
    var list          = getElmById("list-jama-funcs-items")
    var model         = getElmById("list-jama-funcs-item-model");
    var itemElm       = model.cloneNode(true);
    itemElm.id        = "";
    itemElm["Config"] = config;
    getSubElm(itemElm, "list-jama-funcs-item-open").addEventListener( "click", function(e) {
        e.preventDefault();
        var config = e.currentTarget.parentElement.parentElement["Config"]
        openJamaFuncsConfig(config)
    } );
    getSubElm(itemElm, "list-jama-funcs-item-export").addEventListener( "click", function(e) {
        e.preventDefault();
        var config  = e.currentTarget.parentElement.parentElement["Config"]
        wsSendCmd("EXPORT-JAMA-FUNC", config);
    } );
    getSubElm(itemElm, "list-jama-funcs-item-delete").addEventListener( "click", function(e) {
        e.preventDefault();
        var config = e.currentTarget.parentElement.parentElement["Config"];
        var ver    = String(config.info.version).replaceAll(",", ".");
        boxDialogYesNo( "⚠️ DELETE?",
                        "Are you sure you want to remove <b>" + config.info.name + " " + ver + "</b> from Jama Funcs?",
                        function(yes) {
                            if (yes)
                                wsSendCmd("DELETE-JAMA-FUNC", config);
                        } );
    } );
    getSubElm(itemElm, "list-jama-funcs-item-www").addEventListener( "click", function(e) {
        e.preventDefault();
        var config  = e.currentTarget.parentElement.parentElement["Config"]
        wsSendCmd("OPEN-URL", config.info.www);
    } );
    var cfgInfo = config.info;
    var ver     = cfgInfo.version;
    getSubElm(itemElm, "list-jama-funcs-item-name").innerText        = cfgInfo.name;
    getSubElm(itemElm, "list-jama-funcs-item-version").innerText     = "v" + ver[0] + "." + ver[1] + "." + ver[2];
    getSubElm(itemElm, "list-jama-funcs-item-description").innerText = cfgInfo.description;
    getSubElm(itemElm, "list-jama-funcs-item-author").innerText      = cfgInfo.author;
    var mailElm = getSubElm(itemElm, "list-jama-funcs-item-mail");
    var wwwElm  = getSubElm(itemElm, "list-jama-funcs-item-www");
    if (cfgInfo.mail) mailElm.innerText = cfgInfo.mail; else hideElm(mailElm);
    if (cfgInfo.www)  wwwElm.innerText  = cfgInfo.www;  else hideElm(wwwElm);
    itemElm.classList.remove("hide");
    list.appendChild(itemElm);
}

function openJamaFuncsConfig(config) {
    var ver = String(config.info.version).replaceAll(",", ".");
    getElmById("exec-jama-funcs-title").innerText       = config.info.name + " v" + ver;
    getElmById("exec-jama-funcs-description").innerText = config.info.description;
    getElmById("exec-jama-funcs-author").innerText      = "Developed by " + config.info.author;
    rmElmChildren("exec-jama-funcs-args");
    var argsTitle = getElmById("exec-jama-funcs-args-title");
    var argsElm   = getElmById("exec-jama-funcs-args");
    if (config.args && Object.keys(config.args).length > 0) {
        for (var arg in config.args) {
            var labelElm       = newElm("div", null, ["left"]);
            labelElm.innerText = "▶️ " + config.args[arg].label;
            argsElm.appendChild(labelElm);
            var type     = config.args[arg].type;
            var value    = config.args[arg].value;
            var fieldElm = null;
            if (type == "str") {
                fieldElm = newElm("input", null, ["exec-jama-funcs-input"]);
                fieldElm.setAttribute("type", "text");
                fieldElm.setAttribute("spellcheck", "false");
                if (value)
                    fieldElm.value = value;
            }
            else if (type == "int") {
                fieldElm = newElm("input", null, ["exec-jama-funcs-input"]);
                fieldElm.setAttribute("type", "number");
                fieldElm.value = (value ? value : "0");
            }
            else if (type == "float") {
                fieldElm = newElm("input", null, ["exec-jama-funcs-input"]);
                fieldElm.setAttribute("type", "number");
                fieldElm.setAttribute("step", "0.01");
                fieldElm.value = (value ? value : "0.00");
            }
            else if (type == "bool") {
                fieldElm = newElm("div", null, ["exec-jama-funcs-input", "exec-jama-funcs-bool"]);
                if (value)
                    fieldElm.classList.add("exec-jama-funcs-bool-on");
                else
                    fieldElm.classList.add("exec-jama-funcs-bool-off");
                fieldElm.addEventListener( "click", function(e) {
                    e.preventDefault();
                    var elm = e.currentTarget;
                    classToggle(elm, "exec-jama-funcs-bool-off", "exec-jama-funcs-bool-on");
                } );
            }
            else if (type == "list") {
                fieldElm   = newElm("select", null, ["exec-jama-funcs-input"]);
                var optElm = newElm("option", null, null);
                optElm.value = "";
                optElm.text  = "No GPIO";
                fieldElm.appendChild(optElm);
                for (var pin in pinsList) {
                    var optElm   = newElm("option", null, null);
                    optElm.value = pin;
                    optElm.text  = "GPIO-" + pin;
                    fieldElm.appendChild(optElm);
                }
                btnElm = newElm("input", null, ["button-little-text", "right"]);
                btnElm.type  = 'button';
                btnElm.value = ' 💡 ';
                btnElm.addEventListener("click", function(e) { showGPIOInfos(); });
                argsElm.appendChild(btnElm);
            }
            else if (type == "dict") {
                fieldElm  = newElm("select", null, ["exec-jama-funcs-input"]);
                var items = config.args[arg].items;
                for (var item in items) {
                    var optElm   = newElm("option", null, null);
                    optElm.value = item;
                    optElm.text  = items[item];
                    fieldElm.appendChild(optElm);
                }
                if (config.args[arg].value)
                    fieldElm.value = config.args[arg].value;
            }
            if (fieldElm) {
                fieldElm.classList.add("exec-jama-funcs-args-field");
                argsElm.appendChild(fieldElm);
            }
        }
        showElm(argsTitle);
        showElm(argsElm);
    }
    else {
        hideElm(argsTitle);
        hideElm(argsElm);
    }
    execJamaFuncConfig = config;
    showPage("page-exec-jama-funcs");
}

function recvJamaFuncImported(config) {
    refreshJamaFuncs();
}

function recvJamaFuncDeleted(config) {
    refreshJamaFuncs();
}

function setCurrentDirLabel(s) {
    getElmById("browse-current-dir").innerText = (s ? s : "...");
}

function getFileContent(filepath) {
    if (connectionState)
        if (processing == PRC_NONE) {
            var ctnr = getElmById("tabs-code-container");
            for (var i = 0; i < ctnr.children.length; i++) {
                var tabElm = ctnr.children[i];
                if (tabElm["tabData"]["filename"] == filepath) {
                    selectTabCode(tabElm);
                    showIDE();
                    return;
                }
            }
            processing        = PRC_TRANSFER;
            contentBytesArr   = [ ];
            contentRemotePath = filepath;
            wsSendCmd("GET-FILE-CONTENT", filepath);
        }
        else
            showError("A process is in execution...");
    else
        showError("The device must be connected first.");
}

function setListDirAndFiles(path, entries) {
    browsePath = path;
    setCurrentDirLabel("/" + path.substring(path.lastIndexOf("/")+1));
    rmElmChildren("browse-list-files");
    var list  = getElmById("browse-list-files");
    var model = getElmById("list-files-model");
    function _addEntry(filename, filesize) {
        var listElm           = model.cloneNode(true);
        listElm.id            = "";
        listElm["filenameCB"] = filename;
        listElm["filesizeCB"] = filesize;
        var title             = browsePath + "/" + filename;
        if (filesize != null)
            title += "\nFile size: " + sizeToText(filesize, "octets");
        listElm.setAttribute("Title", title);
        listElm.addEventListener( "click", function(e) {
            e.preventDefault();
            var elm      = e.currentTarget;
            var filename = elm["filenameCB"];
            if (elm.id != "list-files-selected") {
                var list = getElmById("browse-list-files")
                for (var i = 0; i < list.children.length; i++)
                    list.children[i].id = "";
                if (filename != "..")
                    elm.id = "list-files-selected";
            }
            else
                elm.id = "";
            setActifListFilesButtons();
        } );
        listElm.addEventListener( "dblclick", function(e) {
            e.preventDefault();
            var elm      = e.currentTarget;
            var filename = elm["filenameCB"];
            var filesize = elm["filesizeCB"];
            if (filename != "..") {
                elm.id = "list-files-selected";
                setActifListFilesButtons();
            }
            if (filesize == null) {
                var path;
                if (filename == "..")
                    path = browsePath.substring(0, browsePath.lastIndexOf("/"));
                else
                    path = browsePath + "/" + filename;
                setCurrentDirLabel(null);
                wsSendCmd("GET-LIST-DIR", path);
            }
            else if (filename.toUpperCase().endsWith(".PY"))
                getFileContent(browsePath + "/" + filename);
        } );
        var sdcard     = (browsePath + "/" + filename == sdcardMountPoint);
        var pictoClass = ( filesize == null
                                ? ( sdcard
                                    ? "list-files-picto-sdcard"
                                    : "list-files-picto-dir" )
                                : filename.toUpperCase().endsWith(".PY")
                                    ? "list-files-picto-file-python"
                                    : "list-files-picto-file" );
        getSubElm(listElm, "list-files-picto").classList.add(pictoClass);
        var text = (filesize == null ? "/" : "") + filename + "\n"
                 + (filesize == null ? (sdcard ? "SD card" : "Folder") : sizeToText(filesize, "octets"));
        getSubElm(listElm, "list-files-text").innerText = text;
        listElm.classList.remove("hide");
        list.appendChild(listElm);
    }
    if (path.startsWith(flashRootPath + "/") && path.length > flashRootPath.length + 1)
        _addEntry("..", null);
    for (var filename in entries)
        _addEntry(filename, entries[filename]);
    setActifListFilesButtons();
}

function addNewCodeEditorElm(code) {
    var ceElm = newElm("div", null, ["code-editor", "hide"]);
    var codeMirror = CodeMirror( ceElm, {
        mode              : "python",
        theme             : "lucario",
        lineNumbers       : true,
        indentUnit        : 4,
        tabSize           : 4,
        indentWithTabs    : false,
        smartIndent       : true,
        matchBrackets     : true,
        autoCloseBrackets : true,
        openDialog        : true,
        searchCursor      : true,
        search            : true,
        scrollbarStyle    : "overlay",
        extraKeys         : { "Ctrl-F"    : "findPersistent",
                              "Cmd-F"     : "findPersistent",
                              "Tab"       : (cm) => {
                                                if (cm.getMode().name === 'null')
                                                    cm.execCommand('insertTab');
                                                else
                                                    if (cm.somethingSelected())
                                                        cm.execCommand('indentMore');
                                                    else
                                                        cm.execCommand('insertSoftTab');
                                            },
                              "Shift-Tab" : (cm) => cm.execCommand('indentLess')
                            },
        value             : code
    } );
    codeMirror.setSize("100%", "100%");
    codeMirror.on("change", function(arg) {
        refreshExecAndStopBtns();
    });
    ceElm["codeMirror"] = codeMirror;
    getElmById("code-editors").appendChild(ceElm);
    return ceElm;
}

function createTabCode(filename, code) {
    var ctnr    = getElmById("tabs-code-container");
    var model   = getElmById("tab-code-model");
    var tabElm  = model.cloneNode(true);
    tabElm.id   = "";
    tabElm.addEventListener( "click", function(e) {
        e.preventDefault();
        var tabElm = e.currentTarget;
        selectTabCode(tabElm);
    } );
    tabElm.addEventListener( "dblclick", function(e) {
        e.preventDefault();
        e.stopPropagation();
    } );
    getSubElm(tabElm, "tab-code-close").addEventListener( "click", function(e) {
        e.preventDefault();
        e.stopPropagation();
        var tabElm = e.currentTarget.parentElement;
        wantToCloseTabCode(tabElm);
    } );
    tabElm["tabData"] = {
        "filename"   : null,
        "codeName"   : null,
        "codeEditor" : addNewCodeEditorElm(code),
        "originCode" : code
    };
    setTabCodeFilename(tabElm, filename);
    tabElm.classList.remove("hide");
    ctnr.appendChild(tabElm);
    selectTabCode(tabElm);
    refreshTabCodeScrollBtns();
}

function setTabCodeFilename(tabElm, newFilename) {
    var tabName = (newFilename ? newFilename.substring(newFilename.lastIndexOf("/")+1) : "New " + counterNewFile++);
    getSubElm(tabElm, "tab-code-text").innerText = tabName;
    if (newFilename)
        tabElm.setAttribute("Title", newFilename);
    tabElm["tabData"]["filename"] = newFilename;
    tabElm["tabData"]["codeName"] = tabName;
    refreshTabCodeScrollBtns();
}

function selectTabCode(tabElm) {
    if (tabElm.id != "tab-code-selected") {
        var selTabElm = getElmById("tab-code-selected");
        if (selTabElm) {
            selTabElm["tabData"]["codeEditor"].classList.add("hide");
            selTabElm.id = "";
        }
        var codeEditorElm = tabElm["tabData"]["codeEditor"];
        codeEditorElm.classList.remove("hide");
        var codeMirror = codeEditorElm["codeMirror"];
        codeMirror.refresh();
        codeMirror.focus();
        tabElm.id = "tab-code-selected";
        refreshTabCodeScrollBtns();
        getElmById("tabs-code-container-scroll").scrollLeft = tabElm.offsetLeft;
        refreshExecAndStopBtns();
    }
}

function isTabCodeModified(tabElm) {
    var tabData = tabElm["tabData"];
    return (tabData["codeEditor"]["codeMirror"].getValue() != tabData["originCode"]);
}

function closeTabCode(tabElm) {
    if (tabElm.id == "tab-code-selected") {
        tabs = Array.from(tabElm.parentElement.children);
        idx  = tabs.indexOf(tabElm);
        if (idx < tabs.length-1)
            selectTabCode(tabs[idx+1]);
        else if (idx > 0)
            selectTabCode(tabs[idx-1]);
        else
            createTabCode(null, "");
    }
    delElm(tabElm["tabData"]["codeEditor"]);
    delElm(tabElm);
    refreshTabCodeScrollBtns();

}

function wantToCloseTabCode(tabElm) {
    if (isTabCodeModified(tabElm)) {
        var filename = tabElm["tabData"]["filename"];
        var text     = ( filename
                         ? "Do you want to save the changes of file <b>'" + filename + "'</b> before closing it?"
                         : "Do you want to save this new file in <b>'" + browsePath + "/'</b> before closing it?" );
        boxDialogYesNo( "⚠️ NOT SAVED...",
                        text,
                        function(yes) {
                            if (yes)
                                saveTabCode(tabElm, true);
                            else
                                closeTabCode(tabElm);
                        } );
    }
    else
        closeTabCode(tabElm);
}

function recvFileContentData(data) {
    contentBytesArr = contentBytesArr.concat(data);
}

function endOfGetFileContent() {
    processing = PRC_NONE;
    var code   = "";
    if (contentBytesArr.length > 0) {
        var typedUTF8Data  = new Int8Array(contentBytesArr);
        var decoder        = new TextDecoder();
        code               = decoder.decode(typedUTF8Data);
        contentBytesArr    = [ ];
    }
    createTabCode(contentRemotePath, code);
    showIDE();
}

function saveTabCode(tabElm, closeTabAfter) {
    if (connectionState)
        if (processing == PRC_NONE) {
            var tabData  = tabElm["tabData"];
            var filename = tabData["filename"];
            var code     = tabData["codeEditor"]["codeMirror"].getValue();
            if (code) {
                if (filename == null) {
                    boxDialogQuery( "💾 Save new file",
                                    "Enter a filename to save your new MicroPython file in <b>" + browsePath + "/</b>:",
                                    "",
                                    function(filename) {
                                        filename = filename.trim();
                                        if (filename != "") {
                                            if (!filename.toUpperCase().endsWith(".PY"))
                                                filename += ".py";
                                            setTabCodeFilename(tabElm, browsePath + "/" + filename);
                                            saveTabCode(tabElm, closeTabAfter);
                                        }
                                } );
                    return;
                };
                processing          = PRC_TRANSFER;
                contentRemotePath   = filename;
                keepTabCodeElm      = tabElm;
                keepCloseTabCodeElm = closeTabAfter;
                var encoder         = new TextEncoder();
                var typedUTF8Data   = encoder.encode(code);
                var contentBytesArr = Array.from(typedUTF8Data);
                var args = {
                    "name" : contentRemotePath,
                    "size" : contentBytesArr.length
                }
                wsSendCmd("START-CONTENT-TRANSFER", args);
                var i = 0;
                do {
                    wsSendCmd("FILE-CONTENT-DATA", contentBytesArr.slice(i, i + 1024));
                    i += 1024;
                } while (i < contentBytesArr.length);
            }
        }
        else
            showError("A process is in execution...");
    else
        showError("The device must be connected first.");
}

function endOfFileContentData() {
    processing = PRC_NONE;
    if (keepTabCodeElm) {
        keepTabCodeElm["tabData"]["originCode"] = keepTabCodeElm["tabData"]["codeEditor"]["codeMirror"].getValue();
        if (keepCloseTabCodeElm)
            closeTabCode(keepTabCodeElm);
        keepTabCodeElm = null;
    }
    if (contentRemotePath.substring(0, contentRemotePath.lastIndexOf("/")) == browsePath)
        wsSendCmd("GET-LIST-DIR", browsePath);
}

function setSystemInfo(o) {

    getElmById("label-sysnfo-freq").innerText       = o.freq + " MHz";
    getElmById("label-sysnfo-flash-size").innerText = sizeToText(o.flashSize, "Bytes");
    getElmById("label-sysnfo-platform").innerText   = o.os.platform;
    getElmById("label-sysnfo-system").innerText     = o.os.system;
    getElmById("label-sysnfo-release").innerText    = o.os.release;
    getElmById("label-sysnfo-version").innerText    = o.os.version;
    getElmById("label-sysnfo-implem").innerText     = o.os.implem;
    setTextTag("label-sysnfo-spiram", (o.os.spiram ? "Yes" : "No"), o.os.spiram);
    getElmById("label-sysnfo-mpyver").innerText     = o.os.mpyver;

    var bootCfgElm = getElmById("sysnfo-boot-config");
    while (bootCfgElm.childElementCount > 0)
        bootCfgElm.removeChild(bootCfgElm.lastChild);
    for (var i in o.bootcfg) {
        var desc = ( o.bootcfg[i] == "BOOT" ? "🆗 Boot configuration file"       :
                     o.bootcfg[i] == "MCU"  ? "▶️ Update system setting"         :
                     o.bootcfg[i] == "STA"  ? "▶️ Connect Wi-Fi"                 :
                     o.bootcfg[i] == "AP"   ? "▶️ Open Wi-Fi access point"       :
                     o.bootcfg[i] == "ETH"  ? "▶️ Initialize Ethernet interface" :
                     o.bootcfg[i] == "SD"   ? "▶️ Mount SD card to file system"  :
                     null );
        if (desc) {
            var elm  = newElm("div", null, ["prop-item"]);
            var text = newElm("div", null, ["prop-item-text"]);
            text.innerText = desc;
            elm.appendChild(text);
            if (o.bootcfg[i] != 'BOOT' || o.bootcfg.length == 1) {
                var btnElm     = newElm("div", "bootcfg-" + o.bootcfg[i], ["prop-item-picto", "prop-item-picto-btn", "right", "list-item-picto-remove"]);
                btnElm.title   = "Remove this setting";
                btnElm["cfg"]  = o.bootcfg[i];
                btnElm["desc"] = desc;
                btnElm.addEventListener( "click", function(e) {
                    var target = getEventTarget(e);
                    boxDialogYesNo( "⚠️ REMOVE?",
                                    "<b>" + target.desc + "</b>\n" +
                                    "Are you sure you want to remove this setting from the boot of your device?",
                                    function(yes) {
                                        if (yes)
                                            wsSendCmd("REMOVE-CFG", target.cfg);
                                    } );
                } );
                elm.appendChild(btnElm);
            }
            bootCfgElm.appendChild(elm);
        }
    }

    var partElm = getElmById("sysnfo-partitions");
    while (partElm.childElementCount > 1)
        partElm.removeChild(partElm.lastChild);

    for (var i in o.partitions) {
        var part = o.partitions[i];
        var trElm = newElm("tr");

        var tdElm = newElm("td");
        tdElm.innerText = (part[0] == 0 ? "⚙️" : "💾");
        trElm.appendChild(tdElm);

        var tdElm = newElm("td");
        tdElm.innerText = part[4];
        trElm.appendChild(tdElm);
        
        var tdElm = newElm("td");
        tdElm.innerText = "0x" + part[2].toString(16);
        trElm.appendChild(tdElm);
        
        var tdElm = newElm("td");
        tdElm.innerText = "0x" + part[3].toString(16);
        trElm.appendChild(tdElm);

        var tdElm = newElm("td");
        tdElm.innerText = "(" + sizeToText(part[3], "bytes") + ")";
        trElm.appendChild(tdElm);

        var tdElm = newElm("td");
        if (part[5])
            tdElm.innerText = "🔑";
        trElm.appendChild(tdElm);

        partElm.appendChild(trElm);
    }
    
    var actPage = getActivePage();
    if (!actPage || actPage.id != "page-system-info") {
        showPage("page-system-info");
        setPinsList(o.pins);
    }

}

function setNetworksInfo(o) {

    if (!o.wifiSTA.active)
        hide("keepSTAConfigBtn");
    setTextTag("label-netnfo-wl-sta-active", (o.wifiSTA.active ? "Yes" : "No"), o.wifiSTA.active);
    if (o.wifiSTA.active) showInline("close-IF-STA"); else hide("close-IF-STA");
    getElmById("label-netnfo-wl-sta-mac").innerText     = o.wifiSTA.mac;
    getElmById("label-netnfo-wl-sta-ssid").innerText    = o.wifiSTA.ssid;
    getElmById("label-netnfo-wl-sta-ip").innerText      = o.wifiSTA.ip;
    getElmById("label-netnfo-wl-sta-mask").innerText    = o.wifiSTA.mask;
    getElmById("label-netnfo-wl-sta-gateway").innerText = o.wifiSTA.gateway;
    getElmById("label-netnfo-wl-sta-dns").innerText     = o.wifiSTA.dns;

    if (!o.wifiAP.active)
        hide("keepAPConfigBtn");
    setTextTag("label-netnfo-wl-ap-active", (o.wifiAP.active ? "Yes" : "No"), o.wifiAP.active);
    if (o.wifiAP.active) showInline("close-IF-AP"); else hide("close-IF-AP");
    getElmById("label-netnfo-wl-ap-mac").innerText      = o.wifiAP.mac;
    getElmById("label-netnfo-wl-ap-ssid").innerText     = o.wifiAP.ssid;
    getElmById("label-netnfo-wl-ap-ip").innerText       = o.wifiAP.ip;
    getElmById("label-netnfo-wl-ap-mask").innerText     = o.wifiAP.mask;
    getElmById("label-netnfo-wl-ap-gateway").innerText  = o.wifiAP.gateway;
    getElmById("label-netnfo-wl-ap-dns").innerText      = o.wifiAP.dns;
    if (o.wifiAP.active) showInline("show-AP-cli-addr"); else hide("show-AP-cli-addr");

    var ok = (o.eth && o.eth.mac);
    if (!ok)
        hide("keepETHConfigBtn");
    setTextTag("label-netnfo-eth-active", ( !o.eth ? "Not supported"
                                            : !ok ? "No driver"
                                              : o.eth.enable ? "Yes" : "No" ),
                                            ok ? o.eth.enable : null);
    if (o.eth && !ok)        showInline("init-ETH-driver"); else hide("init-ETH-driver");
    if (ok && !o.eth.enable) showInline("enable-IF-ETH");   else hide("enable-IF-ETH");
    if (ok && o.eth.enable)  showInline("disable-IF-ETH");  else hide("disable-IF-ETH");
    getElmById("label-netnfo-eth-mac").innerText        = (ok ? o.eth.mac : "");
    setTextTag("label-netnfo-eth-status", ( !ok || !o.eth.enable ? ""
                                            : !o.eth.linkup ? "Unplugged"
                                              : "Plugged in " + (o.eth.gotip ? "(IP Ok)" : "(No IP)")),
                                            ok && o.eth.enable ? o.eth.linkup : null);
    getElmById("label-netnfo-eth-ip").innerText         = (ok ? o.eth.ip : "");
    getElmById("label-netnfo-eth-mask").innerText       = (ok ? o.eth.mask : "");
    getElmById("label-netnfo-eth-gateway").innerText    = (ok ? o.eth.gateway : "");
    getElmById("label-netnfo-eth-dns").innerText        = (ok ? o.eth.dns : "");

    setTextTag("label-netnfo-internet-ok", (o.internetOK ? "Yes" : "No"), o.internetOK);
    
    setTextTag("label-netnfo-ble-active", (o.ble.active ? "Yes" : "No"), o.ble.active);
    if (o.ble.active) showInline("close-IF-BLE"); else hide("close-IF-BLE");
    getElmById("label-netnfo-ble-mac").innerText        = o.ble.mac;
    
    if (showNetworksInfoPage) {
        showNetworksInfoPage = false;
        var actPage = getActivePage();
        if (!actPage || actPage.id != "page-networks-info") {
            showPage("page-networks-info");
            networkMiniInfos = null;
            wsSendCmd("GET-NETWORKS-MIN-INFO", null);
        }
    }

}

function setNetworksMinInfo(o) {
    var actPage = getActivePage();
    if (actPage && actPage.id == "page-networks-info") {
        if (networkMiniInfos != null) {
            getElmById("label-netnfo-wl-sta-rssi").innerText   = (o.staRSSI ? o.staRSSI + " dBm" : "N/A");
            getElmById("label-netnfo-wl-ap-clients").innerText = (o.apStaCount != undefined ? o.apStaCount : "N/A");
            if ( Boolean(o.staRSSI)    != Boolean(networkMiniInfos.staRSSI)    ||
                 Boolean(o.apStaCount) != Boolean(networkMiniInfos.apStaCount) ||
                 o.ethStatus           != networkMiniInfos.ethStatus )
                wsSendCmd("GET-NETWORKS-INFO", true);
        }
        wsSendCmd("GET-NETWORKS-MIN-INFO", null);
    }
    networkMiniInfos = o;
}

function setWiFiNetworks(networks) {
    var itemsConf = [ ];
    for (var ssid in networks) {
        var rssi = networks[ssid]["rssi"];
        var r    = ( rssi == 0    ? 1 :
                     rssi <= -110 ? 1 :
                     rssi <  -100 ? 2 :
                     rssi <  -86  ? 3 :
                     rssi <  -70  ? 4 :
                     rssi <  -60  ? 5 :
                                    6 );
        itemsConf.push( {
            "Value"  : { ssid: ssid, secure: (networks[ssid]["authCode"] > 0) },
            "Picto1" : "list-item-picto-wifi-" + (networks[ssid]["authCode"] > 0 ? "secure" : "open"),
            "Text"   : ssid + " (" + networks[ssid]["authName"] + ")",
            "Picto2" : "list-item-picto-wifi-sig" + r
        } )
    };
    boxDialogList( "📡 Wireless network connection",
                   "Select a Wi-Fi access point to connect the device:",
                   itemsConf,
                   function(value) {
                        if (value.secure)
                            boxDialogQuery( "🔐 Secure Wi-Fi network",
                                            "The " + value.ssid + " access point requires an authentication key:",
                                            "",
                                            function(key) {
                                                key = key.trim();
                                                if (key != "") {
                                                    keepConfig.STA = { ssid: value.ssid, key: key };
                                                    wsSendCmd("WIFI-CONNECT", keepConfig.STA);
                                                }
                                                else
                                                    showError("The authentication key is required.");
                                            },
                                            true )
                        else
                            wsSendCmd("WIFI-CONNECT", { ssid: value.ssid, key: null });
                   } );
}

function mcuSettingUpdated() {
    show("keepMCUConfigBtn");
    boxDialogAlert( "😎 System setting updated with success!",
                    "The system setting of your device is now updated.\n" +
                    "Afterwards, you can make this configuration persistent." );
}

function wifiConnected() {
    show("keepSTAConfigBtn");
    boxDialogAlert( "😎 Wi-Fi connected with success!",
                    "The device is now connected to access point " + keepConfig.STA.ssid + ".\n" +
                    "Afterwards, you can make this configuration persistent." );
}

function wifiAPOpened() {
    show("keepAPConfigBtn");
    boxDialogAlert( "😎 Wi-Fi AP opened with success!",
                    "The device is now reachable on the access point " + keepConfig.AP.ssid + ".\n" +
                    "Afterwards, you can make this configuration persistent." );
}

function ethInitialized() {
    show("keepETHConfigBtn");
    boxDialogAlert( "😎 Ethernet initialized with success!",
                    "The Ethernet PHY interface is now initialized and can be activated.\n" +
                    "Afterwards, you can make this configuration persistent." );
}

function sdCardMounted() {
    show("keepSDConfigBtn");
    boxDialogAlert( "😎 SD card mounted with success!",
                    "The SD card is now mounted to the device's file system on " + keepConfig.SD.mountpt +".\n" +
                    "Afterwards, you can make this configuration persistent." );
}

function showAPClientsAddr(cliAddr) {
    if (cliAddr.length > 0) {
        var s = ""
        for (i in cliAddr)
            s += "\n<b>" + cliAddr[i] + "</b>";
        showInfo("MAC address of <b>" + cliAddr.length + "</b> client(s) currently connected to the AP:\n" + s);
    }
    else
        showInfo("No clients currently connected to the AP.");
}

function terminalFocusClick(e) {
    var doc = codeMirrorTerm.getDoc();
    if (!doc.somethingSelected())
        getElmById("terminal-input-cmd").focus();
}

function refreshJamaFuncs() {
    rmElmChildren("list-jama-funcs-items");
    wsSendCmd("GET-ALL-JAMA-FUNCS-CONFIG", null);
}

function importModules(modules) {
    var itemsConf = [ ];
    for (var i = 0; i < modules.length; i++)
        itemsConf.push( {
            "Value"  : modules[i],
            "Picto1" : "list-item-picto-python",
            "Text"   : "Module " + modules[i],
            "Picto2" : null
        } );
    boxDialogList( "⬇️ Import MicroPython module",
                   "Select an available MicroPython module to import:",
                   itemsConf,
                   function(value) {
                        wsSendCmd("IMPORT-MODULE", value);
                   } );
}

function setEsptoolPage(ver) {
    if (ver) {
        getElmById("esptool-version").innerText = "v" + ver;
        showPage("page-esptool");
    }
    else
        showPage("page-no-esptool");
}

function sizeToText(size, unity) {
    if (size >= 1024*1024*1024)
        return Math.round(size/1024/1024/1024*100)/100 + " G" + unity[0];
    if (size >= 1024*1024)
        return Math.round(size/1024/1024*100)/100 + " M" + unity[0];
    if (size >= 1024)
        return Math.round(size/1024*100)/100 + " K" + unity[0];
    return size + " " + unity;
}

function setSDCardConf(conf) {
    var ok = (conf != null);
    sdcardMountPoint = (ok ? conf.mountPoint : null);
    setTextTag("label-sdcard-init", (ok ? "Yes" : "No"), ok);
    if (!ok) showInline("sdcard-init"); else hide("sdcard-init");
    if (ok && conf.mountPoint == null) showInline("sdcard-release"); else hide("sdcard-release");
    if (ok && conf.mountPoint == null) showInline("sdcard-format"); else hide("sdcard-format");
    getElmById("label-sdcard-size").innerText = (ok ? sizeToText(conf.size, "octets") : "Unavailable");
    ok = (ok && conf.mountPoint != null);
    if (!ok)
        hide("keepSDConfigBtn");
    setTextTag("label-sdcard-mounted", (ok ? "Yes" : "No"), ok);
    if (!ok && conf != null) showInline("sdcard-mount"); else hide("sdcard-mount");
    if (ok) showInline("sdcard-umount"); else hide("sdcard-umount");
    getElmById("sdcard-mounted-point").innerText = (ok ? '"' + conf.mountPoint + '"' : "Unavailable");
    if (connectionState)
        wsSendCmd("GET-LIST-DIR", browsePath);
}

function setDeviceInfo(info) {
    getElmById("device-mcu").innerText    = info["deviceMCU"];
    getElmById("device-module").innerText = "On " + info["deviceModule"];
    show("device-info");
}

function setAutoInfo(info) {
    var memAlloc = info["mem"]["alloc"];
    var memFree  = info["mem"]["free"];
    var memTotal = memAlloc + memFree;
    var unity    = "Bytes";
    var text     = "RAM     " + sizeToText(memAlloc, unity) + " / " + sizeToText(memTotal, unity);
    var percent  = Math.round(memAlloc*100/memTotal);
    var progress = getElmById("mem-progress");
    getSubElm(progress, "progress-little-inner").style.width = percent + "%";
    getSubElm(progress, "progress-little-text").innerText    = text;
    if (info["temp"]) {
        var tempF    = info["temp"]["fahrenheit"];
        var tempC    = info["temp"]["celsius"];
        var text     = "TEMP    " + tempC + "°C (" + tempF + "°F)";
    }
    else {
        var tempC    = 0;
        var text     = "TEMP    " + "N/A on your device";
    }
    var progress = getElmById("temp-progress");
    getSubElm(progress, "progress-little-inner").style.width = tempC + "%";
    getSubElm(progress, "progress-little-text").innerText    = text;
    var uptime   = info["uptime"];
    var text     = "UPTIME  " + uptime + " minute" + (uptime > 1 ? "s" : "");
    var progress = getElmById("uptime-progress");
    getSubElm(progress, "progress-little-inner").style.width = "0";
    getSubElm(progress, "progress-little-text").innerText    = text;
    show("panel-connection");
}

function wantCloseSoftware() {
    var count            = 0;
    var modifiedTabNames = "";
    var ctnr             = getElmById("tabs-code-container");
    for (var i = 0; i < ctnr.children.length; i++) {
        var tabElm = ctnr.children[i];
        if (isTabCodeModified(tabElm)) {
            var filename = tabElm["tabData"]["filename"];
            modifiedTabNames += "<b>" + (filename ? filename : tabElm["tabData"]["codeName"]) + "</b>\n";
            count++;
        }
    }
    if (count)
        boxDialogYesNo( "⚠️ NOT SAVED...",
                        "Are you really sure you want to quit without saving?\n"
                        + "The following " + (count > 1 ? count + " files are" : "file is") + " modified but not saved:\n\n"
                        + modifiedTabNames,
                        function(yes) {
                            if (yes)
                                wsSendCmd("CLOSE-SOFTWARE", null);
                        } );
    else
        wsSendCmd("CLOSE-SOFTWARE", null);
}

function setSwitchButton(btnSwitch) {
    var switchBar = getElmById("switch-bar");
    for (var i = 0; i < switchBar.children.length; i++)
        switchBar.children[i].classList.remove("switch-button-selected");
    btnSwitch.classList.add("switch-button-selected");
    if (btnSwitch.id == "switch-btn-menu") {
        hide("menu-panel-browse");
        show("menu-panel-btns");
    }
    else if (btnSwitch.id == "switch-btn-browse") {
        hide("menu-panel-btns");
        show("menu-panel-browse");
        if (connectionState)
            wsSendCmd("GET-LIST-DIR", browsePath);
    }
}

function showIDE() {
    showPage("page-ide");
    show("ide-code");
    var termCtnr = getElmById("terminal-container");
    termCtnr.classList.remove("terminal-container-maxi");
    termCtnr.classList.add("terminal-container-mini");
    termCtnr.scrollTop = termCtnr.scrollHeight;
    codeMirrorTerm.refresh();
    getElmById("terminal-input-cmd").focus();
    var selTabData = getElmById("tab-code-selected")["tabData"];
    var codeMirror = selTabData["codeEditor"]["codeMirror"];
    codeMirror.refresh();
    codeMirror.focus();
    refreshExecAndStopBtns();
}

function showREPL() {
    showPage("page-ide");
    hide("ide-code");
    var ctnr = getElmById("terminal-container");
    ctnr.classList.remove("terminal-container-mini");
    ctnr.classList.add("terminal-container-maxi");
    codeMirrorTerm.refresh();
    getElmById("terminal-input-cmd").focus();
    refreshExecAndStopBtns();
}

function btnIDEClick(e) {
    if (connectionState)
        setSwitchButton(getElmById("switch-btn-browse"));
    showIDE();
}

function btnSDCardClick(e) {
    if (connectionState) {
        wsSendCmd("GET-SDCARD-CONF", true);
        showPage("page-sdcard");
    }
    else
        showError("The device must be connected first.");
}

function btnHardResetClick(e) {
    if (connectionState)
        boxDialogYesNo( "⚠️ RESET?",
                        "Are you sure you want to hard reset the device?",
                        function(yes) {
                            if (yes)
                                wsSendCmd("RESET", null);
                        } );
    else
        showError("The device must be connected first.");
}

function btnSysInfoClick(e) {
    wsSendCmd("GET-SYS-INFO", false);
}

function btnNetworksInfoClick(e) {
    showNetworksInfoPage = true;
    wsSendCmd("GET-NETWORKS-INFO", false);
}

function btnWiFiSTAClick(e) {
    wsSendCmd("GET-WIFI-NETWORKS", null);
}

function btnWiFiAPClick(e) {
    if (connectionState) {
        getElmById("elm-AP-ssid").value       = "";
        getElmById("elm-AP-auth").value       = "";
        getElmById("elm-AP-key").value        = "";
        getElmById("elm-AP-maxclients").value = "3";
        hide("elm-AP-key-container");
        boxDialogGeneric( "📡 Wireless access point setup",
                          "Configure the device's Wi-Fi access point:",
                          "elm-AP-setup",
                          function() {
                              ssid   = getElmById("elm-AP-ssid").value.trim();
                              auth   = getElmById("elm-AP-auth").value;
                              key    = (auth != "" ? getElmById("elm-AP-key").value : "");
                              maxcli = parseInt(getElmById("elm-AP-maxclients").value.trim());
                              if (ssid.length == 0)
                                  showError("The network name (SSID) cannot be empty.");
                              else if (auth != "" && key.length < 8)
                                  showError("The length of the key is too short.");
                              else if (isNaN(maxcli) || maxcli < 0 || maxcli > 10)
                                  showError("The maximum number of client connections is incorrect.");
                              else {
                                  keepConfig.AP = {
                                        ssid:   ssid,
                                        auth:   auth,
                                        key:    key,
                                        maxcli: maxcli
                                  }
                                  wsSendCmd("WIFI-OPEN-AP", keepConfig.AP);
                              }
                          } );
        getElmById("elm-AP-ssid").focus();
    }
    else
        showError("The device must be connected first.");
}

function elmAPAuthChange(e) {
    if (getElmById("elm-AP-auth").value != "")
        show("elm-AP-key-container");
    else
        hide("elm-AP-key-container");
}

function closeWirelessInterfaceClick(e, interface) {
    wsSendCmd("CLOSE-INTERFACE", interface);
}

function showAPClientsAddrClick(e) {
    wsSendCmd("GET-AP-CLI-ADDR", null);
}

function initETHDriverClick(e) {
    if (connectionState) {
        getElmById("elm-ETH-init-driver").value = "";
        getElmById("elm-ETH-init-addr"  ).value = "00";
        var mdcElm      = getElmById("elm-ETH-init-mdc");
        var mdioElm     = getElmById("elm-ETH-init-mdio");
        var powerElm    = getElmById("elm-ETH-init-power");
        var selElements = [mdcElm, mdioElm, powerElm];
        var optElm;
        for (var i in selElements) {
            rmElmChildren(selElements[i].id);
            optElm       = newElm("option", null, null);
            optElm.value = "";
            optElm.text  = (selElements[i] == powerElm ? "Not used" : "-- Choose a GPIO --");
            selElements[i].appendChild(optElm);
            for (var pin in pinsList) {
                    optElm       = newElm("option", null, null);
                    optElm.value = pin;
                    optElm.text  = "GPIO-" + pin;
                    selElements[i].appendChild(optElm);
            }
        }
        boxDialogGeneric( "🏗 Ethernet PHY initialization",
                          "You must configure the driver of the chipset:",
                          "elm-ETH-init",
                          function() {
                              var driver = getElmById("elm-ETH-init-driver").value;
                              var addr   = parseInt(getElmById("elm-ETH-init-addr").value.trim(), 16);
                              var mdc    = parseInt(getElmById("elm-ETH-init-mdc").value);
                              var mdio   = parseInt(getElmById("elm-ETH-init-mdio").value);
                              var power  = parseInt(getElmById("elm-ETH-init-power").value);
                              if (isNaN(power))
                                  power = null;
                              if (driver == "")
                                  showError("You must choose a chipset.");
                              else if (isNaN(addr) || addr < 0 || addr > 0x1F)
                                  showError("The PHY address is incorrect.");
                              else if (isNaN(mdc))
                                  showError("You must choose a mdc GPIO.");
                              else if (isNaN(mdio))
                                  showError("You must choose a mdio GPIO.");
                              else {
                                   keepConfig.ETH = {
                                        driver: driver,
                                        addr:   addr,
                                        mdc:    mdc,
                                        mdio:   mdio,
                                        power:  power
                                   }
                                   wsSendCmd("INIT_ETH_DRIVER", keepConfig.ETH);
                              }
                          } );
        getElmById("elm-ETH-init-driver").focus();
    }
    else
        showError("The device must be connected first.");
}

function enableInterfaceETHClick(e) {
    wsSendCmd("ENABLE_ETH_IF", null);
}

function disableInterfaceETHClick(e) {
    wsSendCmd("DISABLE_ETH_IF", null);
}

function keepConfigClick(e, configName) {
    if (configName == "MCU" && keepConfig.MCU)
        boxDialogYesNo( "💡 Keep system setting?",
                        "Do you want to keep this system setting in your device\nso that it is set automatically at each boot?",
                        function(yes) {
                            if (yes) {
                                hide("keepMCUConfigBtn");
                                wsSendCmd("SAVE-MCU-CFG", keepConfig.MCU);
                                wsSendCmd("GET-LIST-DIR", browsePath);
                            }
                        } );
    else if (configName == "STA" && keepConfig.STA)
        boxDialogYesNo( "💡 Keep Wi-Fi configuration?",
                        "Do you want to keep this Wi-Fi configuration in your device\nso that it connects automatically at each boot?",
                        function(yes) {
                            if (yes) {
                                hide("keepSTAConfigBtn");
                                wsSendCmd("SAVE-WIFI-STA-CFG", keepConfig.STA);
                                wsSendCmd("GET-LIST-DIR", browsePath);
                            }
                        } );
    else if (configName == "AP" && keepConfig.AP)
        boxDialogYesNo( "💡 Keep Wi-Fi AP configuration?",
                        "Do you want to keep this Wi-Fi access point configuration in your device\nso that it opens automatically at each boot?",
                        function(yes) {
                            if (yes) {
                                hide("keepAPConfigBtn");
                                wsSendCmd("SAVE-WIFI-AP-CFG", keepConfig.AP);
                                wsSendCmd("GET-LIST-DIR", browsePath);
                            }
                        } );
    else if (configName == "ETH" && keepConfig.ETH)
        boxDialogYesNo( "💡 Keep Ethernet configuration?",
                        "Do you want to keep this Ethernet PHY configuration in your device\nso that it initialises automatically at each boot?",
                        function(yes) {
                            if (yes) {
                                hide("keepETHConfigBtn");
                                wsSendCmd("SAVE-ETH-CFG", keepConfig.ETH);
                                wsSendCmd("GET-LIST-DIR", browsePath);
                            }
                        } );
    else if (configName == "SD" && keepConfig.SD)
        boxDialogYesNo( "💡 Keep SD card mounted?",
                        "Do you want to keep the SD card mounted on your device\nto maintain access to the file system at every boot?",
                        function(yes) {
                            if (yes) {
                                hide("keepSDConfigBtn");
                                wsSendCmd("SAVE-SD-CARD-CFG", keepConfig.SD);
                                wsSendCmd("GET-LIST-DIR", browsePath);
                            }
                        } );
}

function setPinoutInfoImg(name) {
    var url = "img/pinout/" + name + ".png";
    getElmById("elm-pinout-info").style.backgroundImage = "url('" + url + "')";
}

function elmListPinoutInfoChange(e) {
    setPinoutInfoImg(getElmById("elm-list-pinout-info").value);
}

function initSDCardClick(e) {
    wsSendCmd("SDCARD-INIT", null);
}

function formatSDCardClick(e) {
    boxDialogYesNo( "⚠️ FORMAT?",
                    "Are you sure you want to format the SD card that is in the device?\n\n" +
                    "Be careful: All your files stored on it will be lost!",
                    function(yes) {
                        if (yes)
                            wsSendCmd("SDCARD-FORMAT", null);
                    } );
}

function mountSDCardClick(e) {
    boxDialogQuery( "🛠 Mount the SD card:",
                    "Enter a name to mount the SD card to the device's file system:",
                    "/sd",
                    function(name) {
                        name = name.trim();
                        if (name != "") {
                            if (name[0] != "/")
                                name = "/" + name;
                            if (name.length > 1 && name.length < 256 && name.split("/").length-1 == 1) {
                                keepConfig.SD = { mountpt: name };
                                wsSendCmd("SDCARD-MOUNT", name);
                            }
                            else
                                showError("The name of this mount point is incorrect.");
                        }
                    } );
}

function umountSDCardClick(e) {
    wsSendCmd("SDCARD-UMOUNT", null);
}

function releaseSDCardClick(e) {
    wsSendCmd("SDCARD-RELEASE", null);
}

function btnSoftInfoEspIdfClick(e)
{ wsSendCmd("OPEN-URL", "https://github.com/espressif/esp-idf/releases"); }

function btnSoftInfoMPY(e)
{ wsSendCmd("OPEN-URL", "https://github.com/micropython/micropython/releases"); }

function btnSoftInfoMPYJama(e)
{ wsSendCmd("OPEN-URL", "https://github.com/jczic/ESP32-MPY-Jama/releases"); }

function btnSoftInfoEsptool(e)
{ wsSendCmd("OPEN-URL", "https://github.com/espressif/esptool/releases"); }

function btnSoftInfoDevKits(e)
{ wsSendCmd("OPEN-URL", "https://www.espressif.com/en/products/devkits"); }

function btnSoftInfoFirmwares(e)
{ wsSendCmd("OPEN-URL", "https://micropython.org/download?port=esp32"); }

function btnSoftInfoESP32Port(e)
{ wsSendCmd("OPEN-URL", "https://github.com/micropython/micropython/blob/master/ports/esp32/README.md"); }

function btnSoftInfoLibDoc(e)
{ wsSendCmd("OPEN-URL", "https://docs.micropython.org/en/latest/library"); }

function btnTerminalClick(e) {
    showREPL();
}

function btnJamaFuncsClick(e) {
    showPage("page-jama-funcs");
}

function btnFirmwareToolsClick(e) {
    wsSendCmd("GET-SERIAL-PORTS", null);
    wsSendCmd("GET-ESPTOOL-VER", null);
}

function btnSoftInfoClick(e) {
    showPage("page-soft-info");
}

function btnConnectionClick(e) {
    if (!connectionState) {
        showConnPortsDialog = true;
        wsSendCmd("GET-SERIAL-PORTS", null);
    }
    else
        wsSendCmd("DISCONNECT-SERIAL", null);
}

function btnSwitchClick(e) {
    setSwitchButton(getEventTarget(e));
}

function setConnectionState(connected) {
    if (connected == null) {
        connected = false
        writeTextInTerminal("\nWelcome to ESP32 MicroPython REPL terminal.\n\n", "terminal-SeaGreen");
    }
    else
        if (connected) {
            hideExistingBoxesDialog();
            writeTextInTerminal("* Device connected.\n\n", "terminal-SeaGreen");
        }
        else {
            hide("device-info");
            writeTextInTerminal("* Device disconnected.\n", "terminal-IndianRed");
        }
    connectionState = connected;
    getElmById("btn-connection").value = (connected ? "Disconnect" : "  Connect") + " device";
    setTextTag("label-connection", "DEVICE " + (connected ? "CONNECTED" : "NOT CONNECTED"), connected);
    if (!connected) {
        var actPage = getActivePage();
        if ( actPage && ( actPage.id == "page-networks-info" ||
                          actPage.id == "page-system-info"   ||
                          actPage.id == "page-sdcard" ) )
            hideElm(actPage)
        setSwitchButton(getElmById("switch-btn-menu"));
        hide("panel-connection");
        setListDirAndFiles("", { });
        setCurrentDirLabel(null);
        hide("keepMCUConfigBtn");
        hide("keepSTAConfigBtn");
        hide("keepAPConfigBtn");
        hide("keepETHConfigBtn");
        hide("keepSDConfigBtn");
        keepConfig = { };
        }
}

function setSerialConnection(port) {
    currentPort = port;
    setConnectionState(port != null);
    getElmById("select-esptool-port").value = (port != null ? port : "");
}

function execCode(code, codeFilename) {
    if (code.length > 0)
        if (connectionState) {
            if (processing == PRC_NONE) {
                processing = PRC_EXEC_CODE;
                if (code.indexOf("\n") >= 0) {
                    var encoder         = new TextEncoder();
                    var typedUTF8Data   = encoder.encode(code);
                    var contentBytesArr = Array.from(typedUTF8Data);
                    var args = {
                        "name" : codeFilename,
                        "size" : contentBytesArr.length
                    }
                    wsSendCmd("START-CONTENT-TRANSFER", args);
                    var i = 0;
                    do {
                        wsSendCmd("PROGRAM-CONTENT-DATA", contentBytesArr.slice(i, i + 1024));
                        i += 1024;
                    } while (i < contentBytesArr.length);
                }
                else {
                    hide("terminal-bar");
                    wsSendCmd( "EXEC-CODE", {
                        "code"         : code,
                        "codeFilename" : codeFilename
                    } );
                }
            }
            else
                showError("A process is already in execution.");
        }
        else
            showError("The device must be connected first.");
}

function importJamaFuncsClick(e) {
    wsSendCmd("IMPORT-JAMA-FUNC", null);
}

function saveJamaFuncsTemplateClick(e) {
    wsSendCmd("SAVE-JAMA-FUNCS-TEMPLATE", null);
}

function btnListFilesOpenClick(e) {
    if (connectionState && getEventTarget(e).classList.contains("browse-button-actif")) {
        var elm = getElmById("list-files-selected");
        if (elm != null) {
            var filename = elm["filenameCB"];
            getFileContent(browsePath + "/" + filename);
        }
    }
}

function btnListFilesExecuteClick(e) {
    if (connectionState && getEventTarget(e).classList.contains("browse-button-actif")) {
        var elm = getElmById("list-files-selected");
        if (elm != null)
            if (processing == PRC_NONE) {
                var filepath = browsePath + "/" + elm["filenameCB"];
                writeTextInTerminal("Attempts to execute file " + filepath + "...\n", "terminal-LightSkyBlue");
                hide("terminal-bar");
                processing = PRC_EXEC_CODE;
                wsSendCmd("EXEC-PY-FILE", filepath);
            }
            else
                showError("A process is already in execution.");
    }
}

function btnListFilesDownloadClick(e) {
    if (connectionState && getEventTarget(e).classList.contains("browse-button-actif")) {
        var elm = getElmById("list-files-selected");
        if (elm != null) {
            var filename = elm["filenameCB"];
            var filesize = elm["filesizeCB"];
            if (filesize != null)
                wsSendCmd("DOWNLOAD-FILE", browsePath + "/" + filename);
        }
    }
}

function btnListFilesUploadClick(e) {
    if (connectionState && getEventTarget(e).classList.contains("browse-button-actif")) {
        wsSendCmd("UPLOAD-FILE", browsePath + "/");
        wsSendCmd("GET-LIST-DIR", browsePath);
    }
}

function btnListFilesRenameClick(e) {
    if (connectionState && getEventTarget(e).classList.contains("browse-button-actif")) {
        var elm = getElmById("list-files-selected");
        if (elm != null) {
            var filename = elm["filenameCB"];
            var srcPath  = browsePath + "/" + filename;
            boxDialogQuery( "✒️ Rename",
                            "Enter a new name for <b>" + srcPath + "</b>:",
                            filename,
                            function(newName) {
                                newName = newName.trim();
                                if (newName != "") {
                                    var dstPath = browsePath + "/" + newName;
                                    wsSendCmd( "RENAME-FILE-OR-DIR", {
                                        "srcPath" : srcPath,
                                        "dstPath" : dstPath } );
                                    wsSendCmd("GET-LIST-DIR", browsePath);
                                }
                        } );
        }
    }
}

function btnListFilesRemoveClick(e) {
    if (connectionState && getEventTarget(e).classList.contains("browse-button-actif")) {
        var elm = getElmById("list-files-selected");
        if (elm != null) {
            var filepath = browsePath + "/" + elm["filenameCB"];
            boxDialogYesNo( "⚠️ DELETE?",
                            "Are you sure you want to remove <b>" + filepath + "</b> from your device?",
                            function(yes) {
                                if (yes) {
                                    wsSendCmd("DELETE-FILE-OR-DIR", filepath);
                                    wsSendCmd("GET-LIST-DIR", browsePath);
                                }
                            } );
        }
    }
}

function btnListFilesNewDirClick(e) {
    if (connectionState && getEventTarget(e).classList.contains("browse-button-actif"))
        boxDialogQuery( "📂 Create new folder",
                        "Create a new folder in <b>" + browsePath + "/</b>:",
                        "",
                        function(dirName) {
                            dirName = dirName.trim();
                            if (dirName != "") {
                                wsSendCmd("CREATE-DIR", browsePath + "/" + dirName);
                                wsSendCmd("GET-LIST-DIR", browsePath);
                            }
                    } );
}

function btnJamaFuncsExecClick(e) {
    if (connectionState) {
        if (processing == PRC_NONE) {
            var config        = execJamaFuncConfig;
            var argsFieldElms = getElmsByClass("exec-jama-funcs-args-field");
            var count         = 0;
            var o             = { };
            for (var arg in config.args) {
                var fieldElm = argsFieldElms[count++];
                var type     = config.args[arg].type;
                var value    = null;
                if (type == "str")
                    value = fieldElm.value.trim();
                else if (type == "int") {
                    var x = fieldElm.value.trim();
                    if (x != "" && !isNaN(Number(x)) && parseInt(x) == parseFloat(x))
                        value = parseInt(x);
                    else {
                        showError("Parameter <b>n°" + count + "</b> is not a correct <b>integer</b> value.");
                        return;
                    }
                }
                else if (type == "float") {
                    var x = fieldElm.value.trim();
                    if (x != "" && !isNaN(parseFloat(Number(x))))
                        value = parseFloat(x);
                    else {
                        showError("Parameter <b>n°" + count + "</b> is not a correct <b>float</b> value.");
                        return;
                    }
                }
                else if (type == "bool")
                    value = fieldElm.classList.contains("exec-jama-funcs-bool-on");
                else if (type == "list") {
                    if (fieldElm.value != "")
                        value = parseInt(fieldElm.value);
                    else if (!config.args[arg].optional) {
                        showError("A GPIO must be selected in the parameter <b>n°" + count + "</b>.");
                        return;
                    }
                }
                else if (type == "dict")
                    value = fieldElm.value;
                o[arg] = value;
            }
            processing = PRC_EXEC_JAMA;
            wsSendCmd("EXEC-JAMA-FUNC", {
                "config" : config,
                "values" : o
            });
        }
        else
            showError("A process is already in execution.");
    }
    else
        showError("The device must be connected first.");
}

function setActifListFilesButtons() {
    var f = function(id, actif) {
        if (actif)
            getElmById(id).classList.add("browse-button-actif");
        else
            getElmById(id).classList.remove("browse-button-actif");
    }
    var elm    = getElmById("list-files-selected");
    var selOk  = (elm != null);
    var selPY  = (selOk && elm["filenameCB"].toUpperCase().endsWith(".PY"));
    var selDir = (selOk && elm["filesizeCB"] == null);
    f("list-files-btn-open",     (connectionState && selPY && !selDir));
    f("list-files-btn-execute",  (connectionState && selPY && !selDir));
    f("list-files-btn-download", (connectionState && selOk && !selDir));
    f("list-files-btn-upload",   connectionState);
    f("list-files-btn-rename",   (connectionState && selOk));
    f("list-files-btn-remove",   (connectionState && selOk));
    f("list-files-btn-newdir",   connectionState);
}

function refreshExecAndStopBtns() {
    if (processing == PRC_EXEC_CODE || processing == PRC_EXEC_JAMA) {
        hide("exec-tiny-btn");
        show("stop-tiny-btn");
        if (getElmById("terminal-container").classList.contains("terminal-container-maxi"))
            show("exec-code-stop-btn");
        else
            hide("exec-code-stop-btn");
    }
    else {
        hide("stop-tiny-btn");
        show("exec-tiny-btn");
        var btnElm     = getElmById("exec-tiny-btn");
        var selTabData = getElmById("tab-code-selected")["tabData"];
        if (selTabData["codeEditor"]["codeMirror"].getValue())
            btnElm.classList.add("tiny-btn-green");
        else
            btnElm.classList.remove("tiny-btn-green");
        hide("exec-code-stop-btn");
    }
}

function connectWS() {
    try {
        var wsUri = "ws://" + window.location.hostname + ':' + window.location.port;
        websocket = new WebSocket(wsUri);
        websocket.addEventListener('open',    onWSOpen);
        websocket.addEventListener('close',   onWSClose);
        websocket.addEventListener('message', onWSMessage);
        websocket.addEventListener('error',   onWSError);
        return true;
    }
    catch (ex) {
        showError("Fatal internal error..!")
        return false;
    }
}

function refreshTabCodeScrollBtns() {
    tabsCodeCtnr       = getElmById("tabs-code-container");
    tabsCodeCtnrScroll = getElmById("tabs-code-container-scroll");
    if ( ( tabsCodeCtnr.scrollWidth > tabsCodeCtnrScroll.offsetWidth &&
           tabsCodeCtnrScroll.classList.contains("tabs-code-container-scroll-hide-btns") ) ||
         ( tabsCodeCtnr.scrollWidth <= tabsCodeCtnrScroll.offsetWidth &&
           tabsCodeCtnrScroll.classList.contains("tabs-code-container-scroll-show-btns") ) )
        classToggle(tabsCodeCtnrScroll, "tabs-code-container-scroll-hide-btns", "tabs-code-container-scroll-show-btns");
}

function timerAppSecond() {
    if (termTextBuffer != '')
        writeTextInTerminal('');
}

function getLatestVersions() {

    var setVer = function(elmId, owner, repo) {
        try {
            var elm = getElmById(elmId);
            var req = new XMLHttpRequest();
            req.onload = function() {
                var lastVer;
                try {
                    lastVer = JSON.parse(this.responseText).tag_name;
                    if (lastVer == undefined)
                        lastVer = 'error...'
                } catch (ex) {
                    lastVer = 'error...'
                }
                elm.innerText = lastVer;
            }
            elm.innerText = '...';
            req.open("get", "https://api.github.com/repos/"+owner+"/"+repo+"/releases/latest", true);
            req.send();
        } catch (ex) { }
    }

    setVer( "label-softver-espidf",  "espressif",   "esp-idf"        );
    setVer( "label-softver-mpy",     "micropython", "micropython"    );
    setVer( "label-softver-mpyjama", "jczic",       "ESP32-MPY-Jama" );
    setVer( "label-softver-esptool", "espressif",   "esptool"        );

}

function checkUpdate() {
    try {
        var req = new XMLHttpRequest();
        req.onload = function() {
            try {
                var lastVer = JSON.parse(this.responseText).tag_name;
                if (lastVer != undefined && lastVer != "v"+appVer)
                    boxDialogYesNo( "🚀 Update?",
                                    "A new version (" + lastVer + ") is available!\nDo you want to download it?",
                                    function(yes) {
                                        if (yes)
                                            wsSendCmd("OPEN-URL", GITHUB_REPOSITORY_URL);
                                    } );
            } catch (ex) { }
        }
        req.open("get", GITHUB_LAST_RELEASE_URL, true);
        req.send();
    } catch (ex) { }
}

window.addEventListener( "resize", function() {
    refreshTabCodeScrollBtns();
} );

window.addEventListener( "load", function() {

    if (!connectWS())
        return;

    codeMirrorTerm = CodeMirror( getElmById("terminal-repl"), {
        mode              : null,
        theme             : "repl",
        readOnly          : true,
        lineNumbers       : false,
        matchBrackets     : false,
        openDialog        : false,
        searchCursor      : false,
        search            : false,
        lineWrapping      : true
    } );
    codeMirrorTerm.setSize("100%", "fit-content");

    codeMirrorJamaTerm = CodeMirror( getElmById("jama-func-terminal"), {
        mode              : null,
        theme             : "repl",
        readOnly          : true,
        lineNumbers       : false,
        matchBrackets     : false,
        openDialog        : false,
        searchCursor      : false,
        search            : false,
        lineWrapping      : true
    } );
    codeMirrorJamaTerm.setSize("100%", "fit-content");

    var selElm = getElmById("elm-list-pinout-info");
    for (var i in pinoutModels) {
        var optElm   = newElm("option", null, null);
        optElm.value = pinoutModels[i];
        optElm.text  = pinoutModels[i];
        selElm.appendChild(optElm);
    }

    setConnectionState(null);
    setSwitchButton(getElmById("switch-btn-menu"));

    this.document.body.addEventListener("keypress", function(e) {
        if (e.metaKey) {
            var k = e.key.toUpperCase();
            if (k == "A" || k == "Z" || k == "Q")
                e.preventDefault();
        }
    } );
    
    getElmById("menubar-logo").addEventListener("click", function(e) {
        e.preventDefault();
        wsSendCmd("OPEN-URL", GITHUB_REPOSITORY_URL);
    } );

    getElmById("JCzic").addEventListener("click", function(e) {
        e.preventDefault();
        wsSendCmd("OPEN-URL", "https://soundcloud.com/jczic/sets/electro-pulse");
    } );

    getElmById("code-editors").addEventListener("keypress", function(e) {
        if ((e.metaKey || e.ctrlKey) && e.key.toUpperCase() == "S") {
            e.preventDefault();
            var selTab = getElmById("tab-code-selected");
            saveTabCode(selTab, false);
        }
    } );

    getElmById("terminal-input-cmd").addEventListener("keypress", function(e) {
        if (e.key === 13 || e.key.toUpperCase() === "ENTER")
            if (connectionState) {
                var input   = getElmById("terminal-input-cmd");
                var code    = input.value.trim();
                input.value = "";
                writeTextInTerminal("MicroPython >>> " + code + "\n\n", "terminal-LightSteelBlue");
                if (code.length > 0) {
                    input.blur();
                    cmdHistory.push(code);
                    cmdHistoryNav = cmdHistory.slice();
                    cmdHistoryNav.push("");
                    cmdHistoryIdx = cmdHistoryNav.length-1;
                    execCode(code, null);
                }
            }
            else
                showError("The device must be connected first.");
    } );

    getElmById("terminal-input-cmd").addEventListener("keydown", function(e) {
        var f = function(idxStep) {
            var input = getElmById("terminal-input-cmd");
            cmdHistoryNav[cmdHistoryIdx] = input.value;
            cmdHistoryIdx += idxStep;
            input.value = cmdHistoryNav[cmdHistoryIdx];
            e.preventDefault();
        };
        if (e.key.toUpperCase() == "ARROWUP")
            if (cmdHistoryIdx > 0)
                f(-1);
        if (e.key.toUpperCase() == "ARROWDOWN")
            if (cmdHistoryIdx < cmdHistoryNav.length-1)
                f(1);
    } );
    
    getElmById("jama-func-stop-btn").addEventListener("click", function(e) {
        e.preventDefault();
        wsSendCmd("EXEC-CODE-STOP", null);
    } );

    getElmById("new-tiny-btn").addEventListener("click", function(e) {
        e.preventDefault();
        createTabCode(null, "");
    } );

    getElmById("save-tiny-btn").addEventListener("click", function(e) {
        e.preventDefault();
        var tabElm = getElmById("tab-code-selected");
        saveTabCode(tabElm, false);
    } );

    getElmById("exec-tiny-btn").addEventListener("click", function(e) {
        e.preventDefault();
        var selTabData = getElmById("tab-code-selected")["tabData"];
        var codeName   = selTabData["codeName"];
        var code       = selTabData["codeEditor"]["codeMirror"].getValue();
        execCode(code, codeName);
    } );

    getElmById("stop-tiny-btn").addEventListener("click", function(e) {
        e.preventDefault();
        wsSendCmd("EXEC-CODE-STOP", null);
    } );

    getElmById("undo-tiny-btn").addEventListener("click", function(e) {
        e.preventDefault();
        var selTabData = getElmById("tab-code-selected")["tabData"];
        selTabData["codeEditor"]["codeMirror"].undo();
    } );

    getElmById("redo-tiny-btn").addEventListener("click", function(e) {
        e.preventDefault();
        var selTabData = getElmById("tab-code-selected")["tabData"];
        selTabData["codeEditor"]["codeMirror"].redo();
    } );

    getElmById("search-tiny-btn").addEventListener("click", function(e) {
        e.preventDefault();
        var selTabData = getElmById("tab-code-selected")["tabData"];
        selTabData["codeEditor"]["codeMirror"].execCommand('find');
    } );
    
    getElmById("modules-tiny-btn").addEventListener("click", function(e) {
        e.preventDefault();
        wsSendCmd("GET-MODULES", null);
    } );

    getElmById("packages-tiny-btn").addEventListener("click", function(e) {
        e.preventDefault();
        if (connectionState) {
            boxDialogQuery( "📦 Install package",
                            "Enter the package name to install it with your packages manager:\n(depending on your MicroPython installation <b>MIP</b> or <b>PyPI</b>)",
                            "",
                            function(name) {
                                name = name.trim();
                                if (name != "") {
                                    writeTextInTerminal("Installation of '" + name + "' package:\n", "terminal-LightSkyBlue");
                                    wsSendCmd("INSTALL-PACKAGE", name);
                                    wsSendCmd("GET-LIST-DIR", browsePath);
                                }
                            } );
        }
        else
            showError("The device must be connected first.");
    } );

    getElmById("gpio-tiny-btn").addEventListener("click", function(e) {
        e.preventDefault();
        showGPIOInfos();
    } );

    getElmById("tabs-code-container").addEventListener("dblclick", function(e) {
        e.preventDefault();
        createTabCode(null, "");
    } );

    getElmById("tabs-code-container-scroll-btn-left").addEventListener("click", function(e) {
        e.preventDefault();
        getElmById("tabs-code-container-scroll").scrollLeft -= 80;
    } );

    getElmById("tabs-code-container-scroll-btn-right").addEventListener("click", function(e) {
        e.preventDefault();
        getElmById("tabs-code-container-scroll").scrollLeft += 80;
    } );

    getElmById("exec-code-stop-btn").addEventListener("click", function(e) {
        e.preventDefault();
        wsSendCmd("EXEC-CODE-STOP", null);
    } );

    getElmById("change-freq").addEventListener("click", function(e) {
        e.preventDefault();
        var picto     = "list-item-picto-freq";
        var itemsConf = [ { "Value"  : 80,
                            "Picto1" : picto,
                            "Text"   : "80 MHz",
                            "Picto2" : null },
                          { "Value"  : 160,
                            "Picto1" : picto,
                            "Text"   : "160 MHz",
                            "Picto2" : null },
                          { "Value"  : 240,
                            "Picto1" : picto,
                            "Text"   : "240 MHz",
                            "Picto2" : null }
        ];
        boxDialogList( "📈 MCU frequency",
        "Choose a frequency to set on your ESP32:",
        itemsConf,
        function(value) {
            if (connectionState) {
                keepConfig.MCU = { freq: value };
                wsSendCmd("SET-MCU-FREQ", value);
            }
            else
                showError("The device must be connected first.");
        } );
    } );

    getElmById("openweb-esptool-installation").addEventListener("click", function(e) {
        e.preventDefault();
        wsSendCmd("OPEN-URL", "https://docs.espressif.com/projects/esptool/en/latest/esp32/installation.html");
    } );

    getElmById("openweb-esptool-commands").addEventListener("click", function(e) {
        e.preventDefault();
        wsSendCmd("OPEN-URL", "https://docs.espressif.com/projects/esptool/en/latest/esp32s3/esptool/basic-commands.html");
    } );
    
    createTabCode(null, "");

    getLatestVersions();

    var f = function() {
        setTimeout( function() {
            timerAppSecond();
            f();
        },
        1000 );
    }
    f();

} );