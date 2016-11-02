/**
 * @file General helper functions and polyfills.
 */

// Ensure that browsers without support for console.log does not throw errors
window.console = window.console || { "log": function(log) {} };

// Catch uncaught exceptions and log errors
window.onerror = function(msg, url, line, col, error) {
   // Note that col & error are new to the HTML 5 spec and may not be
   // supported in every browser.  It worked for me in Chrome.
   var extra = !col ? '' : '\ncolumn: ' + col;
   extra += !error ? '' : '\nerror: ' + error;

   // Log the error to the console
   console.log("Error: " + msg + "\nurl: " + url + "\nline: " + line + extra);
   // TODO Log errors with ajax

   // Alert the user that something went wrong
   $.notify(CUI.text.errorCrash, {
     delay: 0
   });

   // If you return true, then error alerts (like in older versions of
   // Internet Explorer) will be suppressed.
   return true;
};

// Object.create polyfill
if (typeof Object.create != 'function') {
  Object.create = (function() {
    var Temp = function() {};
    return function (prototype) {
      if (arguments.length > 1) {
        throw Error('Second argument not supported');
      }
      if (typeof prototype != 'object') {
        throw TypeError('Argument must be an object');
      }
      Temp.prototype = prototype;
      var result = new Temp();
      Temp.prototype = null;
      return result;
    };
  })();
}
