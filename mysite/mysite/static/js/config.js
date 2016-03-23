require.config({
	// The shim config allows us to configure dependencies for
	// scripts that do not call define() to register a module
	shim: {
		underscore: {
			exports: '_'
		},
		backbone: {
			deps: [
				'underscore',
				'jquery'
			],
			exports: 'Backbone'
		}
	},
	paths: {
		jquery: '../jquery/jquery',
		underscore:'../underscore/underscore',
		backbone: '../backbone/backbone',
		text: '../text/text'
	}
});

require([
	'backbone',
	'views/main_tab_view',
	'utils/utils',
    'routers/router'
], function (Backbone, AppView, utils, Workspace) {
    // Main access point for our app
    var router = new Workspace();
    Backbone.history.start({pushState: true,
							root: '/'});

    var csrftoken = utils.getCookie('csrftoken');
    var oldSync = Backbone.sync;
    Backbone.sync = function(method, model, options){
        options.beforeSend = function(xhr){
            xhr.setRequestHeader('X-CSRFToken', csrftoken);
        };
		var _url = _.isFunction(model.url) ?  model.url() : model.url;
    	_url += _url.charAt(_url.length - 1) == '/' ? '' : '/';
    	options.url = _url;
        return oldSync(method, model, options);
    };

    new AppView({el:$('#lesson_issues')});


});
