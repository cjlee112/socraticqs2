/**
 * @file Defines the CUI namespace that holds texts, config settings, and animation timeline references.
 */

 /**
  * @namespace
  */
var CUI = CUI || {};

/**
 * A dictionary of texts used throughout the app.
 * @namespace
 */
CUI.text = CUI.text = {};

CUI.text.errorCrash = "Something went wrong. Please refresh the page and try again a little later.";
CUI.text.errorTryAgain = "Something went wrong. Please try again.";
CUI.text.errorNoFullscreenSupport = "Your browser does not support fullscreen mode.";

/**
 * General config settings for the app.
 * @namespace
 */
 CUI.config = CUI.config || {};

 /* jshint ignore:start */
 /**
  * The chat's unique ID.
  * @type {number}
  * @public
  */
 CUI.config.chatID;

 /**
  * The url for loading the chat's history.
  * @type {string}
  * @public
  */
 CUI.config.historyUrl;

 /**
  * The url for loading information about progress.
  * @type {string}
  * @public
  */
 CUI.config.progressUrl;

 /**
  * A path to a default avatar for the student.
  * @type {string}
  * @public
  */
 CUI.config.defaultStudentAvatar;

 /**
  * A path to a default avatar for the teacher.
  * @type {string}
  * @public
  */
 CUI.config.defaultTeacherAvatar;

 /**
  * A namespace for globally available GSAP tweens and timelines.
  * @namespace
  */
 CUI.animation = CUI.animation = {};

 CUI.animation.pagePreloaderTimeline;
 CUI.animation.chatLoadingTimeline;
 /* jshint ignore:end */
