import { request } from '../base'

export const listEvent = request('POST', 'rest/v2/event_center/list_event/')
export const detailEvent = request('GET', 'rest/v2/event_center/detail_event/')
export const strategySnapshot = request('GET', 'rest/v2/event_center/strategy_snapshot/')
export const listAlertNotice = request('GET', 'rest/v2/event_center/list_alert_notice/')
export const detailAlertNotice = request('GET', 'rest/v2/event_center/detail_alert_notice/')
export const ackEvent = request('POST', 'rest/v2/event_center/ack_event/')
export const graphPoint = request('POST', 'rest/v2/event_center/graph_point/')
export const eventGraphQuery = request('POST', 'rest/v2/event_center/event_graph_query/')
export const getSolution = request('GET', 'rest/v2/event_center/get_solution/')
export const saveSolution = request('POST', 'rest/v2/event_center/save_solution/')
export const listEventLog = request('POST', 'rest/v2/event_center/event_log/')
export const listSearchItem = request('POST', 'rest/v2/event_center/list_search_item/')
export const listConvergeLog = request('GET', 'rest/v2/event_center/list_converge_log/')
export const stackedChart = request('POST', 'rest/v2/event_center/stacked_chart/')
export const shieldSnapshot = request('GET', 'rest/v2/event_center/shield_snapshot/')
export const eventRelatedInfo = request('POST', 'rest/v2/event_center/event_related_info/')
export const listIndexByHost = request('POST', 'rest/v2/event_center/list_index_by_host/')

export default {
  listEvent,
  detailEvent,
  strategySnapshot,
  listAlertNotice,
  detailAlertNotice,
  ackEvent,
  graphPoint,
  eventGraphQuery,
  getSolution,
  saveSolution,
  listEventLog,
  listSearchItem,
  listConvergeLog,
  stackedChart,
  shieldSnapshot,
  eventRelatedInfo,
  listIndexByHost
}
