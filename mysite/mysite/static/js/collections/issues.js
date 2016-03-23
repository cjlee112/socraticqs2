'use strict';
define(['underscore', 'backbone', 'models/issue'], function(_, Backbone, issue) {
    var IssuesCollection = Backbone.Collection.extend({
      model: issue,

      url: '/api/issues/',

      initialize: function(){
          this.on('add', this.onAdd, this);
      },

      is_open: function() {
         return this.filter(function( issue ) {
             return issue.get('is_open');
         });
      },

      compareBy:'title',

      comparator: function(issue) {
            return issue.get(this.compareBy);
      },

      is_close:function() {
         return this.without.apply( this, this.is_open());
      },

      onAdd: function(){
          console.log('Issue added')
      },

    });
    return new IssuesCollection;
});
