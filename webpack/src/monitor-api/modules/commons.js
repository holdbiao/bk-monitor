import { request } from '../base'

export const businessListOption = request('GET', 'rest/v2/commons/business_list_option/')
export const fetchBusinessInfo = request('GET', 'rest/v2/commons/fetch_business_info/')
export const getDocLink = request('GET', 'rest/v2/commons/get_docs_link/')
export const countryList = request('GET', 'rest/v2/commons/country_list/')
export const ispList = request('GET', 'rest/v2/commons/isp_list/')
export const hostRegionIspInfo = request('GET', 'rest/v2/commons/host_region_isp_info/')
export const ccTopoTree = request('GET', 'rest/v2/performance/cc_topo_tree/')
export const getTopoTree = request('POST', 'rest/v2/commons/get_topo_tree/')
export const getHostInstanceByIp = request('POST', 'rest/v2/commons/get_host_instance_by_ip/')
export const getHostInstanceByNode = request('POST', 'rest/v2/commons/get_host_instance_by_node/')
export const getServiceInstanceByNode = request('POST', 'rest/v2/commons/get_service_instance_by_node/')
export const getServiceCategory = request('POST', 'rest/v2/commons/get_service_category/')
export const hostAgentStatus = request('POST', 'rest/v2/commons/host_agent_status/')
export const getMainlineObjectTopo = request('GET', 'rest/v2/commons/get_mainline_object_topo/')
export const getTemplate = request('POST', 'rest/v2/commons/get_template/')
export const getNodesByTemplate = request('POST', 'rest/v2/commons/get_nodes_by_template/')
export const graphPoint = request('POST', 'rest/v2/commons/graph_point/')
export const getContext = request('GET', 'rest/v2/commons/get_context/')
export const listResultTableAccessInfo = request('GET', 'rest/v2/commons/list_result_table_access_info/')
export const getResultTableAccessInfo = request('GET', 'rest/v2/commons/get_result_table/')
export const getLabel = request('GET', 'rest/v2/commons/get_label/')
export const fileUpload = request('POST', 'rest/v2/commons/file_upload/')
export const fileDeploy = request('POST', 'rest/v2/commons/file_deploy/')
export const queryAsyncTaskResult = request('GET', 'rest/v2/commons/query_async_task_result/')
export const getFooter = request('GET', 'rest/v2/commons/get_footer/')

export default {
  businessListOption,
  fetchBusinessInfo,
  getDocLink,
  countryList,
  ispList,
  hostRegionIspInfo,
  ccTopoTree,
  getTopoTree,
  getHostInstanceByIp,
  getHostInstanceByNode,
  getServiceInstanceByNode,
  getServiceCategory,
  hostAgentStatus,
  getMainlineObjectTopo,
  getTemplate,
  getNodesByTemplate,
  graphPoint,
  getContext,
  listResultTableAccessInfo,
  getResultTableAccessInfo,
  getLabel,
  fileUpload,
  fileDeploy,
  queryAsyncTaskResult,
  getFooter
}
