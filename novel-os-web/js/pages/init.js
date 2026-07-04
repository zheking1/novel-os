/**
 * Novel OS - Init Module (page initialization)
 */
;(function() {
  'use strict';

  // Register init functions globally
  window.init_skill_manage_fn = async function() {
    console.log("[Skill] init_skill_manage called");
    if (window.loadSkillList) await window.loadSkillList();
  };

  window.init_model_profiles_fn = function() {
    if (window.modelProfilesInitStarted) return;
    window.modelProfilesInitStarted = true;
    var b = window.$$ ? window.$$("modelProfilesListBtn") : window.$("modelProfilesListBtn");
    if (b) b.click();
  };

  window.init_model_cost_fn = function() {
    if (window.modelCostInitStarted) return;
    window.modelCostInitStarted = true;
    var b = window.$("costReportBtn");
    if (b) b.click();
  };

  window.init_template_list_fn = function() {
    if (window.templateListInitStarted) return;
    window.templateListInitStarted = true;
    var b = window.$("templateListBtn");
    if (b) b.click();
  };
})();