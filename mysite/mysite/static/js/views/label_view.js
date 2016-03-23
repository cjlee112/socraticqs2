'use strict';
define([
    'jquery',
    'underscore',
    'backbone',
    'collections/labels',
    ],

    function($, _, Backbone, Labels){
        var LabelView = Backbone.View.extend({

            template: _.template('<label data="<%= id %>" class="label <%= color %>"><%= title %></label>'),

            notModelTemplate: _.template('<label data="<%= id %>" class="label_to_add label <%= color %>"> <%= title %></label>'),

            initialize: function () {},

            render: function () {
                this.$el.empty();
                var labels = this.model.labels;
                for (var each in labels) {
                    var label = Labels.getLabelById(labels[each]).toJSON();
                    var new_label = this.template(label);
                    this.$el.append(new_label);
                }
                return this;
		    },

            renderNotModelLabels: function(el){
                el.empty();
                var modelLabels = this.model.labels;
                var labels = Labels.filter(function(x) {
                                    return $.inArray(x.id, modelLabels) < 0;
                                });
                for (var each in labels) {
                    var label = Labels.getLabelById(labels[each].id).toJSON();
                    var new_label = this.notModelTemplate(label);
                    el.append(new_label);
                }
            }

        });
	return LabelView;
});


