'use strict';
define(['underscore', 'backbone', 'models/comment'], function(_, Backbone, comment) {
    var CommentsCollection = Backbone.Collection.extend({
      model: comment,

      url:'/api/comments/',

      initialize: function(options){
          options || (options = {});
          this.issue_id = options.issue_id;
          console.log(this.issue_id);
          this.on('add', this.onAdd, this)
      },

      onAdd: function(){
          console.log('Comment added')
      }
    });
    return new CommentsCollection;
});