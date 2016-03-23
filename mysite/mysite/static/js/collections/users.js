'use strict';
define(['underscore', 'backbone', 'models/user'], function(_, Backbone, user) {
    var Users = Backbone.Collection.extend({
      model: user,

      url: '/ui/api/assignee/',

      initialize: function(){
          this.on('add', this.onAdd, this)
      },

      getUserById: function(id){
            return this.find(function(x){return x.get('id') == id});
      },

      onAdd: function(){
          console.log('User added')
      }
    });
    return new Users;
});