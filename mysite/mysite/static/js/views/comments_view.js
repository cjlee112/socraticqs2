'use strict';
define([
    'jquery',
    'underscore',
    'backbone',
    'collections/comments',
     'text!templates/issue_comment.html'
    ],

    function($, _, Backbone, Comments, comment_template){
        var CommentsView = Backbone.View.extend({

            template: _.template(comment_template),

            initialize: function () {

            },

            render: function () {
                this.$el.empty();
                var issueId = this.model.get('id');
                var commentsForIssue = Comments.filter(function(x) {return x.get('issue') == issueId});
                for (var each in commentsForIssue){
                    this.$el.append(this.renderOne(commentsForIssue[each].toJSON()));
                }
                return this;
		    },

            renderOne: function(comment){
                return this.template(comment);
            }

        });
	return CommentsView;
});


