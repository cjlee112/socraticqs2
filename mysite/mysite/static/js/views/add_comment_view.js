'use strict';
define([
    'jquery',
    'underscore',
    'backbone',
    'models/comment',
    'collections/comments',
     'text!templates/add_comment.html'
    ],

    function($, _, Backbone, comment, Comments, add_comment_template){
        var CommentsView = Backbone.View.extend({

            template: _.template(add_comment_template),

            events: {
                "click #add_comment": "addComment"
            },

            initialize: function (a) {
                this.model = new comment({'author':window.settings.user,
                                            'author_name':''});
                this.listenTo(Comments, 'change', function(){this.stopListening();
                                                             this.undelegateEvents();});
            },

            render: function () {
                this.model.attributes.issue = this.issue;

                this.$el.html(this.template);
		    },

            addComment: function(){
                var unindexed_array = $('#comment_form').serializeArray();
                this.model.attributes.text = unindexed_array[0].value;
                if (this.model.isValid()){
                    Comments.create(this.model);
                }
                else{
                    this.showErrors(this.model.errors)
                }

            },

            showErrors: function(errors){
                for (var e in errors){
                    var $error = $('[name=' + e + ']'),
                    $group = $error.closest('.form-group');
                    $group.addClass('has-error');
                    $group.find('.help-block').removeClass('hidden').html(errors[e]);
                }
            },
        });
	return CommentsView;
});


