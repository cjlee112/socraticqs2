'use strict';
define([
    'jquery',
    'underscore',
    'backbone',
    'collections/issues',
    'collections/users',
    'collections/comments',
    'views/edit_issue',
    'views/label_view',
    'views/comments_view',
    'views/add_comment_view',
    'text!templates/issue_detail.html'
    ],

    function($, _, Backbone, Issues, Users, Comments, edit_issue, label_view, comments_view, add_comment_view, issue_detail_template){
        var IssueDetailView = Backbone.View.extend({
            template: _.template(issue_detail_template),

            events:{
                'click #issue_detail_cancel_button': 'goBackToMainView',
                'click #open_button': 'openIssue',
                'click #close_button': 'closeIssue',
                'click #edit_issue': 'editIssue'
            },

            initialize: function(){
                this.listenTo(this.model, 'change', this.render);
                this.listenTo(Comments, 'change', this.renderComments);
                this.listenTo(Comments, 'reset', this.renderComments);
                Comments.fetch({data: {issue_id:this.model.get('id')}, reset:true});
            },

            render: function () {
                var for_template = this.model.toJSON();
                if (for_template.assignee) {
                    for_template.assignee_name = Users.getUserById(for_template.assignee).toJSON();}
                else {
                    for_template.assignee_name = '';
                }
                this.$el.html(this.template(for_template));
                var view = new label_view({model: this.model.toJSON()});
                this.$el.find('#labels').append(view.render().el);
		    },

            renderComments: function(){
                var commentView = new comments_view({model: this.model});
                $('#comments').html(commentView.render().el);
                var commentFormView = new add_comment_view({el:$('#for_comment_form')});
                commentFormView.issue = this.model.get('id');
                commentFormView.render();
            },

            goBackToMainView: function(){
                this.stopListening();
                this.undelegateEvents();
                Issues.trigger('reset');
            },

            editIssue: function(){
                var view = new edit_issue({model: this.model, el: this.el});
                this.listenToOnce(view, 'cancel', this.render);
                view.render();
            },

            openIssue: function(){
                this.model.save({is_open: true});
            },

            closeIssue: function(){
                this.model.save({is_open: false});
            }
        });
	return IssueDetailView;
});
