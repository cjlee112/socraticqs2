'use strict';
define(['underscore', 'backbone'], function(_, Backbone) {
    var user = Backbone.Model.extend({

        initialize: function() {
        },

        clear: function() {
            this.destroy();
            this.view.remove();
        }
    });
    return user;
});