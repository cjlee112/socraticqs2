/**
 * @file Defines the content of the CUI.utils namespace.
 */

var CUI = CUI || {};

CUI.utils = CUI.utils || {};

/**
 * Attach a window scroll finished event emitter.
 * @global
 */
CUI.utils.attachScrollStoppedEmitter = function() {
    $window = $(window);

    $window.scroll(function() {
        var $this = $(this)
        clearTimeout($this.data('scroll-finished-detector'));

        $this.data('scroll-finished-detector', setTimeout(function() {
            $window.trigger('scrollStopped')
        }, 100));
    })
};
