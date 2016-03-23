'use strict';
define(['underscore', 'backbone'], function(_, Backbone) {
    var comment = Backbone.Model.extend({
        defaults: {
            issue: 1,
            parent: '',
            author: '',
            text: 'Empty comment',
            assignee: 'Unknown',
        },


        clear: function() {
            this.destroy();
            this.view.remove();
        },


        validate: function(attrs, options) {
            var errors = this.errors = {};
            if (!attrs.text) errors.text = 'Empty comment is a bad comment';
            if (!_.isEmpty(errors)) return errors;
        }
    });
    return comment;
});