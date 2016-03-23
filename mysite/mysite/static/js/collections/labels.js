'use strict';
define(['underscore', 'backbone', 'models/label'], function(_, Backbone, label) {
    var LabelsCollection = Backbone.Collection.extend({
      model: label,

      url: '/api/labels/',

      initialize: function(){
          this.on('add', this.onAdd, this)
      },

      getLabelById: function(label_id){
            return this.find(function(x){return x.get('id') == label_id});
      },

      onAdd: function(){
          console.log('Label added')
      }
    });
    return new LabelsCollection;
});
