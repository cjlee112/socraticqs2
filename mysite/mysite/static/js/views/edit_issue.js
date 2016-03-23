'use strict';
define([
    'jquery',
    'underscore',
    'backbone',
    'models/issue',
    'collections/issues',
    'collections/labels',
    'collections/users',
    'views/label_view',
    'text!templates/edit_add_issue.html'
    ],

    function($, _, Backbone, issue, Issues, Labels, Users, label_view, edit_issue){
        var EditIssueView = Backbone.View.extend({

            template: _.template(edit_issue),

            events:{
                "click #ok_button": 'updateIssue',
                "click #cancel_button": "goBackToMainView",
                "click .label_to_add": "addLabel",
                "click #labels>div>label": "removeLabel"
            },

            initialize: function () {
                this.for_template = this.model.toJSON();
                this.for_template['all_users'] = Users.toJSON();
                this.listenTo(this.model, 'change', this.goBackToMainView);
            },

            render: function () {
                this.$el.empty();
                this.$el.html(this.template(this.for_template));
                this.renderLabels();
		    },

            renderLabels: function(){
                var view = new label_view({model: this.for_template});
                $('#labels').html(view.render().el);
                view.renderNotModelLabels($('#all_labels'));
            },

            getFormInfo: function(){
                var for_template = this.for_template;
                var unindexed_array = $('#issue_form').serializeArray();
                $.map(unindexed_array, function(n, i){
                    for_template[n.name] = n.value;
                });
            },

            updateIssue: function(){
                $('.has-error').removeClass('has-error');
                $('.help-block').addClass('hidden');
                this.getFormInfo();
                var temp_model = new issue(this.for_template);
                if (temp_model.isValid()){this.model.save(this.for_template);}
                else{this.showErrors(temp_model.errors)}
            },

             goBackToMainView: function(){
                this.stopListening();
                this.undelegateEvents();
                this.trigger('cancel');
            },

            showErrors: function(errors){
                for (var e in errors){
                    var $error = $('[name=' + e + ']'),
                    $group = $error.closest('.form-group');
                    $group.addClass('has-error');
                    $group.find('.help-block').removeClass('hidden').html(errors[e]);
                }
            },

            addLabel: function(event){
                var label = parseInt(event.currentTarget.getAttribute('data'));
                var labels = Array.from(this.for_template.labels);
                labels.push(label);
                this.for_template.labels = labels;
                this.renderLabels();

            },

            removeLabel: function(event){
                var label = parseInt(event.currentTarget.getAttribute('data'));
                var labels = Array.from(this.for_template.labels);
                var index = this.for_template.labels.indexOf(parseInt(event.currentTarget.getAttribute('data')));
                labels.splice(index, 1);
                this.for_template.labels = labels;
                this.renderLabels();
            }
        });
	return EditIssueView;
});