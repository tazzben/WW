var _os_ = (function(){
var userAgent = navigator.userAgent.toLowerCase();
var pat = new RegExp('10[\_\.]([0-9]*)');
var mt = userAgent.match(pat);
if (mt[1] >= 14){
   isNew = true;
}else{
   isNew = false;
}
return {
    isNew: isNew,
};
}());



function getOS() {
  var userAgent = window.navigator.userAgent,
      platform = window.navigator.platform,
      macosPlatforms = ['Macintosh', 'MacIntel', 'MacPPC', 'Mac68K'],
      windowsPlatforms = ['Win32', 'Win64', 'Windows', 'WinCE'],
      os = null;
  if (macosPlatforms.indexOf(platform) !== -1) {
    os = 'Mac OS';
  } else if (windowsPlatforms.indexOf(platform) !== -1) {
    os = 'Windows';
  } else if (!os && /Linux/.test(platform)) {
    os = 'Linux';
  }
  return os;
}

function getGUIURL(){
  var os = getOS();
  if (os == 'Mac OS'){
    if(_os_.isNew){
window.location = 'http://downloads.bensresearch.com/ADGUI_MAC.zip';
    }else{
window.location = 'http://downloads.bensresearch.com/ADGUI_MACOLD.zip';
    }
    
  }else if(os == 'Windows'){
    window.location = 'http://downloads.bensresearch.com/ADGUI_WIN.zip';
  }else{
    alert('Sorry, your OS is not supported.  Currently there is only a Windows and Mac version the GUI software.  The command line version supports Linux as well.');
  }
  gtag('event', 'download_gui', {
    'event_category': 'Download',
    'event_label': os,
    'event_action': 'download_gui'
  });
return false;
}

function getCLIURL(){
  var os = getOS();
  
  if (os == 'Mac OS'){
    window.location = 'http://downloads.bensresearch.com/ww_out_mac.zip';
  }else if(os == 'Windows'){
    window.location = 'http://downloads.bensresearch.com/ww_out_win.zip';
  }else if(os == 'Linux'){
    window.location = 'http://downloads.bensresearch.com/ww_out_linux_x64.zip';
  }else{
    alert('Sorry, your OS is not supported.  Currently there is only a Windows, Mac, and Linux version the CLI software.');
  }
  gtag('event', 'download_cli', {
    'event_category': 'Download',
    'event_label': os,
    'event_action': 'download_cli' 
  });
return false;
}