import { request } from '../base'

export const ccTopoTree = request('GET', 'rest/v2/performance/cc_topo_tree/')
export const agentStatus = request('GET', 'rest/v2/performance/agent_status/')
export const hostAlarmCount = request('GET', 'rest/v2/performance/host_alarm/count/')
export const hostIndex = request('GET', 'rest/v2/performance/host_index/')
export const getFieldValuesByIndexId = request('POST', 'rest/v2/performance/host_index/field_values/')
export const graphPoint = request('POST', 'rest/v2/performance/host_index/graph_point/')
export const hostComponentInfo = request('GET', 'rest/v2/performance/host_component_info/')
export const hostPerformanceDetail = request('POST', 'rest/v2/performance/host_performance_detail/')
export const hostTopoNodeDetail = request('POST', 'rest/v2/performance/host_topo_node_detail/')
export const hostProcessStatus = request('POST', 'rest/v2/performance/host_process_status/')
export const topoNodeProcessStatus = request('POST', 'rest/v2/performance/topo_node_process_status/')
export const hostPerformance = request('GET', 'rest/v2/performance/host_list/')
export const getHostDashboardConfig = request('POST', 'rest/v2/performance/get_host_dashboard_config/')
export const getTopoNodeDashboardConfig = request('POST', 'rest/v2/performance/get_topo_node_dashboard_config/')
export const searchHostInfo = request('POST', 'rest/v2/performance/search_host_info/')
export const searchHostMetric = request('POST', 'rest/v2/performance/search_host_metric/')

export default {
  ccTopoTree,
  agentStatus,
  hostAlarmCount,
  hostIndex,
  getFieldValuesByIndexId,
  graphPoint,
  hostComponentInfo,
  hostPerformanceDetail,
  hostTopoNodeDetail,
  hostProcessStatus,
  topoNodeProcessStatus,
  hostPerformance,
  getHostDashboardConfig,
  getTopoNodeDashboardConfig,
  searchHostInfo,
  searchHostMetric
}
