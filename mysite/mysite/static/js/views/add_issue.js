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

    function($, _, Backbone, issue, Issues, Labels, Users, label_view, add_issue){
        var AddIssueView = Backbone.View.extend({

            template: _.template(add_issue),

            events:{
                "click #ok_button": 'CreateNewIssue',
                "click #cancel_button": "goBackToMainView",
                "click .label_to_add": "addLabel",
                "click #labels div label": "removeLabel"
            },

            initialize: function () {
                this.listenTo(Issues, 'add', function(){
                                            this.stopListening();
                                            this.undelegateEvents();});
                this.model = new issue({'author':window.settings.user,'labels':[]});
                this.for_template = this.model.toJSON();
                this.for_template['all_users'] = Users.toJSON();
            },

            render: function () {
                this.$el.empty();
                this.$el.html(this.template(this.for_template));
                this.renderLabels();
		    },

             renderLabels: function(){
                $
                var view = new label_view({model: this.model});
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

            CreateNewIssue: function(){
                $('.has-error').removeClass('has-error');
                $('.help-block').addClass('hidden');
                this.getFormInfo()
                var temp_model = new issue(this.for_template);
                if (temp_model.isValid()){
                    Issues.create(temp_model);
                }
                else{
                    this.showErrors(temp_model.errors)
                }
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
                this.for_template.labels.push(parseInt(event.currentTarget.getAttribute('data')));
                this.renderLabels();
            },

            removeLabel: function(event){
                var index = this.for_template.labels.indexOf(parseInt(event.currentTarget.getAttribute('data')));
                this.for_template.labels.splice(index, 1);
                this.renderLabels();
            }
        });
	return AddIssueView;
});