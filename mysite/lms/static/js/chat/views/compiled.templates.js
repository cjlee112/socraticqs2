/** @file Creates the CUI.templates namespace and defines all templates. */ 
 var CUI = CUI || {}; 
 /** Contains Handlebars view templates 
 * @namespace */ 
 CUI.views = CUI.views || {}; 
this["CUI"] = this["CUI"] || {};
this["CUI"]["views"] = this["CUI"]["views"] || {};
this["CUI"]["views"]["chatBackToBreakpointButton"] = Handlebars.template({"compiler":[8,">= 4.3.0"],"main":function(container,depth0,helpers,partials,data) {
    var helper, alias1=depth0 != null ? depth0 : (container.nullContext || {}), alias2=container.hooks.helperMissing, alias3="function", alias4=container.escapeExpression, lookupProperty = container.lookupProperty || function(parent, propertyName) {
        if (Object.prototype.hasOwnProperty.call(parent, propertyName)) {
          return parent[propertyName];
        }
        return undefined
    };

  return "<button class=\"chat-previous-thread\" data-thread-id=\""
    + alias4(((helper = (helper = lookupProperty(helpers,"threadId") || (depth0 != null ? lookupProperty(depth0,"threadId") : depth0)) != null ? helper : alias2),(typeof helper === alias3 ? helper.call(alias1,{"name":"threadId","hash":{},"data":data,"loc":{"start":{"line":1,"column":53},"end":{"line":1,"column":65}}}) : helper)))
    + "\" data-type="
    + alias4(((helper = (helper = lookupProperty(helpers,"type") || (depth0 != null ? lookupProperty(depth0,"type") : depth0)) != null ? helper : alias2),(typeof helper === alias3 ? helper.call(alias1,{"name":"type","hash":{},"data":data,"loc":{"start":{"line":1,"column":77},"end":{"line":1,"column":85}}}) : helper)))
    + ">"
    + alias4(((helper = (helper = lookupProperty(helpers,"html") || (depth0 != null ? lookupProperty(depth0,"html") : depth0)) != null ? helper : alias2),(typeof helper === alias3 ? helper.call(alias1,{"name":"html","hash":{},"data":data,"loc":{"start":{"line":1,"column":86},"end":{"line":1,"column":94}}}) : helper)))
    + "</button>";
},"useData":true});
this["CUI"]["views"]["chatBreakpoint"] = Handlebars.template({"compiler":[8,">= 4.3.0"],"main":function(container,depth0,helpers,partials,data) {
    var stack1, helper, alias1=depth0 != null ? depth0 : (container.nullContext || {}), alias2=container.hooks.helperMissing, alias3="function", alias4=container.escapeExpression, lookupProperty = container.lookupProperty || function(parent, propertyName) {
        if (Object.prototype.hasOwnProperty.call(parent, propertyName)) {
          return parent[propertyName];
        }
        return undefined
    };

  return "<div class=\"chat-breakpoint\" data-thread-id=\""
    + alias4(((helper = (helper = lookupProperty(helpers,"threadId") || (depth0 != null ? lookupProperty(depth0,"threadId") : depth0)) != null ? helper : alias2),(typeof helper === alias3 ? helper.call(alias1,{"name":"threadId","hash":{},"data":data,"loc":{"start":{"line":1,"column":45},"end":{"line":1,"column":57}}}) : helper)))
    + "\" data-message-id=\""
    + alias4(((helper = (helper = lookupProperty(helpers,"id") || (depth0 != null ? lookupProperty(depth0,"id") : depth0)) != null ? helper : alias2),(typeof helper === alias3 ? helper.call(alias1,{"name":"id","hash":{},"data":data,"loc":{"start":{"line":1,"column":76},"end":{"line":1,"column":82}}}) : helper)))
    + "\">\n  <span>"
    + ((stack1 = ((helper = (helper = lookupProperty(helpers,"html") || (depth0 != null ? lookupProperty(depth0,"html") : depth0)) != null ? helper : alias2),(typeof helper === alias3 ? helper.call(alias1,{"name":"html","hash":{},"data":data,"loc":{"start":{"line":2,"column":8},"end":{"line":2,"column":18}}}) : helper))) != null ? stack1 : "")
    + "</span>\n</div>\n";
},"useData":true});
this["CUI"]["views"]["chatMedia"] = Handlebars.template({"1":function(container,depth0,helpers,partials,data) {
    return " chat-message-media-thumbnail ";
},"3":function(container,depth0,helpers,partials,data) {
    return " chat-message-with-caption ";
},"5":function(container,depth0,helpers,partials,data) {
    var stack1, helper, lookupProperty = container.lookupProperty || function(parent, propertyName) {
        if (Object.prototype.hasOwnProperty.call(parent, propertyName)) {
          return parent[propertyName];
        }
        return undefined
    };

  return "        <div class=\"caption\">\n          "
    + ((stack1 = ((helper = (helper = lookupProperty(helpers,"caption") || (depth0 != null ? lookupProperty(depth0,"caption") : depth0)) != null ? helper : container.hooks.helperMissing),(typeof helper === "function" ? helper.call(depth0 != null ? depth0 : (container.nullContext || {}),{"name":"caption","hash":{},"data":data,"loc":{"start":{"line":11,"column":10},"end":{"line":11,"column":23}}}) : helper))) != null ? stack1 : "")
    + "\n        </div>\n";
},"7":function(container,depth0,helpers,partials,data) {
    var stack1, lookupProperty = container.lookupProperty || function(parent, propertyName) {
        if (Object.prototype.hasOwnProperty.call(parent, propertyName)) {
          return parent[propertyName];
        }
        return undefined
    };

  return "          <div class=\"chat-actions\">\n            <div class=\"chat-actions-toggle\"><span></span><span></span><span></span></div>\n\n            <ul>\n"
    + ((stack1 = lookupProperty(helpers,"each").call(depth0 != null ? depth0 : (container.nullContext || {}),(depth0 != null ? lookupProperty(depth0,"overflow") : depth0),{"name":"each","hash":{},"fn":container.program(8, data, 0),"inverse":container.noop,"data":data,"loc":{"start":{"line":20,"column":14},"end":{"line":22,"column":23}}})) != null ? stack1 : "")
    + "            </ul>\n          </div>\n";
},"8":function(container,depth0,helpers,partials,data) {
    var helper, alias1=depth0 != null ? depth0 : (container.nullContext || {}), alias2=container.hooks.helperMissing, alias3="function", alias4=container.escapeExpression, lookupProperty = container.lookupProperty || function(parent, propertyName) {
        if (Object.prototype.hasOwnProperty.call(parent, propertyName)) {
          return parent[propertyName];
        }
        return undefined
    };

  return "              <li data-action=\""
    + alias4(((helper = (helper = lookupProperty(helpers,"action") || (depth0 != null ? lookupProperty(depth0,"action") : depth0)) != null ? helper : alias2),(typeof helper === alias3 ? helper.call(alias1,{"name":"action","hash":{},"data":data,"loc":{"start":{"line":21,"column":31},"end":{"line":21,"column":41}}}) : helper)))
    + "\">"
    + alias4(((helper = (helper = lookupProperty(helpers,"text") || (depth0 != null ? lookupProperty(depth0,"text") : depth0)) != null ? helper : alias2),(typeof helper === alias3 ? helper.call(alias1,{"name":"text","hash":{},"data":data,"loc":{"start":{"line":21,"column":43},"end":{"line":21,"column":51}}}) : helper)))
    + "</li>\n";
},"compiler":[8,">= 4.3.0"],"main":function(container,depth0,helpers,partials,data) {
    var stack1, helper, alias1=depth0 != null ? depth0 : (container.nullContext || {}), alias2=container.hooks.helperMissing, alias3="function", alias4=container.escapeExpression, lookupProperty = container.lookupProperty || function(parent, propertyName) {
        if (Object.prototype.hasOwnProperty.call(parent, propertyName)) {
          return parent[propertyName];
        }
        return undefined
    };

  return "<div class=\"chat-message chat-message-media "
    + ((stack1 = lookupProperty(helpers,"if").call(alias1,(depth0 != null ? lookupProperty(depth0,"thumbnail") : depth0),{"name":"if","hash":{},"fn":container.program(1, data, 0),"inverse":container.noop,"data":data,"loc":{"start":{"line":1,"column":44},"end":{"line":1,"column":98}}})) != null ? stack1 : "")
    + " "
    + ((stack1 = lookupProperty(helpers,"if").call(alias1,(depth0 != null ? lookupProperty(depth0,"caption") : depth0),{"name":"if","hash":{},"fn":container.program(3, data, 0),"inverse":container.noop,"data":data,"loc":{"start":{"line":1,"column":99},"end":{"line":1,"column":148}}})) != null ? stack1 : "")
    + "\" data-thread-id=\""
    + alias4(((helper = (helper = lookupProperty(helpers,"threadId") || (depth0 != null ? lookupProperty(depth0,"threadId") : depth0)) != null ? helper : alias2),(typeof helper === alias3 ? helper.call(alias1,{"name":"threadId","hash":{},"data":data,"loc":{"start":{"line":1,"column":166},"end":{"line":1,"column":178}}}) : helper)))
    + "\" data-message-id=\""
    + alias4(((helper = (helper = lookupProperty(helpers,"id") || (depth0 != null ? lookupProperty(depth0,"id") : depth0)) != null ? helper : alias2),(typeof helper === alias3 ? helper.call(alias1,{"name":"id","hash":{},"data":data,"loc":{"start":{"line":1,"column":197},"end":{"line":1,"column":203}}}) : helper)))
    + "\">\n  <div class=\"chat-container\">\n    <div class=\"inner\">\n      <img src=\""
    + alias4(((helper = (helper = lookupProperty(helpers,"avatar") || (depth0 != null ? lookupProperty(depth0,"avatar") : depth0)) != null ? helper : alias2),(typeof helper === alias3 ? helper.call(alias1,{"name":"avatar","hash":{},"data":data,"loc":{"start":{"line":4,"column":16},"end":{"line":4,"column":26}}}) : helper)))
    + "\" alt=\""
    + alias4(((helper = (helper = lookupProperty(helpers,"name") || (depth0 != null ? lookupProperty(depth0,"name") : depth0)) != null ? helper : alias2),(typeof helper === alias3 ? helper.call(alias1,{"name":"name","hash":{},"data":data,"loc":{"start":{"line":4,"column":33},"end":{"line":4,"column":41}}}) : helper)))
    + "\" class=\"chat-avatar\">\n\n      <div class=\"chat-bubble\">\n        "
    + ((stack1 = ((helper = (helper = lookupProperty(helpers,"html") || (depth0 != null ? lookupProperty(depth0,"html") : depth0)) != null ? helper : alias2),(typeof helper === alias3 ? helper.call(alias1,{"name":"html","hash":{},"data":data,"loc":{"start":{"line":7,"column":8},"end":{"line":7,"column":18}}}) : helper))) != null ? stack1 : "")
    + "\n\n"
    + ((stack1 = lookupProperty(helpers,"if").call(alias1,(depth0 != null ? lookupProperty(depth0,"caption") : depth0),{"name":"if","hash":{},"fn":container.program(5, data, 0),"inverse":container.noop,"data":data,"loc":{"start":{"line":9,"column":8},"end":{"line":13,"column":15}}})) != null ? stack1 : "")
    + "\n"
    + ((stack1 = lookupProperty(helpers,"if").call(alias1,(depth0 != null ? lookupProperty(depth0,"overflow") : depth0),{"name":"if","hash":{},"fn":container.program(7, data, 0),"inverse":container.noop,"data":data,"loc":{"start":{"line":15,"column":8},"end":{"line":25,"column":15}}})) != null ? stack1 : "")
    + "      </div>\n    </div>\n  </div>\n</div>\n";
},"useData":true});
this["CUI"]["views"]["chatMessage"] = Handlebars.template({"1":function(container,depth0,helpers,partials,data) {
    return " chat-message-user ";
},"3":function(container,depth0,helpers,partials,data) {
    var helper, alias1=depth0 != null ? depth0 : (container.nullContext || {}), alias2=container.hooks.helperMissing, alias3="function", alias4=container.escapeExpression, lookupProperty = container.lookupProperty || function(parent, propertyName) {
        if (Object.prototype.hasOwnProperty.call(parent, propertyName)) {
          return parent[propertyName];
        }
        return undefined
    };

  return "      <img src=\""
    + alias4(((helper = (helper = lookupProperty(helpers,"avatar") || (depth0 != null ? lookupProperty(depth0,"avatar") : depth0)) != null ? helper : alias2),(typeof helper === alias3 ? helper.call(alias1,{"name":"avatar","hash":{},"data":data,"loc":{"start":{"line":5,"column":16},"end":{"line":5,"column":26}}}) : helper)))
    + "\" alt=\""
    + alias4(((helper = (helper = lookupProperty(helpers,"name") || (depth0 != null ? lookupProperty(depth0,"name") : depth0)) != null ? helper : alias2),(typeof helper === alias3 ? helper.call(alias1,{"name":"name","hash":{},"data":data,"loc":{"start":{"line":5,"column":33},"end":{"line":5,"column":41}}}) : helper)))
    + "\" class=\"chat-avatar\">\n";
},"5":function(container,depth0,helpers,partials,data) {
    var stack1, lookupProperty = container.lookupProperty || function(parent, propertyName) {
        if (Object.prototype.hasOwnProperty.call(parent, propertyName)) {
          return parent[propertyName];
        }
        return undefined
    };

  return ((stack1 = lookupProperty(helpers,"if").call(depth0 != null ? depth0 : (container.nullContext || {}),(depth0 != null ? lookupProperty(depth0,"initials") : depth0),{"name":"if","hash":{},"fn":container.program(6, data, 0),"inverse":container.program(11, data, 0),"data":data,"loc":{"start":{"line":6,"column":6},"end":{"line":10,"column":6}}})) != null ? stack1 : "");
},"6":function(container,depth0,helpers,partials,data) {
    var stack1, helper, alias1=depth0 != null ? depth0 : (container.nullContext || {}), lookupProperty = container.lookupProperty || function(parent, propertyName) {
        if (Object.prototype.hasOwnProperty.call(parent, propertyName)) {
          return parent[propertyName];
        }
        return undefined
    };

  return "      <div class=\"chat-avatar "
    + ((stack1 = lookupProperty(helpers,"if").call(alias1,(depth0 != null ? lookupProperty(depth0,"userMessage") : depth0),{"name":"if","hash":{},"fn":container.program(7, data, 0),"inverse":container.program(9, data, 0),"data":data,"loc":{"start":{"line":7,"column":30},"end":{"line":7,"column":129}}})) != null ? stack1 : "")
    + "\">"
    + container.escapeExpression(((helper = (helper = lookupProperty(helpers,"initials") || (depth0 != null ? lookupProperty(depth0,"initials") : depth0)) != null ? helper : container.hooks.helperMissing),(typeof helper === "function" ? helper.call(alias1,{"name":"initials","hash":{},"data":data,"loc":{"start":{"line":7,"column":131},"end":{"line":7,"column":143}}}) : helper)))
    + "</div>\n";
},"7":function(container,depth0,helpers,partials,data) {
    return " chat-avatar--student-initials ";
},"9":function(container,depth0,helpers,partials,data) {
    return " chat-avatar--instructor-initials ";
},"11":function(container,depth0,helpers,partials,data) {
    var helper, alias1=depth0 != null ? depth0 : (container.nullContext || {}), alias2=container.hooks.helperMissing, alias3="function", alias4=container.escapeExpression, lookupProperty = container.lookupProperty || function(parent, propertyName) {
        if (Object.prototype.hasOwnProperty.call(parent, propertyName)) {
          return parent[propertyName];
        }
        return undefined
    };

  return "      <img src=\""
    + alias4(((helper = (helper = lookupProperty(helpers,"defaultAvatar") || (depth0 != null ? lookupProperty(depth0,"defaultAvatar") : depth0)) != null ? helper : alias2),(typeof helper === alias3 ? helper.call(alias1,{"name":"defaultAvatar","hash":{},"data":data,"loc":{"start":{"line":9,"column":16},"end":{"line":9,"column":33}}}) : helper)))
    + "\" alt=\""
    + alias4(((helper = (helper = lookupProperty(helpers,"name") || (depth0 != null ? lookupProperty(depth0,"name") : depth0)) != null ? helper : alias2),(typeof helper === alias3 ? helper.call(alias1,{"name":"name","hash":{},"data":data,"loc":{"start":{"line":9,"column":40},"end":{"line":9,"column":48}}}) : helper)))
    + "\" class=\"chat-avatar\">\n      ";
},"13":function(container,depth0,helpers,partials,data) {
    return "is-new";
},"15":function(container,depth0,helpers,partials,data) {
    var stack1, lookupProperty = container.lookupProperty || function(parent, propertyName) {
        if (Object.prototype.hasOwnProperty.call(parent, propertyName)) {
          return parent[propertyName];
        }
        return undefined
    };

  return "          <div class=\"chat-actions\">\n            <div class=\"chat-actions-toggle\"><span></span><span></span><span></span></div>\n\n            <ul>\n"
    + ((stack1 = lookupProperty(helpers,"each").call(depth0 != null ? depth0 : (container.nullContext || {}),(depth0 != null ? lookupProperty(depth0,"overflow") : depth0),{"name":"each","hash":{},"fn":container.program(16, data, 0),"inverse":container.noop,"data":data,"loc":{"start":{"line":23,"column":14},"end":{"line":25,"column":23}}})) != null ? stack1 : "")
    + "            </ul>\n          </div>\n";
},"16":function(container,depth0,helpers,partials,data) {
    var helper, alias1=depth0 != null ? depth0 : (container.nullContext || {}), alias2=container.hooks.helperMissing, alias3="function", alias4=container.escapeExpression, lookupProperty = container.lookupProperty || function(parent, propertyName) {
        if (Object.prototype.hasOwnProperty.call(parent, propertyName)) {
          return parent[propertyName];
        }
        return undefined
    };

  return "              <li data-action=\""
    + alias4(((helper = (helper = lookupProperty(helpers,"action") || (depth0 != null ? lookupProperty(depth0,"action") : depth0)) != null ? helper : alias2),(typeof helper === alias3 ? helper.call(alias1,{"name":"action","hash":{},"data":data,"loc":{"start":{"line":24,"column":31},"end":{"line":24,"column":41}}}) : helper)))
    + "\">"
    + alias4(((helper = (helper = lookupProperty(helpers,"text") || (depth0 != null ? lookupProperty(depth0,"text") : depth0)) != null ? helper : alias2),(typeof helper === alias3 ? helper.call(alias1,{"name":"text","hash":{},"data":data,"loc":{"start":{"line":24,"column":43},"end":{"line":24,"column":51}}}) : helper)))
    + "</li>\n";
},"compiler":[8,">= 4.3.0"],"main":function(container,depth0,helpers,partials,data) {
    var stack1, helper, alias1=depth0 != null ? depth0 : (container.nullContext || {}), alias2=container.hooks.helperMissing, alias3="function", alias4=container.escapeExpression, lookupProperty = container.lookupProperty || function(parent, propertyName) {
        if (Object.prototype.hasOwnProperty.call(parent, propertyName)) {
          return parent[propertyName];
        }
        return undefined
    };

  return "<div class=\"chat-message chat-message-text "
    + ((stack1 = lookupProperty(helpers,"if").call(alias1,(depth0 != null ? lookupProperty(depth0,"userMessage") : depth0),{"name":"if","hash":{},"fn":container.program(1, data, 0),"inverse":container.noop,"data":data,"loc":{"start":{"line":1,"column":43},"end":{"line":1,"column":88}}})) != null ? stack1 : "")
    + "\" data-thread-id=\""
    + alias4(((helper = (helper = lookupProperty(helpers,"threadId") || (depth0 != null ? lookupProperty(depth0,"threadId") : depth0)) != null ? helper : alias2),(typeof helper === alias3 ? helper.call(alias1,{"name":"threadId","hash":{},"data":data,"loc":{"start":{"line":1,"column":106},"end":{"line":1,"column":118}}}) : helper)))
    + "\" data-message-id=\""
    + alias4(((helper = (helper = lookupProperty(helpers,"id") || (depth0 != null ? lookupProperty(depth0,"id") : depth0)) != null ? helper : alias2),(typeof helper === alias3 ? helper.call(alias1,{"name":"id","hash":{},"data":data,"loc":{"start":{"line":1,"column":137},"end":{"line":1,"column":143}}}) : helper)))
    + "\">\n  <div class=\"chat-container\">\n    <div class=\"inner\">\n"
    + ((stack1 = lookupProperty(helpers,"if").call(alias1,(depth0 != null ? lookupProperty(depth0,"avatar") : depth0),{"name":"if","hash":{},"fn":container.program(3, data, 0),"inverse":container.program(5, data, 0),"data":data,"loc":{"start":{"line":4,"column":6},"end":{"line":10,"column":13}}})) != null ? stack1 : "")
    + "      <div class=\"chat-bubble "
    + ((stack1 = lookupProperty(helpers,"if").call(alias1,(depth0 != null ? lookupProperty(depth0,"is_new") : depth0),{"name":"if","hash":{},"fn":container.program(13, data, 0),"inverse":container.noop,"data":data,"loc":{"start":{"line":11,"column":30},"end":{"line":11,"column":57}}})) != null ? stack1 : "")
    + "\">\n        "
    + ((stack1 = ((helper = (helper = lookupProperty(helpers,"html") || (depth0 != null ? lookupProperty(depth0,"html") : depth0)) != null ? helper : alias2),(typeof helper === alias3 ? helper.call(alias1,{"name":"html","hash":{},"data":data,"loc":{"start":{"line":12,"column":8},"end":{"line":12,"column":18}}}) : helper))) != null ? stack1 : "")
    + "\n\n        <span class=\"chat-new-msg\">\n            new\n        </span>\n\n"
    + ((stack1 = lookupProperty(helpers,"if").call(alias1,(depth0 != null ? lookupProperty(depth0,"overflow") : depth0),{"name":"if","hash":{},"fn":container.program(15, data, 0),"inverse":container.noop,"data":data,"loc":{"start":{"line":18,"column":8},"end":{"line":28,"column":15}}})) != null ? stack1 : "")
    + "      </div>\n    </div>\n  </div>\n</div>\n";
},"useData":true});
this["CUI"]["views"]["chatToNextBreakpointButton"] = Handlebars.template({"compiler":[8,">= 4.3.0"],"main":function(container,depth0,helpers,partials,data) {
    var helper, alias1=depth0 != null ? depth0 : (container.nullContext || {}), alias2=container.hooks.helperMissing, alias3="function", alias4=container.escapeExpression, lookupProperty = container.lookupProperty || function(parent, propertyName) {
        if (Object.prototype.hasOwnProperty.call(parent, propertyName)) {
          return parent[propertyName];
        }
        return undefined
    };

  return "<div class=\"chat-next-thread-container\">\n    <button class=\"chat-next-thread\" data-thread-id=\""
    + alias4(((helper = (helper = lookupProperty(helpers,"threadId") || (depth0 != null ? lookupProperty(depth0,"threadId") : depth0)) != null ? helper : alias2),(typeof helper === alias3 ? helper.call(alias1,{"name":"threadId","hash":{},"data":data,"loc":{"start":{"line":2,"column":53},"end":{"line":2,"column":65}}}) : helper)))
    + "\" data-type=\""
    + alias4(((helper = (helper = lookupProperty(helpers,"type") || (depth0 != null ? lookupProperty(depth0,"type") : depth0)) != null ? helper : alias2),(typeof helper === alias3 ? helper.call(alias1,{"name":"type","hash":{},"data":data,"loc":{"start":{"line":2,"column":78},"end":{"line":2,"column":86}}}) : helper)))
    + "\">"
    + alias4(((helper = (helper = lookupProperty(helpers,"html") || (depth0 != null ? lookupProperty(depth0,"html") : depth0)) != null ? helper : alias2),(typeof helper === alias3 ? helper.call(alias1,{"name":"html","hash":{},"data":data,"loc":{"start":{"line":2,"column":88},"end":{"line":2,"column":96}}}) : helper)))
    + "</button>\n</div>";
},"useData":true});
this["CUI"]["views"]["inputOption"] = Handlebars.template({"compiler":[8,">= 4.3.0"],"main":function(container,depth0,helpers,partials,data) {
    var helper, alias1=depth0 != null ? depth0 : (container.nullContext || {}), alias2=container.hooks.helperMissing, alias3="function", alias4=container.escapeExpression, lookupProperty = container.lookupProperty || function(parent, propertyName) {
        if (Object.prototype.hasOwnProperty.call(parent, propertyName)) {
          return parent[propertyName];
        }
        return undefined
    };

  return "<button class=\"btn chat-option\" data-option-value=\""
    + alias4(((helper = (helper = lookupProperty(helpers,"value") || (depth0 != null ? lookupProperty(depth0,"value") : depth0)) != null ? helper : alias2),(typeof helper === alias3 ? helper.call(alias1,{"name":"value","hash":{},"data":data,"loc":{"start":{"line":1,"column":51},"end":{"line":1,"column":60}}}) : helper)))
    + "\">"
    + alias4(((helper = (helper = lookupProperty(helpers,"text") || (depth0 != null ? lookupProperty(depth0,"text") : depth0)) != null ? helper : alias2),(typeof helper === alias3 ? helper.call(alias1,{"name":"text","hash":{},"data":data,"loc":{"start":{"line":1,"column":62},"end":{"line":1,"column":70}}}) : helper)))
    + "</button>\n";
},"useData":true});
this["CUI"]["views"]["sidebarBreakpoint"] = Handlebars.template({"1":function(container,depth0,helpers,partials,data) {
    return " unlocked ";
},"3":function(container,depth0,helpers,partials,data) {
    return " started ";
},"5":function(container,depth0,helpers,partials,data) {
    return " done ";
},"7":function(container,depth0,helpers,partials,data) {
    return " is-active ";
},"compiler":[8,">= 4.3.0"],"main":function(container,depth0,helpers,partials,data) {
    var stack1, helper, alias1=depth0 != null ? depth0 : (container.nullContext || {}), alias2=container.hooks.helperMissing, alias3="function", alias4=container.escapeExpression, lookupProperty = container.lookupProperty || function(parent, propertyName) {
        if (Object.prototype.hasOwnProperty.call(parent, propertyName)) {
          return parent[propertyName];
        }
        return undefined
    };

  return "<li class=\""
    + ((stack1 = lookupProperty(helpers,"if").call(alias1,(depth0 != null ? lookupProperty(depth0,"isStarted") : depth0),{"name":"if","hash":{},"fn":container.program(1, data, 0),"inverse":container.noop,"data":data,"loc":{"start":{"line":1,"column":11},"end":{"line":1,"column":45}}})) != null ? stack1 : "")
    + " "
    + ((stack1 = lookupProperty(helpers,"if").call(alias1,(depth0 != null ? lookupProperty(depth0,"isStarted") : depth0),{"name":"if","hash":{},"fn":container.program(3, data, 0),"inverse":container.noop,"data":data,"loc":{"start":{"line":1,"column":46},"end":{"line":1,"column":79}}})) != null ? stack1 : "")
    + " "
    + ((stack1 = lookupProperty(helpers,"if").call(alias1,(depth0 != null ? lookupProperty(depth0,"isUnlocked") : depth0),{"name":"if","hash":{},"fn":container.program(1, data, 0),"inverse":container.noop,"data":data,"loc":{"start":{"line":1,"column":80},"end":{"line":1,"column":115}}})) != null ? stack1 : "")
    + " "
    + ((stack1 = lookupProperty(helpers,"if").call(alias1,(depth0 != null ? lookupProperty(depth0,"isDone") : depth0),{"name":"if","hash":{},"fn":container.program(5, data, 0),"inverse":container.noop,"data":data,"loc":{"start":{"line":1,"column":116},"end":{"line":1,"column":143}}})) != null ? stack1 : "")
    + " "
    + ((stack1 = lookupProperty(helpers,"if").call(alias1,(depth0 != null ? lookupProperty(depth0,"isCurrent") : depth0),{"name":"if","hash":{},"fn":container.program(7, data, 0),"inverse":container.noop,"data":data,"loc":{"start":{"line":1,"column":144},"end":{"line":1,"column":179}}})) != null ? stack1 : "")
    + "\" data-thread-id=\""
    + alias4(((helper = (helper = lookupProperty(helpers,"threadId") || (depth0 != null ? lookupProperty(depth0,"threadId") : depth0)) != null ? helper : alias2),(typeof helper === alias3 ? helper.call(alias1,{"name":"threadId","hash":{},"data":data,"loc":{"start":{"line":1,"column":197},"end":{"line":1,"column":209}}}) : helper)))
    + "\" data-first-message-id=\""
    + alias4(((helper = (helper = lookupProperty(helpers,"id") || (depth0 != null ? lookupProperty(depth0,"id") : depth0)) != null ? helper : alias2),(typeof helper === alias3 ? helper.call(alias1,{"name":"id","hash":{},"data":data,"loc":{"start":{"line":1,"column":234},"end":{"line":1,"column":240}}}) : helper)))
    + "\" data-updates-count=\""
    + alias4(((helper = (helper = lookupProperty(helpers,"updatesCount") || (depth0 != null ? lookupProperty(depth0,"updatesCount") : depth0)) != null ? helper : alias2),(typeof helper === alias3 ? helper.call(alias1,{"name":"updatesCount","hash":{},"data":data,"loc":{"start":{"line":1,"column":262},"end":{"line":1,"column":278}}}) : helper)))
    + "\">\n  "
    + ((stack1 = ((helper = (helper = lookupProperty(helpers,"html") || (depth0 != null ? lookupProperty(depth0,"html") : depth0)) != null ? helper : alias2),(typeof helper === alias3 ? helper.call(alias1,{"name":"html","hash":{},"data":data,"loc":{"start":{"line":2,"column":2},"end":{"line":2,"column":12}}}) : helper))) != null ? stack1 : "")
    + "\n</li>\n";
},"useData":true});
this["CUI"]["views"]["sidebarResources"] = Handlebars.template({"1":function(container,depth0,helpers,partials,data) {
    return " unlocked ";
},"3":function(container,depth0,helpers,partials,data) {
    return " started ";
},"5":function(container,depth0,helpers,partials,data) {
    return " done ";
},"7":function(container,depth0,helpers,partials,data) {
    return " is-active ";
},"compiler":[8,">= 4.3.0"],"main":function(container,depth0,helpers,partials,data) {
    var stack1, helper, alias1=depth0 != null ? depth0 : (container.nullContext || {}), alias2=container.hooks.helperMissing, alias3="function", alias4=container.escapeExpression, lookupProperty = container.lookupProperty || function(parent, propertyName) {
        if (Object.prototype.hasOwnProperty.call(parent, propertyName)) {
          return parent[propertyName];
        }
        return undefined
    };

  return "<li class=\""
    + ((stack1 = lookupProperty(helpers,"if").call(alias1,(depth0 != null ? lookupProperty(depth0,"isUnlocked") : depth0),{"name":"if","hash":{},"fn":container.program(1, data, 0),"inverse":container.noop,"data":data,"loc":{"start":{"line":1,"column":11},"end":{"line":1,"column":46}}})) != null ? stack1 : "")
    + "\n           "
    + ((stack1 = lookupProperty(helpers,"if").call(alias1,(depth0 != null ? lookupProperty(depth0,"isStarted") : depth0),{"name":"if","hash":{},"fn":container.program(3, data, 0),"inverse":container.noop,"data":data,"loc":{"start":{"line":2,"column":11},"end":{"line":2,"column":44}}})) != null ? stack1 : "")
    + "\n           "
    + ((stack1 = lookupProperty(helpers,"if").call(alias1,(depth0 != null ? lookupProperty(depth0,"isDone") : depth0),{"name":"if","hash":{},"fn":container.program(5, data, 0),"inverse":container.noop,"data":data,"loc":{"start":{"line":3,"column":11},"end":{"line":3,"column":38}}})) != null ? stack1 : "")
    + "\n           "
    + ((stack1 = lookupProperty(helpers,"if").call(alias1,(depth0 != null ? lookupProperty(depth0,"isCurrent") : depth0),{"name":"if","hash":{},"fn":container.program(7, data, 0),"inverse":container.noop,"data":data,"loc":{"start":{"line":4,"column":11},"end":{"line":4,"column":46}}})) != null ? stack1 : "")
    + "\"\n    data-first-message-id=\""
    + alias4(((helper = (helper = lookupProperty(helpers,"id") || (depth0 != null ? lookupProperty(depth0,"id") : depth0)) != null ? helper : alias2),(typeof helper === alias3 ? helper.call(alias1,{"name":"id","hash":{},"data":data,"loc":{"start":{"line":5,"column":27},"end":{"line":5,"column":33}}}) : helper)))
    + "\"\n    data-thread-id=\""
    + alias4(((helper = (helper = lookupProperty(helpers,"threadId") || (depth0 != null ? lookupProperty(depth0,"threadId") : depth0)) != null ? helper : alias2),(typeof helper === alias3 ? helper.call(alias1,{"name":"threadId","hash":{},"data":data,"loc":{"start":{"line":6,"column":20},"end":{"line":6,"column":32}}}) : helper)))
    + "\"\n    data-ul=\""
    + alias4(((helper = (helper = lookupProperty(helpers,"ul") || (depth0 != null ? lookupProperty(depth0,"ul") : depth0)) != null ? helper : alias2),(typeof helper === alias3 ? helper.call(alias1,{"name":"ul","hash":{},"data":data,"loc":{"start":{"line":7,"column":13},"end":{"line":7,"column":19}}}) : helper)))
    + "\">\n  "
    + ((stack1 = ((helper = (helper = lookupProperty(helpers,"html") || (depth0 != null ? lookupProperty(depth0,"html") : depth0)) != null ? helper : alias2),(typeof helper === alias3 ? helper.call(alias1,{"name":"html","hash":{},"data":data,"loc":{"start":{"line":8,"column":2},"end":{"line":8,"column":12}}}) : helper))) != null ? stack1 : "")
    + "\n</li>\n";
},"useData":true});