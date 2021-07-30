import { request } from '../base'

export const collectConfigList = request('POST', 'rest/v2/collecting_config/config_list/')
export const collectConfigDetail = request('GET', 'rest/v2/collecting_config/config_detail/')
export const frontendCollectConfigDetail = request('GET', 'rest/v2/collecting_config/frontend_config_detail/')
export const collectTargetStatus = request('GET', 'rest/v2/collecting_config/status/')
export const collectNodeStatus = request('GET', 'rest/v2/collecting_config/node_status/')
export const toggleCollectConfigStatus = request('POST', 'rest/v2/collecting_config/toggle/')
export const deleteCollectConfig = request('POST', 'rest/v2/collecting_config/delete/')
export const cloneCollectConfig = request('POST', 'rest/v2/collecting_config/clone/')
export const retryTargetNodes = request('POST', 'rest/v2/collecting_config/retry/')
export const revokeTargetNodes = request('POST', 'rest/v2/collecting_config/revoke/')
export const batchRevokeTargetNodes = request('POST', 'rest/v2/collecting_config/batch_revoke/')
export const batchRetryConfig = request('POST', 'rest/v2/collecting_config/batch_retry/')
export const saveCollectConfig = request('POST', 'rest/v2/collecting_config/save/')
export const upgradeCollectPlugin = request('POST', 'rest/v2/collecting_config/upgrade/')
export const rollbackDeploymentConfig = request('POST', 'rest/v2/collecting_config/rollback/')
export const graphPoint = request('POST', 'rest/v2/collecting_config/graph_point/')
export const frontendTargetStatusTopo = request('POST', 'rest/v2/collecting_config/target_status_topo/')
export const getMetrics = request('GET', 'rest/v2/collecting_config/metrics/')
export const renameCollectConfig = request('POST', 'rest/v2/collecting_config/rename/')
export const deploymentConfigDiff = request('GET', 'rest/v2/collecting_config/deployment_diff/')
export const collectRunningStatus = request('GET', 'rest/v2/collecting_config/running_status/')
export const getCollectLogDetail = request('GET', 'rest/v2/collecting_config/get_collect_log_detail/')
export const updateConfigInstanceCount = request('GET', 'rest/v2/collecting_config/update_config_instance_count/')
export const getCollectVariables = request('GET', 'rest/v2/collecting_config/get_collect_variables/')
export const collectInstanceStatus = request('GET', 'rest/v2/collecting_config/collect_instance_status/')
export const batchRetry = request('POST', 'rest/v2/collecting_config/batch_retry_detailed/')
export const listLegacySubscription = request('GET', 'rest/v2/collecting_config/list_legacy_subscription/')
export const cleanLegacySubscription = request('GET', 'rest/v2/collecting_config/clean_legacy_subscription/')
export const listLegacyStrategy = request('GET', 'rest/v2/collecting_config/list_legacy_strategy/')
export const getCollectDashboardConfig = request('POST', 'rest/v2/collecting_config/get_collect_dashboard_config/')
export const listRelatedStrategy = request('POST', 'rest/v2/collecting_config/list_related_strategy/')
export const isTaskReady = request('POST', 'rest/v2/collecting_config/is_task_ready/')

export default {
  collectConfigList,
  collectConfigDetail,
  frontendCollectConfigDetail,
  collectTargetStatus,
  collectNodeStatus,
  toggleCollectConfigStatus,
  deleteCollectConfig,
  cloneCollectConfig,
  retryTargetNodes,
  revokeTargetNodes,
  batchRevokeTargetNodes,
  batchRetryConfig,
  saveCollectConfig,
  upgradeCollectPlugin,
  rollbackDeploymentConfig,
  graphPoint,
  frontendTargetStatusTopo,
  getMetrics,
  renameCollectConfig,
  deploymentConfigDiff,
  collectRunningStatus,
  getCollectLogDetail,
  updateConfigInstanceCount,
  getCollectVariables,
  collectInstanceStatus,
  batchRetry,
  listLegacySubscription,
  cleanLegacySubscription,
  listLegacyStrategy,
  getCollectDashboardConfig,
  listRelatedStrategy,
  isTaskReady
}
