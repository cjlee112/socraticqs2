define(['jquery',
	    'backbone',
	    'collections/issues',],

function ($, Backbone, Issues) {
	'use strict';

	var IssueRouter = Backbone.Router.extend({
		routes: {
			'ui/hack/lesson/:number(/)': 'doSomethig',
			'ui/hack/lesson/:number/:is_open(/)': 'is_open',
		},

        initialize: function(){
            Backbone.on('change_url',this.changeUrl);
        },

		is_open: function (number, is_open) {
            console.log(is_open);
            Backbone.trigger('unit_lesson',{unit_lesson: number});
			Issues.trigger(is_open);
		},

		doSomethig: function(number){
            console.log(number);
            Backbone.trigger('unit_lesson',{unit_lesson: number});
			this.trigger(number);
        },

        changeUrl: function (url){
            console.log(url);
        }
	});

	return IssueRouter;
});