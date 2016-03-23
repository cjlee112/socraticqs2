'use strict';
define(['underscore', 'backbone'], function(_, Backbone) {
    var label = Backbone.Model.extend({
        defaults: {
            title: '',
            description: '',
            color: '',
            default: false,
        },

        initialize: function() {
        },

        clear: function() {
            this.destroy();
            this.view.remove();
        }
    });
    return label;
});
