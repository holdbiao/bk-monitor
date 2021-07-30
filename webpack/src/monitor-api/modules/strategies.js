import { request } from '../base'

export const getScenarioList = request('GET', 'rest/v2/strategies/get_scenario_list/')
export const getMetricList = request('POST', 'rest/v2/strategies/get_metric_list/')
export const getDimensionValues = request('POST', 'rest/v2/strategies/get_dimension_values/')
export const strategyConfig = request('POST', 'rest/v2/strategies/strategy_config/')
export const cloneStrategyConfig = request('POST', 'rest/v2/strategies/clone_strategy_config/')
export const deleteStrategyConfig = request('POST', 'rest/v2/strategies/delete_strategy_config/')
export const strategyConfigList = request('POST', 'rest/v2/strategies/strategy_config_list/')
export const strategyConfigDetail = request('GET', 'rest/v2/strategies/strategy_config_detail/')
export const bulkEditStrategy = request('POST', 'rest/v2/strategies/bulk_edit_strategy/')
export const getDimensionList = request('GET', 'rest/v2/strategies/get_dimension_list/')
export const plainStrategyList = request('GET', 'rest/v2/strategies/plain_strategy_list/')
export const strategyInfo = request('GET', 'rest/v2/strategies/strategy_info/')
export const noticeVariableList = request('GET', 'rest/v2/strategies/notice_variable_list/')
export const getIndexSetList = request('GET', 'rest/v2/strategies/get_index_set_list/')
export const getLogFields = request('GET', 'rest/v2/strategies/get_log_fields/')
export const renderNoticeTemplate = request('POST', 'rest/v2/strategies/render_notice_template/')
export const getUnitList = request('GET', 'rest/v2/strategies/get_unit_list/')
export const getUnitInfo = request('GET', 'rest/v2/strategies/get_unit_info/')
export const strategyLabel = request('POST', 'rest/v2/strategies/strategy_label/')
export const strategyLabelList = request('GET', 'rest/v2/strategies/strategy_label_list/')
export const deleteStrategyLabel = request('POST', 'rest/v2/strategies/delete_strategy_label/')
export const fetchItemStatus = request('POST', 'rest/v2/strategies/fetch_item_status/')

export default {
  getScenarioList,
  getMetricList,
  getDimensionValues,
  strategyConfig,
  cloneStrategyConfig,
  deleteStrategyConfig,
  strategyConfigList,
  strategyConfigDetail,
  bulkEditStrategy,
  getDimensionList,
  plainStrategyList,
  strategyInfo,
  noticeVariableList,
  getIndexSetList,
  getLogFields,
  renderNoticeTemplate,
  getUnitList,
  getUnitInfo,
  strategyLabel,
  strategyLabelList,
  deleteStrategyLabel,
  fetchItemStatus
}
