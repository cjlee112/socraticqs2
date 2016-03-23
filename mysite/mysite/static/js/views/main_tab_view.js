'use strict';
define([
    'jquery',
    'underscore',
    'backbone',
    'collections/issues',
    'collections/labels',
    'collections/users',
    'collections/comments',
    'views/issue_row_view',
    'views/add_issue',
    'text!templates/issue_tab.html'
    ],

    function($, _, Backbone, Issues, Labels, Users, Comments, issue_row_view, add_issue_view, tab_template){
        var main_tab_view = Backbone.View.extend({

            template: _.template(tab_template),

            events:{
                'click .col-sm-2': 'addIssue',
                'click #byTitle': 'byTitle',
                'click #byAuthor': 'byAuthor',
                'click .choices': 'filterByLabels',
                'click #show_all_labels': 'addAll',
                'click #open_issues': 'goToOpen',
                'click #closed_issues': 'goToClosed'
            },

            initialize: function(){
                Backbone.on('unit_lesson', this.new_unit, this);
                this.listenTo(Issues, 'reset', this.render);
                this.listenTo(Issues, 'add', this.render);
                this.listenTo(Issues, 'open', this.addOpen);
                this.listenTo(Issues, 'closed', this.addClosed);
                this.filter = {is_open: true};
                Labels.fetch({reset:true});
                Users.fetch({reset:true});
                Backbone.history.loadUrl();
            },

            new_unit: function(param){
                Issues.fetch({data: param, reset:true});
            },

            render: function(){
                this.$el.html(this.template({closed_count: Issues.is_close().length,
                                             open_count: Issues.is_open().length,
                                             all_labels: Labels.toJSON(),
                                             filter: this.filter}));
                this.addAll();
            },

            addOne: function(issue){
                var view = new issue_row_view({model: issue});
                view.parent = this;
			    $('#table_of_issues').append(view.render().el);
            },

            addAll: function(){
                $('#table_of_issues').empty();
                var collection = Issues.where({is_open: this.filter.is_open});
                if (this.filter.label){
                    var label = this.filter.label;
                    collection = _.filter(collection, function(issue){ return $.inArray(label,issue.get('labels')) >= 0; });
                }
                for (var each in collection){
                    this.addOne(collection[each]);
                }

            },

            addOpen: function() {
                this.filter.is_open = true;
                $('#open_link_th').addClass('success');
                $('#close_link_th').removeClass('success');
                this.addAll();
            },

            addClosed: function() {
                this.filter.is_open = false;
                $('#open_link_th').removeClass('success');
                $('#close_link_th').addClass('success');
                this.addAll();
            },
            addIssue: function(){
                var view = new add_issue_view({el: this.el});
                this.listenToOnce(view, 'cancel', this.render);
                view.render();
            },

            byAuthor: function(){
                Issues.compareBy = 'author_name';
                Issues.sort();
                this.addAll();
            },

            byTitle: function(){
                Issues.compareBy = 'title';
                Issues.sort();
                this.addAll();
            },

            filterByLabels: function(event){
                this.filter.label = parseInt(event.currentTarget.getAttribute('data'));
                this.addAll();
            },

            goToOpen: function(e){
                e.preventDefault();
                var pathname = window.location.pathname;
                var firstPartOfPath = pathname.match( /\/ui\/hack\/lesson\/\d+/ )[0];
                Backbone.history.navigate(firstPartOfPath+'/open/');
                Issues.trigger('open');
            },

            goToClosed: function(e){
                e.preventDefault();
                var pathname = window.location.pathname;
                var firstPartOfPath = pathname.match( /\/ui\/hack\/lesson\/\d+/ )[0];
                Backbone.history.navigate(firstPartOfPath+'/closed/');
                Issues.trigger('closed');
            }

        });
        return main_tab_view;
    }
);
