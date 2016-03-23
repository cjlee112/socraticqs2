'use strict';
define(['underscore', 'backbone'], function(_, Backbone) {
    var issue = Backbone.Model.extend({

       defaults:{
          'labels':[],
          'title':'',
          'description':'',
          'author_name':'',
          'assignee':''
        },

        initialize: function() {
        },

        clear: function() {
            this.destroy();
            this.view.remove();
        },

        validate: function(attrs, options) {
            var errors = this.errors = {};
            if (!attrs.title) errors.title = 'Title is required';
            if (!_.isEmpty(errors)) return errors;
        }
    });
    return issue;
});


