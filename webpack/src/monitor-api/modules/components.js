import { request } from '../base'

export const componentGraphPoint = request('POST', 'rest/v1/component_graph_point/')
export const editInstanceName = request('POST', 'rest/v1/edit_instance_name/')
export const setCategoryForComponent = request('POST', 'rest/v1/set_component_category/')
export const componentAccessExecution = request('POST', 'rest/v1/component_access/execute/')
export const componentReportStatus = request('GET', 'rest/v1/component_report_status/')
export const hostAgentStatus = request('GET', 'rest/v1/host_agent_status/')
export const componentInstanceList = request('GET', 'rest/v1/component_instance_list/')

export default {
  componentGraphPoint,
  editInstanceName,
  setCategoryForComponent,
  componentAccessExecution,
  componentReportStatus,
  hostAgentStatus,
  componentInstanceList
}
